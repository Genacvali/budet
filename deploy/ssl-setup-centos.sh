#!/bin/bash
set -e

# SSL Setup with Let's Encrypt for CentOS/RHEL (without snap)
# Alternative to ssl-setup.sh for systems where snap is not available

echo "🔒 Setting up HTTPS with Let's Encrypt (CentOS/RHEL)..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root (sudo ./ssl-setup-centos.sh)${NC}"
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

echo -e "${YELLOW}📦 Installing Certbot via package manager...${NC}"

# Detect OS version to use correct package names
if [ -f /etc/os-release ]; then
    . /etc/os-release
    VERSION_ID=${VERSION_ID}
fi

# Install certbot using package manager instead of snap
if command -v yum >/dev/null 2>&1; then
    # CentOS/RHEL 7
    yum install -y epel-release
    if [[ "$VERSION_ID" =~ ^7 ]]; then
        yum install -y certbot python2-certbot-nginx
    else
        # CentOS 8+ or recent RHEL with yum
        yum install -y certbot python3-certbot-nginx
    fi
elif command -v dnf >/dev/null 2>&1; then
    # CentOS/RHEL 8+ or Fedora
    dnf install -y epel-release
    
    # Try different package name variants for different versions
    if dnf list python3-certbot-nginx >/dev/null 2>&1; then
        dnf install -y certbot python3-certbot-nginx
    elif dnf list certbot-nginx >/dev/null 2>&1; then
        dnf install -y certbot certbot-nginx  
    else
        echo -e "${YELLOW}⚠️  Standard nginx plugin not found, installing certbot only...${NC}"
        dnf install -y certbot
        echo -e "${YELLOW}📝 You'll need to configure nginx manually after getting certificate${NC}"
    fi
else
    echo -e "${RED}❌ Unsupported system for this script. Use ssl-setup.sh instead.${NC}"
    exit 1
fi

echo -e "${YELLOW}🔒 Obtaining SSL certificate...${NC}"

# First try with nginx plugin
if certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive 2>/dev/null; then
    echo -e "${GREEN}✅ Certificate obtained with nginx plugin${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx plugin failed, trying webroot method...${NC}"
    
    # Stop nginx temporarily for webroot
    systemctl stop nginx
    
    # Get certificate using standalone method
    if certbot certonly --standalone -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive; then
        echo -e "${GREEN}✅ Certificate obtained with standalone method${NC}"
        
        # Start nginx back
        systemctl start nginx
    else
        echo -e "${RED}❌ Failed to obtain certificate${NC}"
        systemctl start nginx
        exit 1
    fi
fi

# Update nginx config for your domain
cat > /etc/nginx/sites-available/budget << EOF
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
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

# Create sites-enabled directory if it doesn't exist (CentOS doesn't have it by default)
mkdir -p /etc/nginx/sites-enabled
# Add include to main nginx.conf if not present
if ! grep -q "sites-enabled" /etc/nginx/nginx.conf; then
    sed -i '/http {/a\    include /etc/nginx/sites-enabled/*;' /etc/nginx/nginx.conf
fi

ln -sf /etc/nginx/sites-available/budget /etc/nginx/sites-enabled/budget

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