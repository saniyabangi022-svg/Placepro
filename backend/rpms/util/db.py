"""MySQL connectivity (mysql-connector-python) with a connection pool.

Usage in services:
    with session() as cur:          # one transaction: commit on success, rollback on error
        cur.run("UPDATE ... WHERE id=%s", (1,))
Every query is parameterized - user input is never concatenated into SQL.
"""
import logging
from contextlib import contextmanager
from datetime import timedelta

from mysql.connector import Error as MySQLError, errorcode, pooling

from ..exception.errors import DatabaseError, DuplicateRecordError, ValidationFailedError
from .config import settings

log = logging.getLogger("placepro.db")
_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="rpms_pool", pool_size=settings.DB_POOL_SIZE,
                host=settings.DB_HOST, port=settings.DB_PORT, user=settings.DB_USER,
                password=settings.DB_PASSWORD, database=settings.DB_NAME, charset="utf8mb4")
        except MySQLError as e:
            log.error("DB connection failed: %s", e)
            raise DatabaseError("Cannot connect to the database. Check MySQL is running and the .env settings.")
    return _pool


def _clean(row):
    """MySQL TIME arrives as timedelta; turn it into 'HH:MM' for JSON."""
    if row:
        for k, v in row.items():
            if isinstance(v, timedelta):
                s = int(v.total_seconds()); row[k] = f"{s // 3600:02d}:{s % 3600 // 60:02d}"
    return row


class Cursor:
    def __init__(self, cur): self._c = cur

    def _exec(self, sql, params):
        try:
            self._c.execute(sql, params or ())
        except MySQLError as e:
            if e.errno == errorcode.ER_DUP_ENTRY:
                raise DuplicateRecordError("A record with the same unique value already exists.")
            if e.errno in (errorcode.ER_NO_REFERENCED_ROW_2, errorcode.ER_ROW_IS_REFERENCED_2):
                raise ValidationFailedError("Referenced record does not exist or is still in use.")
            if e.errno in (4025, 3819):  # CHECK constraint (MariaDB / MySQL)
                raise ValidationFailedError("A value violates a database rule (CHECK constraint).")
            log.error("SQL error %s: %s | %s", e.errno, e.msg, sql)
            raise DatabaseError("A database error occurred.")

    def all(self, sql, params=None):
        self._exec(sql, params); return [_clean(r) for r in self._c.fetchall()]

    def one(self, sql, params=None):
        self._exec(sql, params); return _clean(self._c.fetchone())

    def run(self, sql, params=None):
        self._exec(sql, params); return self._c.lastrowid


@contextmanager
def session():
    conn = _get_pool().get_connection()
    try:
        yield Cursor(conn.cursor(dictionary=True))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ping():
    with session() as cur:
        return cur.one("SELECT 1 AS ok")["ok"] == 1
