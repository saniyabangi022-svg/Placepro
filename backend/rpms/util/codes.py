"""Business-code generators (CAN-2026-0001, COM-001, APP-2026-0001, OFF-2026-001)."""
from datetime import date

# (table, column, prefix-template, zero-pad). Values are internal constants, never user input.
_SPEC = {"candidate": ("candidates", "candidate_code", "CAN-{y}-", 4),
         "company": ("companies", "company_code", "COM-", 3),
         "application": ("applications", "application_code", "APP-{y}-", 4),
         "offer": ("offers", "offer_code", "OFF-{y}-", 3)}


def next_code(cur, kind: str) -> str:
    table, col, tpl, pad = _SPEC[kind]
    prefix = tpl.format(y=date.today().year)
    row = cur.one(f"SELECT MAX(CAST(SUBSTRING({col}, %s) AS UNSIGNED)) AS n FROM {table} WHERE {col} LIKE %s",
                  (len(prefix) + 1, prefix + "%"))
    return f"{prefix}{(row['n'] or 0) + 1:0{pad}d}"
