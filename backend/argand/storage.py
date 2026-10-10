"""SQLite storage for immutable attempts, voice snapshots and evaluations."""

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException

DB = Path(
    os.environ.get(
        "ARGAND_DB", Path(__file__).resolve().parents[2] / "attempts.sqlite3"
    )
)


@contextmanager
def db():
    c = sqlite3.connect(DB)
    c.execute(
        "CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, data TEXT NOT NULL)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS evaluations(id TEXT PRIMARY KEY, attempt TEXT NOT NULL, data TEXT NOT NULL)"
    )
    try:
        with c:
            yield c
    finally:
        c.close()


def get_attempt(ident):
    with db() as c:
        r = c.execute("SELECT data FROM attempts WHERE id=?", (ident,)).fetchone()
    if not r:
        raise HTTPException(404, "Attempt not found")
    return json.loads(r[0])
