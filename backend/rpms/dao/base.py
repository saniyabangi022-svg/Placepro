"""Tiny helpers shared by all DAOs. SQL fragments are constants; values are always bound parameters."""


def like(v):
    v = (v or "").strip() if isinstance(v, str) else v
    return f"%{v}%" if v else None


def where(filters):
    """filters = [(sql_fragment_with_%s, value)]; entries whose value is empty are skipped."""
    parts, params = [], []
    for frag, val in filters:
        if val not in (None, ""):
            parts.append(frag); params.append(val)
    return (" WHERE " + " AND ".join(parts) if parts else ""), params


def paged(cur, select_sql, count_sql, w, params, order, page, size):
    total = cur.one(count_sql + w, params)["n"]
    rows = cur.all(f"{select_sql}{w} ORDER BY {order} LIMIT %s OFFSET %s", params + [size, (page - 1) * size])
    return {"items": rows, "total": total, "page": page, "page_size": size}
