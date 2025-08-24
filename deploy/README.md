# Production Deployment Guide

Complete production setup for Budget App on DigitalOcean or any Ubuntu/Debian VPS.

## 📋 Prerequisites

- Ubuntu 20.04+ or Debian 11+ VPS
- Root access or sudo privileges  
- Domain name pointed to server (optional, for HTTPS)
- Firewall allowing HTTP (80) and HTTPS (443) traffic

## 🚀 Quick Deployment (Recommended)

1. **Upload files to server**:
```bash
# From local machine
scp -r . root@your-server-ip:/root/budget-app/
```

2. **Run automated deployment**:
```bash
# On server
ssh root@your-server-ip
cd /root/budget-app
./deploy/deploy.sh
```

3. **Access your app**: `http://your-server-ip`

## 🔒 HTTPS Setup (Optional)

If you have a domain name:

```bash
./deploy/ssl-setup.sh
# Enter your domain and email when prompted
```

Your app will be available at `https://your-domain.com`

## 📊 Monitoring

The deployment automatically sets up:

- **Health monitoring**: Checks every 5 minutes, auto-restarts if needed
- **Log rotation**: Application and access logs in `/var/log/budget/`
- **Automatic restart**: If memory usage exceeds 500MB or service fails

## 🛠️ Manual Commands

```bash
# Check service status
sudo systemctl status budget.service

# View live logs
sudo journalctl -u budget.service -f

# Restart application
sudo systemctl restart budget.service

# Check health
curl http://localhost/health

# Update and restart
git pull
sudo systemctl restart budget.service
```

## 📁 File Structure After Deployment

```
/root/budget-app/
├── app.py              # Flask application
├── services.py         # CSV parsing utilities
├── templates/          # HTML templates
├── static/            # CSS, JS files
├── budget.db          # SQLite database
├── .env               # Environment config
└── deploy/
    ├── deploy.sh       # Main deployment script
    ├── ssl-setup.sh    # HTTPS setup
    ├── health-monitor.sh # Health monitoring
    ├── budget.service   # Systemd service
    └── nginx-budget.conf # Nginx config
```

## 🔧 Configuration Files

### Systemd Service
- **Location**: `/etc/systemd/system/budget.service`
- **Workers**: 2 Gunicorn workers with 2 threads each
- **Bind**: `127.0.0.1:8000` (local only)
- **Auto-restart**: Yes, with 5-second delay

### Nginx Configuration  
- **Location**: `/etc/nginx/sites-available/budget`
- **Port**: 80 (HTTP), 443 (HTTPS if SSL enabled)
- **Proxy**: Forwards to `127.0.0.1:8000`
- **Static files**: Served directly by Nginx
- **Security headers**: Enabled (XSS, HSTS, etc.)

### Health Monitor
- **Location**: `/root/budget-app/deploy/health-monitor.sh`
- **Schedule**: Every 5 minutes (cron)
- **Checks**: Service status, HTTP health endpoint, memory usage
- **Actions**: Auto-restart on failure or high memory usage

## 📈 Performance Tuning

For higher traffic, edit `/etc/systemd/system/budget.service`:

```ini
# Increase workers for more concurrent users
ExecStart=/root/budget-app/.venv/bin/gunicorn \
    --workers 4 \
    --threads 4 \
    # ... other options
```

## 🔐 Security Considerations

- Application runs on `127.0.0.1:8000` (not exposed externally)
- Nginx handles public traffic on port 80/443
- Security headers enabled (HSTS, XSS protection, etc.)
- SQLite database in WAL mode for concurrent access
- Regular health monitoring and auto-restart

## 🆘 Troubleshooting

**Service won't start**:
```bash
sudo journalctl -u budget.service --no-pager -n 20
```

**Nginx issues**:
```bash
sudo nginx -t  # Test config
sudo systemctl status nginx
```

**Database locked**:
```bash
# Check WAL mode
sqlite3 /root/budget-app/budget.db "PRAGMA journal_mode;"
```

**High memory usage**:
- Health monitor will auto-restart at >500MB
- Adjust limit in `/root/budget-app/deploy/health-monitor.sh`

## 📝 Logs

- **Application**: `/var/log/budget/access.log`, `/var/log/budget/error.log`
- **Health Monitor**: `/var/log/budget/health-monitor.log`
- **System Service**: `sudo journalctl -u budget.service`
- **Nginx**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`