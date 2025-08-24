#!/bin/bash
set -e

# SSL Setup with Let's Encrypt for Budget App
# Run after deploy.sh and when you have a domain pointed to your server

echo "🔒 Setting up HTTPS with Let's Encrypt..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root (sudo ./ssl-setup.sh)${NC}"
    exit 1
fi

# Get domain name
read -p "Enter your domain name (e.g., budget.example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ Domain name is required${NC}"
    exit 1
fi

read -p "Enter your email for Let's Encrypt notifications: " EMAIL
if [ -z "$EMAIL" ]; then
    echo -e "${RED}❌ Email is required${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Installing Certbot...${NC}"
apt update
apt install -y snapd
snap install core; snap refresh core
snap install --classic certbot
ln -sf /snap/bin/certbot /usr/bin/certbot

echo -e "${YELLOW}🔒 Obtaining SSL certificate...${NC}"
certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive

# Update nginx config for your domain
cat > /etc/nginx/sites-available/budget << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Static files
    location /static/ {
        alias /root/budget-app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Main app proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/api/health;
    }
}
EOF

nginx -t && systemctl reload nginx

# Set up auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

echo -e "${GREEN}🎉 HTTPS setup completed!${NC}"
echo ""
echo -e "${YELLOW}📋 Your app is now available at:${NC}"
echo "https://$DOMAIN"
echo ""
echo -e "${YELLOW}📊 Certificate will auto-renew every 12 hours at noon${NC}"
echo "Check renewal: certbot certificates"