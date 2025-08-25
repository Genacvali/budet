#!/bin/bash
set -e

echo "=== Updating Budget PWA Backend ==="

GREEN='\033[0;32m'
NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }

if [[ ! -f "backend/main.go" ]]; then
    echo "Error: Run from project root"
    exit 1
fi

info "Building new backend binary"
cd backend
CGO_ENABLED=1 go build -o budget-api

info "Stopping service"
sudo systemctl stop budget-api

info "Installing new binary"
sudo cp budget-api /opt/budget-pwa/backend/
sudo cp -r db /opt/budget-pwa/backend/  # обновить migrate.sql если изменился

info "Starting service"
sudo systemctl start budget-api

info "Checking status"
sudo systemctl status budget-api --no-pager --lines=5

info "Backend update complete"