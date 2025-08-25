package db

import (
    "database/sql"
    _ "github.com/mattn/go-sqlite3"
    "os"
)

func Open(path string) (*sql.DB, error) {
    if err := os.MkdirAll("./data", 0755); err != nil { return nil, err }
    dsn := path + "?_busy_timeout=5000&_journal_mode=WAL&_foreign_keys=on"
    db, err := sql.Open("sqlite3", dsn)
    if err != nil { return nil, err }
    // Pragmas on connection
    if _, err = db.Exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`); err != nil {
        return nil, err
    }
    return db, nil
}