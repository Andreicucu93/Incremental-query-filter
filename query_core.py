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
