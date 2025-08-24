#!/bin/bash

echo "🔍 Checking available Certbot packages..."

# Check system info
echo "📋 System Information:"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "OS: $NAME"
    echo "Version: $VERSION"
    echo "ID: $ID"
    echo "Version ID: $VERSION_ID"
fi
echo ""

echo "📦 Available Certbot packages:"
if command -v dnf >/dev/null 2>&1; then
    echo "Using dnf..."
    dnf search certbot 2>/dev/null | grep -E "^(certbot|python.*certbot)" || echo "No certbot packages found with dnf search"
    echo ""
    
    echo "🔍 Trying specific package names:"
    for pkg in certbot python3-certbot-nginx certbot-nginx python2-certbot-nginx; do
        if dnf list "$pkg" >/dev/null 2>&1; then
            echo "✅ $pkg - Available"
        else
            echo "❌ $pkg - Not found"
        fi
    done
    
elif command -v yum >/dev/null 2>&1; then
    echo "Using yum..."
    yum search certbot 2>/dev/null | grep -E "^(certbot|python.*certbot)" || echo "No certbot packages found with yum search"
    echo ""
    
    echo "🔍 Trying specific package names:"
    for pkg in certbot python3-certbot-nginx certbot-nginx python2-certbot-nginx; do
        if yum list "$pkg" >/dev/null 2>&1; then
            echo "✅ $pkg - Available"
        else
            echo "❌ $pkg - Not found"
        fi
    done
    
elif command -v apt >/dev/null 2>&1; then
    echo "Using apt..."
    apt search certbot 2>/dev/null | grep -E "^(certbot|python.*certbot)" || echo "No certbot packages found with apt search"
fi

echo ""
echo "💡 Recommendation:"
echo "If no nginx plugin is available, you can:"
echo "1. Use 'certbot certonly --standalone' method"  
echo "2. Use the main ssl-setup.sh (with snap) instead"
echo "3. Install certificates manually"