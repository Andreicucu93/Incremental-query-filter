# Incremental Query Filter v2 — Design

**Date:** 2026-07-01
**Branch:** `feature/query-filter-v2` (repo: `C:\AI_space\work\Incremental-query-filter`)
**Status:** Approved design — ready for implementation planning

---

## 1. Purpose

A native desktop helper that turns a large pasted column of IDs into a sequence
of SQL `IN (...)` query batches, each sized to fit under a character limit, and
tracks which records are done across runs. The user copies each batch to the
clipboard and runs it against a (laggy, production) cloud database.

This is a **modernize-in-place rewrite** of the existing single-file
CustomTkinter app: same double-click desktop tool, but with the logic bugs fixed,
the record order preserved, a genuinely informative progress display, and a
clear count of batches remaining.

## 2. Problems in the current version (root causes)

1. **Record order is destroyed.** `load_records()` reads lines into Python
   `set`s (`{line for line in file}`); sets are unordered, so every load
   scrambles the pasted sequence. The progress box compounds this by inserting
   each batch at `"1.0"` (the top), reversing chronological order.
2. **Random crashes.** When no records fit (or all are already done),
   `generate_query()` calls `save_input_data()` then **calls itself** with no
   exit condition → infinite recursion → `RecursionError`.
3. **Broken install.** `requirements.txt` pins `customtkinter==0.0.3`, an
   ancient/broken version (current is 5.x), so clean installs can fail.
4. **No "batches remaining" indicator.** A `live_status` label exists but is
   never populated.
5. **Cramped, uninformative UI.** 17-character text boxes, no totals, no
   progress bar, silent clipboard copy, and a `Clear` button that wipes
   everything instantly with no confirmation — dangerous for production use.
6. **Muddled paste model.** The input box is simultaneously the data source and
   the live list, and clicking "Get Query" silently overwrites the saved file.

## 3. Output format (source of truth)

The generated query must match this user-provided example **byte-for-byte**:

```
DBKEY in ('1840833','1706494','1840916', … ,'1712498')
```

Format rules:

- Template: `{attribute} in ({values})`
- Each value wrapped in **single quotes**: `'1840833'`
- Values joined by a comma with **no space**: `'1840833','1706494'`
- Normal spacing around `in`: `{attribute} in (`
- Example for one value: `DBKEY in ('1840833')`

> Note: this **overrides** an earlier answer that selected double quotes. The
> user's example output is authoritative. The current code's double-quote,
> comma-space format (`in ("a", "b")`) is replaced entirely.

The greedy packing (Section 6) measures length against **this exact string**, so
batches fill right up to the limit without wasting bytes on spaces.

## 4. Architecture

Split the tangled single file into two focused units:

- **`query_core.py`** — pure logic, **no I/O and no UI imports**, fully
  unit-testable. Functions: dedup-preserving-order, build query string, pack one
  batch, count total batches, compute pending. This is where every bug lives, so
  this is what gets tests. Pure functions in/out — nothing on disk.
- **`storage.py`** — all file/settings persistence: read/write the record files
  and `settings.json`. Isolated so `query_core` stays pure.
- **`main.py`** — the CustomTkinter UI. Builds widgets, wires them to
  `query_core` + `storage`, handles user interaction. No business logic of its
  own beyond glue.

Files on disk (unchanged names for the record files, so existing data is
compatible):

- `all_records.txt` — the full list, one ID per line, **in paste order**.
- `executed_records.txt` — done IDs, one per line, in the order they were
  executed.
- `settings.json` (new, optional) — remembers last-used `attribute` and
  `char limit` so the user doesn't retype them each run.

## 5. Data model

No `set` anywhere. Order-preserving throughout.

- **List** — IDs in exact paste order, deduplicated by **first occurrence**,
  blank lines stripped.
- **Done** — executed IDs, in execution order.
- **Pending** — `List` minus `Done`, preserving `List` order.

Order-preserving dedup uses `dict.fromkeys(...)` (or equivalent), never `set`.

## 6. Core logic

### 6.1 Build query
```
build_query(attribute, ids) -> "{attribute} in ({v1}','{v2}',…)"
  values = ",".join("'" + id + "'" for id in ids)
  return f"{attribute} in ({values})"
```

### 6.2 Length (computed additively, O(n), no repeated string building)
For an attribute `A` and `k` ids:
```
base = len(A) + len(" in (") + len(")")        # e.g. "DBKEY in ()" = 11
length(k ids) = base + Σ(len(id_i) + 2)         # +2 for the two single quotes
                     + (k - 1)                   # commas between values
```
Verified against the example: `DBKEY in ('1840833')` = 20 chars =
`base(11) + (7+2) + 0`. ✓

### 6.3 Pack one batch
Greedily accumulate pending IDs (in order) while length ≤ limit:
```
pack_batch(pending, attribute, limit):
  cur = base(attribute); batch = []
  for id in pending:
    add = (len(id) + 2) + (1 if batch else 0)   # value + comma if not first
    if cur + add > limit: break
    batch.append(id); cur += add
  return batch
```

### 6.4 Count batches remaining
```
count_batches(pending, attribute, limit):
  remaining = list(pending); n = 0
  while remaining:
    b = pack_batch(remaining, attribute, limit)
    if not b: return None            # single ID too big — cannot complete
    n += 1; remaining = remaining[len(b):]
  return n
```
This yields the **exact** number of query batches left — the user's requested
indicator.

### 6.5 Edge cases (all crash-free)
- **A single ID's query already exceeds the limit** → `pack_batch` returns empty;
  the UI shows a clear message ("Limit too small — one ID won't fit") and does
  not advance. **No recursion.**
- **Pending is empty** → "✅ All done" state; Next batch disabled.
- **Missing/empty record files** → recreated gracefully on load.

## 7. UI layout (native CustomTkinter, redesigned)

```
┌─ Incremental Query Filter ─────────────────────────────────────┐
│  Attribute: [ DBKEY ]            Char limit: [ 1200 ]          │
├────────────────────────────────────────────────────────────────┤
│  OVERALL PROGRESS                                              │
│  ██████████████████░░░░░░░░░░░  62%                            │
│  Total 196    ·    Done 122    ·    Remaining 74              │
│  ▶  Batches remaining:  3                                     │
├───────────────┬───────────────┬────────────────────────────────┤
│ PASTE COLUMN  │ PENDING (order)│ DONE                          │
│ ┌───────────┐ │ ┌───────────┐  │ ┌───────────┐                 │
│ │1840833    │ │ │1840916    │  │ │1840833    │                 │
│ │1706494    │ │ │1882571    │  │ │1706494    │                 │
│ │...        │ │ │...        │  │ │...        │                 │
│ └───────────┘ │ └───────────┘  │ └───────────┘                 │
│ [ Load list ] │                │                              │
├────────────────────────────────────────────────────────────────┤
│        [  ▶ Next batch  ]            [ Clear (confirm) ]        │
├────────────────────────────────────────────────────────────────┤
│ Current query  →  copied to clipboard ✓                        │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ DBKEY in ('1840916','1882571', … )                         │ │
│ └────────────────────────────────────────────────────────────┘ │
│ Copied 42 IDs · 1,180 / 1,200 chars used     [☐ Stay on top]  │
│                                    Transparency ▁▂▃▄▅▆▇█        │
└────────────────────────────────────────────────────────────────┘
```

- **Progress card** (top): progress bar + %, live Total / Done / Remaining, and
  a prominent **Batches remaining** count. This is the "revealing" upgrade the
  user asked for.
- **Three ordered panels**: the editable Paste column (left), the read-only
  **Pending** list and **Done** list (middle/right). Pending shrinks and Done
  grows as batches run — both in true paste order.
- **Stay-on-top** checkbox and **Transparency** slider are kept (handy for
  overlaying on a production console).

## 8. UI behavior

- **Load list** — take the paste box content → split lines, strip, drop blanks,
  dedup preserving first occurrence → write `all_records.txt` in order → **reset
  progress** (`executed_records.txt` cleared) → refresh all panels/counters.
  If progress already exists, **confirm first** (this discards it).
- **Next batch** — compute pending; if empty show "✅ All done"; else pack a
  batch, build the query, copy to clipboard, **append** batch IDs to
  `executed_records.txt` (progress auto-saved), refresh panels/counters, and
  show `Copied N IDs · X / limit chars used`.
- **Clear** — **confirmation dialog**, then wipe both files and the UI.
- **On startup** — load both files, render panels/counters, restore last
  attribute + limit from `settings.json`.
- **Attribute / limit** — persisted to `settings.json` when a batch runs.

## 9. Error handling & polish

- Attribute empty or limit not a positive integer → friendly inline message; no
  crash (fixes the silent `int()` failure).
- Single-ID-too-big and all-done states handled explicitly (Section 6.5).
- Clipboard copy shows a visible "Copied ✓" confirmation.
- `requirements.txt` updated to a modern `customtkinter` (5.x) + `pyperclip`.

## 10. Testing

`pytest` unit tests against `query_core` (written **test-first**, since the bugs
live in the logic):

- `dedup_preserve_order` keeps first occurrence, strips blanks, no reordering.
- `build_query` matches the example format exactly (single quotes, no spaces).
- `length()` additive formula equals `len(build_query(...))` for random inputs.
- `pack_batch` fills up to but never over the limit; respects order.
- `count_batches` returns the exact number for known inputs; `None` when a
  single ID can't fit.
- `pending` = List − Done in List order.
- Round-trip: packing all batches in sequence reproduces the full pending list,
  in order, with no gaps or duplicates.

UI is verified by running the app against the sample data.

## 11. Acceptance criteria

1. Pasting the sample column and loading it preserves **exact order** in the
   Pending panel (top matches the first pasted ID).
2. Generated queries match `DBKEY in ('…','…')` byte-for-byte (single quotes, no
   spaces).
3. Each batch is ≤ the char limit and as full as possible.
4. "Batches remaining" shows the correct count and decrements as batches run.
5. Progress bar, Total/Done/Remaining update live.
6. No crash when: limit too small for one ID, all records done, empty/invalid
   attribute or limit, missing files.
7. Progress persists across app restarts; Load list resets it (with confirm);
   Clear wipes it (with confirm).
8. `pip install -r requirements.txt` succeeds on a clean environment.

## 12. Out of scope (Phase 2 — noted, not built now)

Cloud automation via a logical screen recording to drive query execution against
the laggy production system. Deferred to a separate spec after v2 is working, so
the recording can be built around the finished, stable UI.
