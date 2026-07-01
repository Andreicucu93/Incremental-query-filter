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
