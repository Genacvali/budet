#!/bin/bash
# Quick update script for Budget PWA on CentOS 9
set -euo pipefail

SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST:-your-server-ip}"
REMOTE_DIR="/opt/budget-pwa"

echo "🔄 Updating Budget PWA on server..."

# Сборка только фронтенда (обычно меняется чаще)
echo "📦 Building frontend..."
cd frontend

# Проверяем наличие node_modules
if [ ! -d "node_modules" ]; then
  echo "📥 Installing dependencies..."
  npm install --legacy-peer-deps
fi

npm run build
cd ..

# Создаем пакет обновления
echo "📁 Preparing update package..."
rm -rf update-temp
mkdir -p update-temp
cp -r frontend/build/* update-temp/

# Создаем скрипт обновления
cat > update-temp/update.sh << 'EOF'
#!/bin/bash
set -euo pipefail

echo "🔄 Updating frontend files..."
sudo cp -r /tmp/budget-update/* /opt/budget-pwa/frontend/

echo "🔄 Restarting nginx..."
sudo systemctl reload nginx

echo "✅ Update completed!"
EOF

chmod +x update-temp/update.sh

# Загружаем на сервер
echo "📤 Uploading update to server..."
ssh "$SERVER_USER@$SERVER_HOST" "mkdir -p /tmp/budget-update"
scp -r update-temp/* "$SERVER_USER@$SERVER_HOST:/tmp/budget-update/"

# Применяем обновление
echo "⚙️ Applying update..."
ssh "$SERVER_USER@$SERVER_HOST" "cd /tmp/budget-update && ./update.sh"

# Очистка
rm -rf update-temp
ssh "$SERVER_USER@$SERVER_HOST" "rm -rf /tmp/budget-update"

echo "✅ Update completed successfully!"
echo "🌐 Check your PWA at: http://$SERVER_HOST"