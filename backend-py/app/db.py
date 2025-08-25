import aiosqlite
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "budget.db")

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = None
    
    async def connect(self):
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        # Enable WAL mode for better concurrency
        await self._connection.execute("PRAGMA journal_mode=WAL")
        # Enable foreign keys
        await self._connection.execute("PRAGMA foreign_keys=ON")
        return self._connection
    
    async def disconnect(self):
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    @asynccontextmanager
    async def transaction(self):
        if not self._connection:
            await self.connect()
        
        try:
            await self._connection.execute("BEGIN")
            yield self._connection
            await self._connection.commit()
        except Exception:
            await self._connection.rollback()
            raise

# Global database instance
db_instance = Database(DATABASE_URL)

async def get_db() -> aiosqlite.Connection:
    """Get database connection"""
    if not db_instance._connection:
        await db_instance.connect()
    return db_instance._connection

async def init_db():
    """Initialize database with schema"""
    logger.info("🗄️  Initializing database...")
    
    db = await get_db()
    
    # Read and execute migrations
    migrations_path = os.path.join(os.path.dirname(__file__), "migrations.sql")
    
    try:
        with open(migrations_path, "r") as f:
            migrations = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in migrations.split(';') if stmt.strip()]
        
        for statement in statements:
            await db.execute(statement)
        
        await db.commit()
        logger.info("✅ Database schema applied successfully")
        
    except FileNotFoundError:
        logger.error(f"❌ Migrations file not found: {migrations_path}")
        # Create basic schema inline as fallback
        await create_basic_schema(db)
    except Exception as e:
        logger.error(f"❌ Failed to apply migrations: {e}")
        raise

async def create_basic_schema(db: aiosqlite.Connection):
    """Create basic schema if migrations file is not found"""
    logger.info("📝 Creating basic schema...")
    
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
        color TEXT NOT NULL,
        icon TEXT,
        sync_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE(user_id, sync_id)
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        description TEXT NOT NULL,
        date TIMESTAMP NOT NULL,
        sync_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE,
        UNIQUE(user_id, sync_id)
    );

    CREATE INDEX IF NOT EXISTS idx_categories_user_id ON categories(user_id);
    CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(type);
    CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_category_id ON transactions(category_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
    CREATE INDEX IF NOT EXISTS idx_transactions_sync_id ON transactions(sync_id);
    CREATE INDEX IF NOT EXISTS idx_categories_sync_id ON categories(sync_id);

    CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users FOR EACH ROW
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

    CREATE TRIGGER IF NOT EXISTS update_categories_timestamp 
    AFTER UPDATE ON categories FOR EACH ROW
    BEGIN
        UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

    CREATE TRIGGER IF NOT EXISTS update_transactions_timestamp 
    AFTER UPDATE ON transactions FOR EACH ROW
    BEGIN
        UPDATE transactions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """
    
    statements = [stmt.strip() for stmt in schema.split(';') if stmt.strip()]
    
    for statement in statements:
        await db.execute(statement)
    
    await db.commit()
    logger.info("✅ Basic schema created successfully")