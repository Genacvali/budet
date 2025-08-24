#!/bin/bash
set -e

# Quick HTTP-only deployment for Budget App
# Usage: ./quick-deploy.sh [user] [app_path]

USER=${1:-root}
APP_PATH=${2:-/data/budget-app}

echo "🚀 Quick HTTP deployment for user: $USER, path: $APP_PATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Run as root: sudo ./quick-deploy.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}1️⃣ Stopping conflicting services...${NC}"
systemctl stop caddy 2>/dev/null || true
systemctl disable caddy 2>/dev/null || true

echo -e "${YELLOW}2️⃣ Installing packages...${NC}"
if command -v apt >/dev/null; then
    apt update && apt install -y nginx python3-venv python3-pip curl
elif command -v dnf >/dev/null; then
    dnf install -y nginx python3 python3-pip curl
elif command -v yum >/dev/null; then
    yum install -y nginx python3 python3-pip curl
fi

echo -e "${YELLOW}3️⃣ Setting up Python environment...${NC}"
cd "$APP_PATH"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${YELLOW}4️⃣ Setting up systemd service...${NC}"
cat > /etc/systemd/system/budget.service << EOF
[Unit]
Description=Budget app (Flask)
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_PATH
Environment="PATH=$APP_PATH/.venv/bin"
ExecStart=$APP_PATH/.venv/bin/gunicorn -w 1 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable budget.service

echo -e "${YELLOW}5️⃣ Setting up Nginx...${NC}"
cat > /etc/nginx/sites-available/budget << 'EOF'
server {
    listen 80;
    server_name _;

    location /static/ {
        alias $APP_PATH/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
EOF

# Create sites-enabled if not exists (for CentOS)
mkdir -p /etc/nginx/sites-enabled

# Add include to nginx.conf if not present
if ! grep -q "sites-enabled" /etc/nginx/nginx.conf; then
    sed -i '/http {/a\    include /etc/nginx/sites-enabled/*;' /etc/nginx/nginx.conf
fi

ln -sf /etc/nginx/sites-available/budget /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo -e "${YELLOW}6️⃣ Setting up environment...${NC}"
if [ ! -f "$APP_PATH/.env" ]; then
    cp "$APP_PATH/.env.example" "$APP_PATH/.env" 2>/dev/null || true
fi

# Fix ownership
chown -R $USER:$USER "$APP_PATH"

echo -e "${YELLOW}7️⃣ Starting services...${NC}"
nginx -t
systemctl start budget.service
systemctl start nginx
systemctl enable nginx

echo -e "${YELLOW}8️⃣ Checking status...${NC}"
sleep 2

if systemctl is-active --quiet budget.service; then
    echo -e "${GREEN}✅ Budget service: running${NC}"
else
    echo -e "${RED}❌ Budget service: failed${NC}"
    journalctl -u budget.service --no-pager -n 5
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx: running${NC}"
else
    echo -e "${RED}❌ Nginx: failed${NC}"
fi

echo -e "${YELLOW}9️⃣ Testing application...${NC}"
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")

if curl -s http://127.0.0.1:8000 >/dev/null; then
    echo -e "${GREEN}✅ App responding on 127.0.0.1:8000${NC}"
else
    echo -e "${RED}❌ App not responding locally${NC}"
fi

if curl -s http://127.0.0.1/ >/dev/null; then
    echo -e "${GREEN}✅ Nginx proxy working${NC}"
else
    echo -e "${RED}❌ Nginx proxy failed${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo ""
echo -e "${YELLOW}📋 Access your app:${NC}"
echo "http://$PUBLIC_IP"
echo ""
echo -e "${YELLOW}📊 Useful commands:${NC}"
echo "sudo systemctl status budget.service"
echo "sudo journalctl -u budget.service -f"
echo "curl -I http://localhost/"
echo "sudo ss -tulpn | grep -E ':80|:8000'"
echo ""
echo -e "${YELLOW}⚠️  Don't forget to open port 80 in DigitalOcean Firewall!${NC}"