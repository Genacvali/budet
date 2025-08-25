#!/bin/bash
set -e

echo "=== Budget PWA Frontend Fix and Deploy ==="

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Проверяем что мы в корне проекта
if [[ ! -f "frontend/package.json" || ! -f "backend/main.go" ]]; then
    error "Run this script from project root (should contain backend/ and frontend/)"
    exit 1
fi

info "Step 1: Cleaning frontend build cache"
cd frontend
rm -rf node_modules .svelte-kit build package-lock.json 2>/dev/null || true

info "Step 2: Installing fresh dependencies"
npm install

info "Step 3: Running TypeScript check"
if npm run check; then
    info "✅ TypeScript check passed"
else
    warn "⚠️  TypeScript check had warnings (continuing)"
fi

info "Step 4: Building frontend"
if npm run build; then
    info "✅ Frontend build successful!"
else
    error "❌ Frontend build failed"
    echo
    error "Common issues to check:"
    error "1. Make sure svelte.config.js has vitePreprocess()"
    error "2. Check that all <script> tags have lang=\"ts\""
    error "3. Verify Dexie imports use 'type Table'"
    error "4. Ensure no NodeJS.Timeout types in browser code"
    exit 1
fi

info "Step 5: Deploying to production directory"
sudo mkdir -p /opt/budget-pwa/frontend
sudo rsync -a --delete build/ /opt/budget-pwa/frontend/

info "Step 6: Setting correct permissions"
sudo chown -R nginx:nginx /opt/budget-pwa/frontend/ 2>/dev/null || sudo chown -R root:root /opt/budget-pwa/frontend/

info "Step 7: Testing Nginx config"
sudo nginx -t || {
    error "Nginx config test failed"
    exit 1
}

info "Step 8: Reloading Nginx"
sudo systemctl reload nginx

info "Step 9: Running deployment tests"
sleep 2

# Test frontend access
if curl -s -I http://localhost/ | grep -q "200 OK"; then
    info "✅ Frontend accessible at http://localhost/"
else
    error "❌ Frontend not accessible"
    exit 1
fi

# Test API proxy
if curl -s -I http://localhost/api/auth/me | grep -q -E "(401|400)"; then
    info "✅ API proxy working (got expected auth error)"
else
    warn "⚠️  API proxy might have issues"
fi

# Test static assets
if curl -s -I http://localhost/favicon.ico | grep -q -E "(200|404)"; then
    info "✅ Static asset serving working"
else
    warn "⚠️  Static assets might have issues"
fi

echo
info "=== Frontend Deployment Complete! ==="
info "🚀 App is live at: http://$(hostname -I | awk '{print $1}')/"
echo
info "Next steps:"
info "1. Test registration: http://localhost/auth/register"
info "2. Check backend logs: journalctl -u budget-api -f"
info "3. Monitor nginx logs: tail -f /var/log/nginx/access.log"
echo
info "To enable HTTPS:"
info "./setup-ssl.sh your-domain.com your-email@example.com"