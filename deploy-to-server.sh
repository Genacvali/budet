#!/bin/bash
# Deploy Budget PWA to CentOS 9 Server
set -euo pipefail

SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST:-your-server-ip}"
APP_NAME="budget-pwa"
REMOTE_DIR="/opt/$APP_NAME"

echo "🚀 Deploying Budget PWA to CentOS 9 Server"
echo "Server: $SERVER_USER@$SERVER_HOST"
echo "Remote path: $REMOTE_DIR"

# Сборка фронтенда
echo "📦 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Подготовка файлов для деплоя
echo "📁 Preparing deployment package..."
rm -rf deploy-temp
mkdir -p deploy-temp

# Копируем собранный фронтенд
cp -r frontend/build deploy-temp/frontend

# Копируем бэкенд
cp -r backend-py deploy-temp/backend

# Копируем конфигурационные файлы
cp deploy/*.conf deploy-temp/
cp deploy/*.service deploy-temp/

# Создаем деплой скрипт для сервера
cat > deploy-temp/server-install.sh << 'EOF'
#!/bin/bash
set -euo pipefail

APP_NAME="budget-pwa"
APP_DIR="/opt/$APP_NAME"
NGINX_CONF="/etc/nginx/conf.d/budget.conf"
SYSTEMD_SERVICE="/etc/systemd/system/budget-api.service"

echo "🔧 Installing Budget PWA on CentOS 9..."

# Создаем директорию приложения
sudo mkdir -p "$APP_DIR"
sudo chown -R $(whoami):$(whoami) "$APP_DIR"

# Копируем файлы
echo "📁 Copying application files..."
cp -r frontend/* "$APP_DIR/frontend/"
cp -r backend/* "$APP_DIR/backend/"

# Устанавливаем Python зависимости
echo "🐍 Installing Python dependencies..."
cd "$APP_DIR/backend"
sudo dnf install -y python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настраиваем nginx
echo "🌐 Configuring nginx..."
sudo dnf install -y nginx
sudo cp budget-nginx.conf "$NGINX_CONF"
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# Настраиваем systemd service
echo "⚙️ Setting up systemd service..."
sudo cp budget-api.service "$SYSTEMD_SERVICE"
sudo systemctl daemon-reload
sudo systemctl enable budget-api
sudo systemctl restart budget-api

# Открываем порты в firewall
echo "🔓 Configuring firewall..."
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# Проверяем статус
echo "✅ Checking services status..."
sudo systemctl status nginx --no-pager
sudo systemctl status budget-api --no-pager

echo "🎉 Deployment completed!"
echo "App should be available at: http://$(curl -s ifconfig.me)"
EOF

chmod +x deploy-temp/server-install.sh

# Копируем на сервер
echo "📤 Uploading to server..."
scp -r deploy-temp/* "$SERVER_USER@$SERVER_HOST:/tmp/budget-deploy/"

# Запускаем установку на сервере
echo "⚙️ Running installation on server..."
ssh "$SERVER_USER@$SERVER_HOST" "cd /tmp/budget-deploy && chmod +x server-install.sh && ./server-install.sh"

# Очистка временных файлов
rm -rf deploy-temp

echo "✅ Deployment completed successfully!"
echo "🌐 Your PWA should be available at: http://$SERVER_HOST"