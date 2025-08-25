#!/bin/bash
set -e

echo "=== Budget PWA Python Backend Deployment ==="

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Check if we're in project root
if [[ ! -f "backend-py/pyproject.toml" || ! -f "frontend/package.json" ]]; then
    error "Run this script from project root (should contain backend-py/ and frontend/)"
    exit 1
fi

info "Step 1: Setting up Python backend environment"
cd backend-py

# Check Python version
PYTHON_VERSION=$(python3 --version 2>/dev/null || echo "not found")
info "Python version: $PYTHON_VERSION"

if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install dependencies
info "Installing Python dependencies..."
pip install --upgrade pip
pip install -e .

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    info "Creating .env file from template..."
    cp .env.example .env
    warn "⚠️  Please edit .env file with your actual configuration!"
    warn "⚠️  Especially change JWT_SECRET to a secure random string!"
fi

info "Step 2: Testing Python backend"
# Test database initialization
info "Testing database connection..."
python3 -c "
import asyncio
from app.db import init_db, get_db

async def test_db():
    await init_db()
    db = await get_db()
    cursor = await db.execute('SELECT 1')
    result = await cursor.fetchone()
    print('✅ Database test passed')

asyncio.run(test_db())
"

# Test FastAPI app startup
info "Testing FastAPI application startup..."
timeout 10s python3 -c "
import uvicorn
from app.main import app
import sys
import os

# Test import
try:
    from app.main import app
    print('✅ FastAPI app imports successfully')
except Exception as e:
    print(f'❌ FastAPI app import failed: {e}')
    sys.exit(1)
" || {
    error "FastAPI application test failed"
    exit 1
}

cd ..

info "Step 3: Building frontend"
cd frontend

# Clean build
rm -rf node_modules .svelte-kit build package-lock.json 2>/dev/null || true

# Install dependencies
info "Installing frontend dependencies..."
npm install

# Run TypeScript check
info "Running TypeScript check..."
if npm run check; then
    info "✅ TypeScript check passed"
else
    warn "⚠️  TypeScript check had warnings (continuing)"
fi

# Build frontend
info "Building frontend..."
if npm run build; then
    info "✅ Frontend build successful!"
else
    error "❌ Frontend build failed"
    exit 1
fi

cd ..

info "Step 4: Deploying to production directories"

# Create production directories
sudo mkdir -p /opt/budget-pwa/frontend
sudo mkdir -p /opt/budget-pwa/backend
sudo mkdir -p /var/log/budget-pwa

# Deploy frontend
info "Deploying frontend..."
sudo rsync -a --delete frontend/build/ /opt/budget-pwa/frontend/

# Deploy backend
info "Deploying backend..."
sudo rsync -a --delete backend-py/ /opt/budget-pwa/backend/
sudo chown -R budget-pwa:budget-pwa /opt/budget-pwa/backend/ 2>/dev/null || sudo chown -R root:root /opt/budget-pwa/backend/

# Set permissions
info "Setting permissions..."
sudo chown -R nginx:nginx /opt/budget-pwa/frontend/ 2>/dev/null || sudo chown -R root:root /opt/budget-pwa/frontend/
sudo chmod -R 755 /opt/budget-pwa/
sudo chmod 644 /opt/budget-pwa/backend/.env 2>/dev/null || true

info "Step 5: Creating systemd service"

# Create systemd service file
sudo tee /etc/systemd/system/budget-api.service > /dev/null << 'EOF'
[Unit]
Description=Budget PWA API Server
After=network.target

[Service]
Type=exec
User=budget-pwa
Group=budget-pwa
WorkingDirectory=/opt/budget-pwa/backend
Environment=PATH=/opt/budget-pwa/backend/venv/bin
ExecStart=/opt/budget-pwa/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=budget-api

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/budget-pwa/backend
ReadWritePaths=/var/log/budget-pwa

[Install]
WantedBy=multi-user.target
EOF

# Create user for service if it doesn't exist
if ! id "budget-pwa" &>/dev/null; then
    info "Creating budget-pwa system user..."
    sudo useradd --system --home /opt/budget-pwa --shell /bin/false budget-pwa
fi

# Setup Python environment in production directory
info "Setting up production Python environment..."
cd /opt/budget-pwa/backend
if [[ ! -d "venv" ]]; then
    sudo -u budget-pwa python3 -m venv venv 2>/dev/null || {
        sudo python3 -m venv venv
        sudo chown -R budget-pwa:budget-pwa venv
    }
fi

sudo -u budget-pwa ./venv/bin/pip install --upgrade pip 2>/dev/null || {
    sudo ./venv/bin/pip install --upgrade pip
    sudo chown -R budget-pwa:budget-pwa venv
}

sudo -u budget-pwa ./venv/bin/pip install -e . 2>/dev/null || {
    sudo ./venv/bin/pip install -e .
    sudo chown -R budget-pwa:budget-pwa venv
}

cd - > /dev/null

# Reload systemd and start service
info "Starting Budget API service..."
sudo systemctl daemon-reload
sudo systemctl enable budget-api
sudo systemctl restart budget-api

# Wait for service to start
sleep 3

# Check service status
if sudo systemctl is-active --quiet budget-api; then
    info "✅ Budget API service is running"
else
    error "❌ Budget API service failed to start"
    warn "Check logs with: journalctl -u budget-api -f"
    exit 1
fi

info "Step 6: Testing Nginx configuration"
sudo nginx -t || {
    error "Nginx configuration test failed"
    exit 1
}

info "Step 7: Reloading Nginx"
sudo systemctl reload nginx

info "Step 8: Running deployment tests"
sleep 2

# Test frontend access
if curl -s -I http://localhost/ | grep -q "200 OK"; then
    info "✅ Frontend accessible at http://localhost/"
else
    error "❌ Frontend not accessible"
    exit 1
fi

# Test backend API
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    info "✅ Backend API healthy at http://localhost:8000/"
else
    warn "⚠️  Backend API might have issues"
fi

# Test API proxy through Nginx
if curl -s -I http://localhost/api/health | grep -q "200 OK"; then
    info "✅ API proxy working"
else
    warn "⚠️  API proxy might have issues"
fi

echo
info "=== Python Backend Deployment Complete! ==="
info "🚀 Frontend: http://$(hostname -I | awk '{print $1}')/"
info "🚀 Backend API: http://$(hostname -I | awk '{print $1}'):8000/"
echo
info "Service management:"
info "• Check status: sudo systemctl status budget-api"
info "• View logs: journalctl -u budget-api -f"
info "• Restart: sudo systemctl restart budget-api"
echo
info "Database location: /opt/budget-pwa/backend/budget.db"
info "Configuration: /opt/budget-pwa/backend/.env"
echo
info "To test the API:"
info "curl http://localhost:8000/api/health"
echo
warn "⚠️  Remember to:"
warn "1. Set a secure JWT_SECRET in /opt/budget-pwa/backend/.env"
warn "2. Configure CORS_ORIGINS for your domain"
warn "3. Set up HTTPS with: ./setup-ssl.sh your-domain.com"