#!/bin/bash
set -e

echo "=== Fixing Frontend Build Issues ==="

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

cd frontend

info "Cleaning node_modules and reinstalling"
rm -rf node_modules package-lock.json .svelte-kit build
npm install

info "Running type check"
npm run check || true

info "Building frontend"
npm run build

if [[ $? -eq 0 ]]; then
    info "✅ Frontend build successful!"
    
    info "Deploying to production directory"
    sudo rsync -a --delete build/ /opt/budget-pwa/frontend/
    sudo chown -R nginx:nginx /opt/budget-pwa/frontend/ 2>/dev/null || true
    
    info "Reloading nginx"
    sudo nginx -t
    sudo systemctl reload nginx
    
    info "Testing deployment"
    if curl -s -I http://localhost/ | grep -q "200 OK"; then
        info "✅ Frontend deployment successful!"
    else
        error "❌ Frontend not accessible"
        exit 1
    fi
    
    echo
    info "🚀 Frontend is now live!"
    
else
    error "❌ Frontend build failed"
    exit 1
fi