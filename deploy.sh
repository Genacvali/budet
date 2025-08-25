#!/bin/bash
set -e

echo "=== Budget PWA Deployment Script ==="
echo

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Проверяем что мы в корне проекта
if [[ ! -f "backend/main.go" || ! -f "frontend/package.json" ]]; then
    error "Run this script from project root (should contain backend/ and frontend/)"
fi

info "Step 1: Creating target directories"
sudo mkdir -p /opt/budget-pwa/backend/data
sudo mkdir -p /opt/budget-pwa/frontend

info "Step 2: Building backend"
cd backend
if ! command -v go &> /dev/null; then
    error "Go is not installed. Install Go 1.22+"
fi

CGO_ENABLED=1 go build -o budget-api || error "Backend build failed"
info "Backend binary built successfully"

info "Step 3: Installing backend"
sudo cp budget-api /opt/budget-pwa/backend/
sudo cp -r db /opt/budget-pwa/backend/   # для migrate.sql
sudo chown -R root:root /opt/budget-pwa/backend/

info "Step 4: Creating systemd service"
JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || echo "budget-pwa-$(date +%s)-secret")

sudo tee /etc/systemd/system/budget-api.service >/dev/null <<EOF
[Unit]
Description=Budget API (Go)
After=network.target

[Service]
WorkingDirectory=/opt/budget-pwa/backend
ExecStart=/opt/budget-pwa/backend/budget-api
Environment=DB_PATH=/opt/budget-pwa/backend/data/budget.db
Environment=JWT_SECRET=$JWT_SECRET
Restart=on-failure
RestartSec=2
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable budget-api

info "Step 5: Building frontend"
cd ../frontend
if ! command -v npm &> /dev/null; then
    error "npm is not installed. Install Node.js 18+"
fi

npm ci || error "npm install failed"
npm run build || error "Frontend build failed"
info "Frontend built successfully"

info "Step 6: Installing frontend"
sudo rsync -a --delete build/ /opt/budget-pwa/frontend/
sudo chown -R nginx:nginx /opt/budget-pwa/frontend/ 2>/dev/null || true

info "Step 7: Installing Nginx"
if ! command -v nginx &> /dev/null; then
    sudo dnf install -y nginx || error "Nginx installation failed"
fi
sudo systemctl enable nginx

info "Step 8: Creating Nginx config"
sudo tee /etc/nginx/conf.d/budget.conf >/dev/null <<'EOF'
proxy_http_version 1.1;
proxy_read_timeout 30s;
proxy_connect_timeout 5s;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;

gzip on;
gzip_types text/plain text/css application/json application/javascript application/xml image/svg+xml;
gzip_min_length 1024;

server {
    listen 80;
    server_name _;

    root /opt/budget-pwa/frontend;
    index index.html;

    location = /service-worker.js { add_header Cache-Control "no-cache"; try_files $uri =404; }
    location = /manifest.webmanifest { add_header Cache-Control "no-cache"; try_files $uri =404; }

    location ~* \.(?:js|css|woff2?|ttf|eot|ico|png|jpg|jpeg|svg)$ {
        try_files $uri =404;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8080$request_uri;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
}
EOF

# Проверяем конфиг nginx
sudo nginx -t || error "Nginx config test failed"

info "Step 9: Configuring SELinux and Firewall"
# SELinux: разрешить nginx подключаться к backend
if command -v setsebool &> /dev/null; then
    sudo setsebool -P httpd_can_network_connect 1 || warn "Failed to set SELinux policy"
fi

# Firewall: открыть HTTP/HTTPS
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-service=http >/dev/null 2>&1 || warn "Failed to open HTTP port"
    sudo firewall-cmd --permanent --add-service=https >/dev/null 2>&1 || warn "Failed to open HTTPS port"
    sudo firewall-cmd --reload >/dev/null 2>&1 || warn "Failed to reload firewall"
fi

info "Step 10: Starting services"
sudo systemctl start budget-api || error "Failed to start budget-api"
sudo systemctl start nginx || error "Failed to start nginx"

info "Step 11: Service status"
sudo systemctl status budget-api --no-pager --lines=3
sudo systemctl status nginx --no-pager --lines=3

info "Step 12: Running smoke tests"
sleep 3

# Тест API напрямую
if curl -s http://127.0.0.1:8080/api/auth/me >/dev/null 2>&1; then
    info "✅ Backend API responding"
else
    warn "⚠️  Backend API not responding"
fi

# Тест через Nginx
if curl -s http://localhost/ >/dev/null 2>&1; then
    info "✅ Frontend accessible via Nginx"
else
    warn "⚠️  Frontend not accessible"
fi

# Тест API через Nginx
if curl -s http://localhost/api/auth/me >/dev/null 2>&1; then
    info "✅ API proxy working"
else
    warn "⚠️  API proxy not working"
fi

echo
info "=== Deployment Complete! ==="
info "Access your app at: http://$(hostname -I | awk '{print $1}')/"
info "JWT Secret: $JWT_SECRET"
echo
info "To update:"
info "  Backend: ./update-backend.sh"  
info "  Frontend: ./update-frontend.sh"
info "  Logs: journalctl -u budget-api -f"
echo