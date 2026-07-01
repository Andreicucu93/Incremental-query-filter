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
