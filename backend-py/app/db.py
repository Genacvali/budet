# app/db.py
import os
from pathlib import Path
import aiosqlite
import logging

log = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "./data/budget.db")

SCHEMA_CANDIDATES = [
    "db/migrate.sql",             # backend-py/db/migrate.sql
    "backend/db/migrate.sql",     # если запускают из корня репо (старая структура)
]

async def init_db():
    # гарантируем директорию
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    # ищем migrate.sql
    schema_path = None
    for p in SCHEMA_CANDIDATES:
        if Path(p).exists():
            schema_path = p
            break
    if not schema_path:
        raise FileNotFoundError("migrate.sql not found in: " + ", ".join(SCHEMA_CANDIDATES))

    sql = Path(schema_path).read_text(encoding="utf-8")

    log.info("🗄️  Initializing database...")

    async with aiosqlite.connect(DB_PATH, timeout=5) as db:
        # PRAGMA — сразу после connect
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        # ВАЖНО: выполняем весь скрипт целиком
        await db.executescript(sql)
        await db.commit()

    log.info("✅ Migrations applied")
