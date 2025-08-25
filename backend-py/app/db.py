# app/db.py
import os
from pathlib import Path
import aiosqlite
import sqlite3
import logging
from typing import AsyncIterator

log = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "./data/budget.db")

SCHEMA_CANDIDATES = [
    "db/migrate.sql",
    "backend/db/migrate.sql",
]

async def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    schema_path = next((p for p in SCHEMA_CANDIDATES if Path(p).exists()), None)
    if not schema_path:
        raise FileNotFoundError("migrate.sql not found in: " + ", ".join(SCHEMA_CANDIDATES))

    sql = Path(schema_path).read_text(encoding="utf-8")

    log.info("🗄️  Initializing database...")
    async with aiosqlite.connect(DB_PATH, timeout=5) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        await db.executescript(sql)
        await db.commit()
    log.info("✅ Migrations applied")

async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """FastAPI dependency: открывает подключение к SQLite и закрывает после запроса."""
    db = await aiosqlite.connect(DB_PATH, timeout=5)
    db.row_factory = sqlite3.Row
    await db.execute("PRAGMA foreign_keys=ON;")
    try:
        yield db
    finally:
        await db.close()
