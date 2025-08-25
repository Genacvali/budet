#!/bin/bash

echo "=== Budget PWA Backend Diagnostics ==="
echo

# 1. Проверка структуры файлов
echo "1. Checking file structure..."
echo "📁 Required files:"
for file in "main.go" "db/migrate.sql" "db/sqlite.go" "api/auth.go" "api/entities.go" "api/sync.go" "internal/models.go" "internal/jwt.go"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ MISSING: $file"
    fi
done
echo

# 2. Проверка go.mod
echo "2. Checking go.mod..."
if [ -f "go.mod" ]; then
    echo "  ✅ go.mod exists"
    echo "  📋 Module: $(head -1 go.mod)"
else
    echo "  ❌ MISSING: go.mod"
fi
echo

# 3. Проверка зависимостей
echo "3. Checking dependencies..."
go list -m all 2>/dev/null | head -5
echo

# 4. Проверка директории data
echo "4. Checking data directory..."
if [ -d "data" ]; then
    echo "  ✅ data/ directory exists"
    ls -la data/
else
    echo "  ⚠️  Creating data/ directory"
    mkdir -p data
fi
echo

# 5. Проверка SQLite
echo "5. Testing SQLite connection..."
if command -v sqlite3 &> /dev/null; then
    echo "  ✅ sqlite3 available"
    echo "CREATE TABLE test(id INTEGER);" | sqlite3 data/test.db 2>/dev/null && echo "  ✅ SQLite write test OK" || echo "  ❌ SQLite write test failed"
    rm -f data/test.db
else
    echo "  ⚠️  sqlite3 not installed"
fi
echo

# 6. Проверка переменных окружения
echo "6. Checking environment..."
if [ -n "$JWT_SECRET" ]; then
    echo "  ✅ JWT_SECRET is set (length: ${#JWT_SECRET})"
else
    echo "  ⚠️  JWT_SECRET not set (using default)"
fi

if [ -n "$DB_PATH" ]; then
    echo "  ✅ DB_PATH is set: $DB_PATH"
else
    echo "  ℹ️  DB_PATH not set (using default: ./data/budget.db)"
fi
echo

# 7. Проверка сборки
echo "7. Testing build..."
go build -o budget-api-test main.go 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ Build successful"
    rm -f budget-api-test
else
    echo "  ❌ Build failed"
    echo "  📝 Error details:"
    go build -o budget-api-test main.go
fi
echo

# 8. Проверка портов
echo "8. Checking ports..."
if lsof -i :8080 >/dev/null 2>&1; then
    echo "  ⚠️  Port 8080 already in use:"
    lsof -i :8080
else
    echo "  ✅ Port 8080 available"
fi
echo

echo "=== Diagnostics Complete ==="
echo "To fix common issues:"
echo "1. Set JWT_SECRET: export JWT_SECRET='your-secret-key-here'"
echo "2. Install SQLite dev: sudo dnf install -y sqlite-devel gcc"  
echo "3. Run with CGO: CGO_ENABLED=1 go run main.go"
echo "4. Check firewall: sudo firewall-cmd --list-ports"