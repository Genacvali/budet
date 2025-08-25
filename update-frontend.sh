#!/bin/bash
set -e

echo "=== Updating Budget PWA Frontend ==="

GREEN='\033[0;32m'
NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }

if [[ ! -f "frontend/package.json" ]]; then
    echo "Error: Run from project root"
    exit 1
fi

info "Building new frontend"
cd frontend
npm ci
npm run build

info "Installing new build"
sudo rsync -a --delete build/ /opt/budget-pwa/frontend/
sudo chown -R nginx:nginx /opt/budget-pwa/frontend/ 2>/dev/null || true

info "Reloading nginx"
sudo systemctl reload nginx

info "Frontend update complete"