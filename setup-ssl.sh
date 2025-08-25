#!/bin/bash
set -e

echo "=== Setting up HTTPS with Let's Encrypt ==="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 budget.example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

info "Installing certbot"
sudo dnf install -y epel-release
sudo dnf install -y certbot python3-certbot-nginx

info "Updating nginx config for domain: $DOMAIN"
sudo sed -i "s/server_name _;/server_name $DOMAIN;/" /etc/nginx/conf.d/budget.conf
sudo nginx -t
sudo systemctl reload nginx

info "Obtaining SSL certificate"
sudo certbot --nginx -d "$DOMAIN" -m "$EMAIL" --agree-tos --redirect -n

info "Testing SSL renewal"
sudo certbot renew --dry-run

info "HTTPS setup complete!"
info "Your app is now available at: https://$DOMAIN/"