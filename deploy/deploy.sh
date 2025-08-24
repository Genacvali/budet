#!/bin/bash
set -e

echo "🚀 Deploying Budget App to production..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/root/budget-app"
DEPLOY_DIR="$(dirname "$(realpath "$0")")"
LOG_DIR="/var/log/budget"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root (sudo ./deploy.sh)${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Installing system dependencies...${NC}"
apt update
apt install -y nginx python3-venv python3-pip

echo -e "${YELLOW}📁 Setting up directories...${NC}"
mkdir -p "$LOG_DIR"
mkdir -p "$APP_DIR"

echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
cd "$APP_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${YELLOW}⚙️  Setting up systemd service...${NC}"
cp "$DEPLOY_DIR/budget.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable budget.service

echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"
# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Install our config
cp "$DEPLOY_DIR/nginx-budget.conf" /etc/nginx/sites-available/budget
ln -sf /etc/nginx/sites-available/budget /etc/nginx/sites-enabled/budget

# Test nginx config
nginx -t

echo -e "${YELLOW}🔧 Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}📝 Created .env file - please edit it if needed${NC}"
fi

echo -e "${YELLOW}🗄️  Initializing database...${NC}"
python app.py &
sleep 2
pkill -f "python app.py" || true

echo -e "${YELLOW}🚀 Starting services...${NC}"
systemctl start budget.service
systemctl reload nginx

echo -e "${YELLOW}📊 Service status:${NC}"
systemctl is-active budget.service && echo -e "${GREEN}✅ Budget service: running${NC}" || echo -e "${RED}❌ Budget service: failed${NC}"
systemctl is-active nginx && echo -e "${GREEN}✅ Nginx: running${NC}" || echo -e "${RED}❌ Nginx: failed${NC}"

# Test the app
echo -e "${YELLOW}🧪 Testing application...${NC}"
sleep 2
if curl -s http://localhost/ > /dev/null; then
    echo -e "${GREEN}✅ Application is responding on http://localhost/${NC}"
else
    echo -e "${RED}❌ Application test failed${NC}"
    echo -e "${YELLOW}📋 Checking logs:${NC}"
    journalctl -u budget.service --no-pager -n 10
fi

echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Open http://$(curl -s http://checkip.amazonaws.com)/ in browser"
echo "2. Check logs: journalctl -u budget.service -f"
echo "3. For HTTPS setup, edit nginx config and run certbot"
echo ""
echo -e "${YELLOW}📊 Useful commands:${NC}"
echo "sudo systemctl status budget.service    # Check service status"
echo "sudo systemctl restart budget.service   # Restart app"
echo "sudo journalctl -u budget.service -f    # View live logs"
echo "sudo nginx -t && sudo systemctl reload nginx  # Reload nginx config"