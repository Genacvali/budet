PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('income','expense')),
  icon TEXT, color TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  limit_type TEXT NOT NULL DEFAULT 'none',         -- none|fixed|percent
  limit_value REAL NOT NULL DEFAULT 0,             -- сумма или %
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  currency TEXT NOT NULL DEFAULT 'RUB',
  expected_date TEXT, icon TEXT, color TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS rules (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  category_id TEXT NOT NULL,
  percent REAL NOT NULL DEFAULT 0,
  cap_cents INTEGER,                                -- максимум для категории
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(source_id) REFERENCES sources(id),
  FOREIGN KEY(category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS operations (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('income','expense')),
  source_id TEXT,                                   -- для income
  category_id TEXT NOT NULL,
  wallet TEXT,                                      -- опц.
  amount_cents INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'RUB',
  rate REAL NOT NULL DEFAULT 1,                     -- курс к базовой валюте
  date TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT,
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(source_id) REFERENCES sources(id),
  FOREIGN KEY(category_id) REFERENCES categories(id)
);

CREATE INDEX IF NOT EXISTS idx_updated_at ON operations(updated_at);
CREATE INDEX IF NOT EXISTS idx_deleted_at ON operations(deleted_at);