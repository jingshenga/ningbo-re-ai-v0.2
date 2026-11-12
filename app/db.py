from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from app.settings import DATABASE_URL


@contextmanager
def session():
    """One short DB transaction; commits on success, rolls back on error."""
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=8) as conn:
        yield conn
