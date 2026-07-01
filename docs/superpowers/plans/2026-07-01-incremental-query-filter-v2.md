# Incremental Query Filter v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the Incremental Query Filter as a bug-free, order-preserving desktop tool with a revealing progress display and a batches-remaining indicator.

**Architecture:** Split the tangled single-file app into three focused modules — `query_core.py` (pure logic, unit-tested), `storage.py` (file/settings I/O, unit-tested), and `main.py` (CustomTkinter UI, verified by running). All logic is test-first; the UI is manually verified against the sample data.

**Tech Stack:** Python 3.12, CustomTkinter 5.x, Tkinter, pyperclip, pytest.

## Global Constraints

- **Output format is authoritative and byte-exact:** `{attribute} in ('v1','v2',…)` — each value in **single quotes**, values joined by a comma with **no space**. Example: `DBKEY in ('1840833','1706494')`. One value: `DBKEY in ('1840833')`.
- **No `set` for anything order-bearing.** List, Done, and Pending must preserve order. A `set` may be used only for O(1) membership testing where order is not read (e.g. inside `pending_records`).
- **Record files keep their existing names** (backward compatible): `all_records.txt` (paste order), `executed_records.txt` (execution order). New: `settings.json` (last attribute + limit).
- **Python 3.12**, run on Windows. UI is a native double-click desktop app.
- **TDD**: write the failing test first for all `query_core` and `storage` work. Commit after each task.
- **Every commit message must end with these two footer lines** (shown in Task 1, append to every commit):
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01953vEfdui6nzYzzpbfXnRB
  ```

## File Structure

- Create: `query_core.py` — pure functions: `dedup_preserve_order`, `build_query`, `query_length`, `pack_batch`, `pending_records`, `count_batches`.
- Create: `storage.py` — `read_lines`, `write_lines`, `append_lines`, `clear_file`, `load_settings`, `save_settings`.
- Create: `main.py` — `App(ctk.CTk)` UI class wiring the above. (Replaces the old `main.py`.)
- Create: `tests/test_query_core.py`, `tests/test_storage.py`.
- Modify: `requirements.txt` (fix broken pin), `README.md` (reflect v2).

---

### Task 1: Fix environment & dependencies

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: nothing.
- Produces: a working install — `import customtkinter, pyperclip` succeeds; `pytest` available.

- [ ] **Step 1: Replace `requirements.txt` contents**

```
customtkinter>=5.2.0
pyperclip>=1.9.0
pytest>=8.0
```

- [ ] **Step 2: Install and verify imports**

Run:
```powershell
pip install -r requirements.txt
python -c "import customtkinter, pyperclip; print('ok')"
```
Expected: prints `ok` with no error (the old `customtkinter==0.0.3` pin no longer breaks install).

- [ ] **Step 3: Commit**

```powershell
git add requirements.txt
git commit -m @'
fix: replace broken customtkinter pin, add pytest

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01953vEfdui6nzYzzpbfXnRB
'@
```

---

### Task 2: query_core — dedup & build_query

**Files:**
- Create: `query_core.py`
- Test: `tests/test_query_core.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `dedup_preserve_order(items: Iterable[str]) -> list[str]` — strips each item, drops blanks, dedups keeping first occurrence, preserves order.
  - `build_query(attribute: str, ids: list[str]) -> str` — returns `{attribute} in ('id1','id2',…)` (single quotes, comma no space).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_query_core.py`:
```python
import query_core as qc


def test_dedup_preserves_order_and_strips_blanks():
    assert qc.dedup_preserve_order([" b ", "a", "b", "", "c", "a"]) == ["b", "a", "c"]


def test_build_query_two_values_single_quotes_no_spaces():
    assert qc.build_query("DBKEY", ["1840833", "1706494"]) == "DBKEY in ('1840833','1706494')"


def test_build_query_single_value():
    assert qc.build_query("DBKEY", ["1840833"]) == "DBKEY in ('1840833')"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_query_core.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'query_core'`.

- [ ] **Step 3: Write minimal implementation**

Create `query_core.py`:
```python
"""Pure logic for the Incremental Query Filter. No I/O, no UI imports."""


def dedup_preserve_order(items):
    seen = {}
    for raw in items:
        s = raw.strip()
        if s and s not in seen:
            seen[s] = None
    return list(seen)


def build_query(attribute, ids):
    values = ",".join(f"'{i}'" for i in ids)
    return f"{attribute} in ({values})"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_query_core.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add query_core.py tests/test_query_core.py
git commit -m @'
feat: add dedup_preserve_order and build_query

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01953vEfdui6nzYzzpbfXnRB
'@
```

---

### Task 3: query_core — query_length & pack_batch

**Files:**
- Modify: `query_core.py`
- Test: `tests/test_query_core.py`

**Interfaces:**
- Consumes: `build_query` from Task 2.
- Produces:
  - `query_length(attribute: str, ids: list[str]) -> int` — length of `build_query(attribute, ids)`, computed additively (must equal `len(build_query(...))`).
  - `pack_batch(pending: list[str], attribute: str, limit: int) -> list[str]` — greedily takes pending IDs in order while the query length ≤ `limit`; returns `[]` if not even one ID fits.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_query_core.py`:
```python
def test_query_length_matches_build_query():
    ids = [str(i) for i in range(1000, 1123)]
    assert qc.query_length("DBKEY", ids) == len(qc.build_query("DBKEY", ids))


def test_query_length_empty():
    assert qc.query_length("DBKEY", []) == len("DBKEY in ()")


def test_pack_batch_fills_up_to_limit_in_order():
    pending = ["11", "22", "33", "44"]
    batch = qc.pack_batch(pending, "A", 20)
    assert batch == pending[:len(batch)]                     # order preserved, prefix only
    assert qc.query_length("A", batch) <= 20
    if len(batch) < len(pending):
        assert qc.query_length("A", pending[:len(batch) + 1]) > 20  # one more would overflow


def test_pack_batch_single_id_too_big_returns_empty():
    assert qc.pack_batch(["1840833"], "DBKEY", 10) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_query_core.py -v`
Expected: FAIL — `AttributeError: module 'query_core' has no attribute 'query_length'`.

- [ ] **Step 3: Write minimal implementation**

Append to `query_core.py`:
```python
def query_length(attribute, ids):
    if not ids:
        return len(f"{attribute} in ()")
    base = len(attribute) + len(" in (") + len(")")
    body = sum(len(x) + 2 for x in ids) + (len(ids) - 1)
    return base + body


def pack_batch(pending, attribute, limit):
    base = len(attribute) + len(" in (") + len(")")
    cur = base
    batch = []
    for item in pending:
        add = len(item) + 2 + (1 if batch else 0)   # value + quotes, plus comma if not first
        if cur + add > limit:
            break
        batch.append(item)
        cur += add
    return batch
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_query_core.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```powershell
git add query_core.py tests/test_query_core.py
git commit -m @'
feat: add query_length and pack_batch

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01953vEfdui6nzYzzpbfXnRB
'@
```

---

### Task 4: query_core — pending_records & count_batches

**Files:**
- Modify: `query_core.py`
- Test: `tests/test_query_core.py`

**Interfaces:**
- Consumes: `pack_batch` from Task 3.
- Produces:
  - `pending_records(all_records: list[str], done: list[str]) -> list[str]` — `all_records` minus `done`, preserving `all_records` order.
  - `count_batches(pending: list[str], attribute: str, limit: int) -> int | None` — exact number of batches to finish `pending`; `None` if a single ID can't fit the limit.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_query_core.py`:
```python
def test_pending_records_excludes_done_preserves_order():
    assert qc.pending_records(["a", "b", "c", "d"], ["b", "d"]) == ["a", "c"]


def test_count_batches_exact():
    pending = ["11", "22", "33", "44", "55", "66"]
    limit = qc.query_length("A", ["11", "22"])   # exactly fits two per batch
    assert qc.count_batches(pending, "A", limit) == 3


def test_count_batches_none_when_single_too_big():
    assert qc.count_batches(["1840833"], "DBKEY", 10) is None


def test_full_round_trip_reproduces_pending_in_order():
    pending = [str(i) for i in range(1000, 1075)]
    remaining, collected = list(pending), []
    while remaining:
        b = qc.pack_batch(remaining, "COL", 60)
        assert b, "at least one ID must always fit"
        collected.extend(b)
        remaining = remaining[len(b):]
    assert collected == pending      # no gaps, no dupes, original order
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_query_core.py -v`
Expected: FAIL — `AttributeError: module 'query_core' has no attribute 'pending_records'`.

- [ ] **Step 3: Write minimal implementation**

Append to `query_core.py`:
```python
def pending_records(all_records, done):
    done_set = set(done)                     # membership only; order comes from all_records
    return [x for x in all_records if x not in done_set]


def count_batches(pending, attribute, limit):
    remaining = list(pending)
    n = 0
    while remaining:
        b = pack_batch(remaining, attribute, limit)
        if not b:
            return None                      # a single ID can't fit — cannot complete
        n += 1
        remaining = remaining[len(b):]
    return n
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_query_core.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```powershell
git add query_core.py tests/test_query_core.py
git commit -m @'
feat: add pending_records and count_batches

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01953vEfdui6nzYzzpbfXnRB
'@
```

---

### Task 5: storage — record files & settings

**Files:**
- Create: `storage.py`
- Test: `tests/test_storage.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `read_lines(path: str) -> list[str]` — stripped non-blank lines in file order; `[]` if file missing.
  - `write_lines(path: str, items: list[str]) -> None` — one item per line (overwrite).
  - `append_lines(path: str, items: list[str]) -> None` — append one item per line.
  - `clear_file(path: str) -> None` — truncate to empty.
  - `load_settings(path: str) -> dict` — parsed JSON, `{}` if missing/corrupt.
  - `save_settings(path: str, data: dict) -> None` — write JSON.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_storage.py`:
```python
import storage


def test_write_and_read_lines_roundtrip(tmp_path):
    p = str(tmp_path / "all.txt")
    storage.write_lines(p, ["a", "b", "c"])
    assert storage.read_lines(p) == ["a", "b", "c"]


def test_read_lines_missing_file_returns_empty(tmp_path):
    assert storage.read_lines(str(tmp_path / "nope.txt")) == []


def test_read_lines_strips_and_skips_blanks(tmp_path):
    p = tmp_path / "all.txt"
    p.write_text("a\n\n b \n\n", encoding="utf-8")
    assert storage.read_lines(str(p)) == ["a", "b"]


def test_append_lines(tmp_path):
    p = str(tmp_path / "done.txt")
    storage.write_lines(p, ["a"])
    storage.append_lines(p, ["b", "c"])
    assert storage.read_lines(p) == ["a", "b", "c"]


def test_clear_file(tmp_path):
    p = str(tmp_path / "all.txt")
    storage.write_lines(p, ["a", "b"])
    storage.clear_file(p)
    assert storage.read_lines(p) == []


def test_settings_roundtrip(tmp_path):
    p = str(tmp_path / "settings.json")
    storage.save_settings(p, {"attribute": "DBKEY", "limit": 1200})
    assert storage.load_settings(p) == {"attribute": "DBKEY", "limit": 1200}


def test_load_settings_missing_returns_empty(tmp_path):
    assert storage.load_settings(str(tmp_path / "no.json")) == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_storage.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'storage'`.

- [ ] **Step 3: Write minimal implementation**

Create `storage.py`:
```python
"""File and settings persistence for the Incremental Query Filter."""
import json
import os


def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def write_lines(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(f"{it}\n")


def append_lines(path, items):
    with open(path, "a", encoding="utf-8") as f:
        for it in items:
            f.write(f"{it}\n")


def clear_file(path):
    open(path, "w", encoding="utf-8").close()


def load_settings(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_storage.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```powershell
git add storage.py tests/test_storage.py
git commit -m @'
feat: add storage module for records and settings

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01953vEfdui6nzYzzpbfXnRB
'@
```

---

### Task 6: main.py — UI layout & widgets

**Files:**
- Create: `main.py` (overwrites the old file)

**Interfaces:**
- Consumes: `query_core` and `storage` modules (imported, wired in Task 7).
- Produces: `App(ctk.CTk)` with widget attributes `attr_entry`, `limit_entry`, `progress`, `percent_lbl`, `totals_lbl`, `batches_lbl`, `paste_box`, `pending_box`, `done_box`, `next_btn`, `query_box`, `status_lbl`; helper methods `_set_box`, `_toggle_ontop`, `_set_alpha`; and stub callbacks `load_list`, `next_batch`, `clear_all`, `refresh`, `_load_state` (real bodies land in Task 7).

- [ ] **Step 1: Write `main.py` with full layout and stub callbacks**

Create `main.py`:
```python
"""Incremental Query Filter — desktop UI."""
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import pyperclip

import query_core as qc
import storage

ALL_RECORDS = "all_records.txt"
EXECUTED = "executed_records.txt"
SETTINGS = "settings.json"

ctk.set_appearance_mode("dark")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Incremental query filter")
        self.geometry("920x660")
        self._build_ui()
        self._load_state()

    # ---------- UI construction ----------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        ctk.CTkLabel(top, text="Attribute:").grid(row=0, column=0, padx=(12, 4), pady=10)
        self.attr_entry = ctk.CTkEntry(top, width=180)
        self.attr_entry.grid(row=0, column=1, padx=(0, 20), pady=10)
        ctk.CTkLabel(top, text="Char limit:").grid(row=0, column=2, padx=(0, 4), pady=10)
        self.limit_entry = ctk.CTkEntry(top, width=100)
        self.limit_entry.grid(row=0, column=3, padx=(0, 12), pady=10)

        card = ctk.CTkFrame(self)
        card.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text="OVERALL PROGRESS", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 2))
        self.progress = ctk.CTkProgressBar(card)
        self.progress.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        self.progress.set(0)
        self.percent_lbl = ctk.CTkLabel(card, text="0%")
        self.percent_lbl.grid(row=1, column=1, padx=12)
        self.totals_lbl = ctk.CTkLabel(card, text="Total 0  ·  Done 0  ·  Remaining 0", anchor="w")
        self.totals_lbl.grid(row=2, column=0, sticky="w", padx=12, pady=(2, 2))
        self.batches_lbl = ctk.CTkLabel(card, text="▶  Batches remaining:  0",
                                        font=ctk.CTkFont(size=15, weight="bold"), anchor="w")
        self.batches_lbl.grid(row=3, column=0, sticky="w", padx=12, pady=(2, 10))

        panels = ctk.CTkFrame(self)
        panels.grid(row=2, column=0, padx=16, pady=8, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        for c in range(3):
            panels.grid_columnconfigure(c, weight=1)
        panels.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(panels, text="PASTE COLUMN").grid(row=0, column=0, pady=(8, 2))
        self.paste_box = ctk.CTkTextbox(panels, width=240)
        self.paste_box.grid(row=1, column=0, padx=8, sticky="nsew")
        ctk.CTkButton(panels, text="Load list", command=self.load_list).grid(row=2, column=0, pady=8)

        ctk.CTkLabel(panels, text="PENDING (in order)").grid(row=0, column=1, pady=(8, 2))
        self.pending_box = ctk.CTkTextbox(panels, width=240)
        self.pending_box.grid(row=1, column=1, padx=8, sticky="nsew")

        ctk.CTkLabel(panels, text="DONE").grid(row=0, column=2, pady=(8, 2))
        self.done_box = ctk.CTkTextbox(panels, width=240)
        self.done_box.grid(row=1, column=2, padx=8, sticky="nsew")

        actions = ctk.CTkFrame(self)
        actions.grid(row=3, column=0, padx=16, pady=8, sticky="ew")
        self.next_btn = ctk.CTkButton(actions, text="▶ Next batch", command=self.next_batch,
                                      height=40, font=ctk.CTkFont(size=15, weight="bold"))
        self.next_btn.grid(row=0, column=0, padx=12, pady=10)
        ctk.CTkButton(actions, text="Clear", command=self.clear_all,
                      fg_color="firebrick1", hover_color="brown1").grid(row=0, column=1, padx=12, pady=10)

        bottom = ctk.CTkFrame(self)
        bottom.grid(row=4, column=0, padx=16, pady=(8, 16), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(bottom, text="Current query", anchor="w").grid(
            row=0, column=0, sticky="w", padx=12, pady=(8, 2))
        self.query_box = ctk.CTkTextbox(bottom, height=70)
        self.query_box.grid(row=1, column=0, columnspan=2, padx=12, sticky="ew")
        self.status_lbl = ctk.CTkLabel(bottom, text="", anchor="w")
        self.status_lbl.grid(row=2, column=0, sticky="w", padx=12, pady=(4, 8))

        self.ontop_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(bottom, text="Stay on top", variable=self.ontop_var,
                        command=self._toggle_ontop).grid(row=2, column=1, sticky="e", padx=12)
        self.alpha = ctk.CTkSlider(bottom, from_=0.3, to=1.0, command=self._set_alpha)
        self.alpha.set(1.0)
        self.alpha.grid(row=3, column=1, sticky="e", padx=12, pady=(0, 8))

    # ---------- helpers ----------
    def _set_box(self, box, lines):
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", "\n".join(lines))
        box.configure(state="disabled")   # pending/done/query are read-only

    def _toggle_ontop(self):
        self.attributes("-topmost", self.ontop_var.get())

    def _set_alpha(self, value):
        self.attributes("-alpha", float(value))

    # ---------- callbacks (stubs — implemented in Task 7) ----------
    def load_list(self):
        print("load_list stub")

    def next_batch(self):
        print("next_batch stub")

    def clear_all(self):
        print("clear_all stub")

    def refresh(self):
        print("refresh stub")

    def _load_state(self):
        print("_load_state stub")


if __name__ == "__main__":
    App().mainloop()
```

- [ ] **Step 2: Run the app to verify the layout renders**

Run: `python main.py`
Expected: a ~920×660 dark window opens showing the attribute/limit row, an OVERALL PROGRESS card (empty bar, "Batches remaining: 0"), three side-by-side panels (PASTE COLUMN with a "Load list" button, PENDING, DONE), a "▶ Next batch" button, a red "Clear" button, a "Current query" box, a "Stay on top" checkbox, and a transparency slider. Clicking buttons prints the stub messages to the console. Close the window.

- [ ] **Step 3: Commit**

```powershell
git add main.py
git commit -m @'
feat: build v2 UI layout with progress card and ordered panels

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01953vEfdui6nzYzzpbfXnRB
'@
```

---

### Task 7: main.py — wire behavior

**Files:**
- Modify: `main.py` (replace the five stub methods, add `_validate`)

**Interfaces:**
- Consumes: all of `query_core` (Tasks 2–4) and `storage` (Task 5); the widgets built in Task 6.
- Produces: a fully functional app.

- [ ] **Step 1: Replace the stub-callbacks block**

In `main.py`, replace this block:
```python
    # ---------- callbacks (stubs — implemented in Task 7) ----------
    def load_list(self):
        print("load_list stub")

    def next_batch(self):
        print("next_batch stub")

    def clear_all(self):
        print("clear_all stub")

    def refresh(self):
        print("refresh stub")

    def _load_state(self):
        print("_load_state stub")
```
with this implementation:
```python
    # ---------- logic ----------
    def _validate(self):
        attribute = self.attr_entry.get().strip()
        limit_raw = self.limit_entry.get().strip()
        if not attribute:
            messagebox.showinfo("Missing attribute", "Please enter a query attribute.")
            return None
        if not limit_raw.isdigit() or int(limit_raw) <= 0:
            messagebox.showinfo("Bad limit", "Char limit must be a positive whole number.")
            return None
        return attribute, int(limit_raw)

    def refresh(self):
        all_records = qc.dedup_preserve_order(storage.read_lines(ALL_RECORDS))
        done = storage.read_lines(EXECUTED)
        pending = qc.pending_records(all_records, done)
        self._set_box(self.pending_box, pending)
        self._set_box(self.done_box, [x for x in all_records if x not in set(pending)])

        total = len(all_records)
        done_n = total - len(pending)
        frac = (done_n / total) if total else 0
        self.progress.set(frac)
        self.percent_lbl.configure(text=f"{round(frac * 100)}%")
        self.totals_lbl.configure(
            text=f"Total {total}  ·  Done {done_n}  ·  Remaining {len(pending)}")

        attribute = self.attr_entry.get().strip()
        limit_raw = self.limit_entry.get().strip()
        if pending and attribute and limit_raw.isdigit() and int(limit_raw) > 0:
            n = qc.count_batches(pending, attribute, int(limit_raw))
            txt = "▶  Batches remaining:  —  (limit too small)" if n is None \
                else f"▶  Batches remaining:  {n}"
        elif not pending and total:
            txt = "✅  All done"
        else:
            txt = "▶  Batches remaining:  —"
        self.batches_lbl.configure(text=txt)

        self.next_btn.configure(state="disabled" if not pending else "normal")

    def load_list(self):
        items = qc.dedup_preserve_order(self.paste_box.get("1.0", "end-1c").splitlines())
        if not items:
            messagebox.showinfo("Nothing to load", "Paste a column of IDs first.")
            return
        if storage.read_lines(EXECUTED):
            if not messagebox.askyesno(
                    "Start fresh?", "Loading a new list resets all progress. Continue?"):
                return
        storage.write_lines(ALL_RECORDS, items)
        storage.clear_file(EXECUTED)
        self.next_btn.configure(text="▶ Next batch")
        self.status_lbl.configure(text=f"Loaded {len(items)} records.")
        self.refresh()

    def next_batch(self):
        validated = self._validate()
        if not validated:
            return
        attribute, limit = validated
        storage.save_settings(SETTINGS, {"attribute": attribute, "limit": limit})

        all_records = qc.dedup_preserve_order(storage.read_lines(ALL_RECORDS))
        pending = qc.pending_records(all_records, storage.read_lines(EXECUTED))
        if not pending:
            self.status_lbl.configure(text="✅ All done — nothing left to query.")
            self.refresh()
            return
        batch = qc.pack_batch(pending, attribute, limit)
        if not batch:
            messagebox.showinfo(
                "Limit too small", "A single ID won't fit in the character limit. Raise the limit.")
            return
        query = qc.build_query(attribute, batch)
        pyperclip.copy(query)
        storage.append_lines(EXECUTED, batch)
        self._set_box(self.query_box, [query])
        used = qc.query_length(attribute, batch)
        self.status_lbl.configure(
            text=f"Copied {len(batch)} IDs ✓  ·  {used} / {limit} chars used")
        self.next_btn.configure(text="▶ Next Query")
        self.refresh()

    def clear_all(self):
        if not messagebox.askyesno(
                "Clear everything?", "This wipes the loaded list AND all progress. Continue?"):
            return
        storage.clear_file(ALL_RECORDS)
        storage.clear_file(EXECUTED)
        self.paste_box.delete("1.0", "end")
        self._set_box(self.query_box, [])
        self.status_lbl.configure(text="")
        self.next_btn.configure(text="▶ Next batch")
        self.refresh()

    def _load_state(self):
        s = storage.load_settings(SETTINGS)
        if s.get("attribute"):
            self.attr_entry.insert(0, s["attribute"])
        if s.get("limit"):
            self.limit_entry.insert(0, str(s["limit"]))
        self.refresh()
```

- [ ] **Step 2: Verify the core logic still passes**

Run: `python -m pytest -v`
Expected: 18 passed (11 in `test_query_core.py` + 7 in `test_storage.py`; no regression, `main.py` imports cleanly).

- [ ] **Step 3: Manual end-to-end verification**

Run: `python main.py`, then:
1. Paste this column into PASTE COLUMN (each ID on its own line):
   `1840833` `1706494` `1840916` `1882571` `1712459` (five lines). Click **Load list** → confirm "reset progress" if asked.
2. Verify PENDING shows the five IDs **top-to-bottom in that exact order**; totals read `Total 5 · Done 0 · Remaining 5`.
3. Set Attribute `DBKEY`, Char limit `40`. Batches remaining should show a number ≥ 2.
4. Click **▶ Next batch**. The Current query box must read exactly `DBKEY in ('1840833','1706494',…)` (single quotes, no spaces) and paste from the clipboard (Ctrl+V somewhere) must match. Status shows `Copied N IDs ✓ · X / 40 chars used`. PENDING shrinks, DONE grows, progress bar advances, Batches remaining decrements.
5. Keep clicking until **✅ All done** appears and **Next batch** disables — with **no crash**.
6. Set Char limit `5`, reload the list, click Next batch → expect the "Limit too small" dialog, no crash.

- [ ] **Step 4: Commit**

```powershell
git add main.py
git commit -m @'
feat: wire load/next-batch/clear, progress, and settings persistence

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01953vEfdui6nzYzzpbfXnRB
'@
```

---

### Task 8: Docs & final acceptance sweep

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the finished app.
- Produces: updated docs; a recorded full-suite pass.

- [ ] **Step 1: Update `README.md`**

Update the Features section to reflect v2 and correct the query format. Replace the Features list with:
```markdown
## 🔹 Features
- Paste a column of data (IDs, DB keys, etc.) — order is preserved exactly.
- Generate progressive `IN (...)` queries under a **custom character limit**, e.g. `DBKEY in ('1840833','1706494')` (single-quoted, no spaces).
- Live progress: total / done / remaining, a progress bar, and a **batches-remaining** count.
- One click copies the current batch to the clipboard (`pyperclip`).
- Explicit **Load list** (fresh job) and confirmed **Clear**; progress auto-saved between runs.
- UI tweaks: transparency, stay-on-top.
```

- [ ] **Step 2: Run the full test suite**

Run: `python -m pytest -v`
Expected: 18 passed (11 in `test_query_core.py` + 7 in `test_storage.py`).

- [ ] **Step 3: Acceptance checklist (from the spec)**

Confirm each, using the app:
1. Pasted order preserved in PENDING (top = first pasted ID).
2. Query matches `DBKEY in ('…','…')` byte-for-byte.
3. Each batch ≤ char limit and as full as possible.
4. Batches-remaining correct and decrements.
5. Progress bar / totals update live.
6. No crash on: limit too small for one ID, all done, empty/invalid attribute or limit, missing files.
7. Progress persists across restart; Load list resets (with confirm); Clear wipes (with confirm).
8. `pip install -r requirements.txt` succeeds clean.

- [ ] **Step 4: Commit**

```powershell
git add README.md
git commit -m @'
docs: update README for v2 (order preservation, format, batches remaining)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01953vEfdui6nzYzzpbfXnRB
'@
```

---

## Notes for the implementer

- Run all `pytest` and `python main.py` commands **from the repo root** (`C:\AI_space\work\Incremental-query-filter`) so `import query_core` / `import storage` resolve.
- The repo already contains `all_records.txt` and `executed_records.txt` with sample data; the app loads them on start. Use **Clear** or **Load list** to start clean.
- `__pycache__/` holds stale compiled copies of old modules — ignore them; they're not imported by the new code.
- Phase 2 (cloud automation via screen recording) is intentionally **not** in this plan.
