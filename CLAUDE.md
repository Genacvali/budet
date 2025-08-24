# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Russian-language Flask-based budget tracking application that implements envelope budgeting methodology with automatic CSV import from Tinkoff Bank. The app supports income allocation across different sources (ЗП/Аванс/Декретные), automatic transaction categorization through rules and merchant mapping, and monthly budget tracking with carryover calculations.

## Architecture

This is a server-based Flask application with SQLite database:

- **Backend**: Flask with SQLite (WAL mode) for persistence
- **Frontend**: HTML templates with Pico CSS framework
- **CSV Processing**: Tinkoff bank statement parsing with automatic categorization
- **Deployment**: Gunicorn + systemd service, designed for VPS hosting

### Key Files Structure

- `app.py` - Main Flask application with all routes and business logic
- `services.py` - CSV parsing, text normalization, and rule processing utilities
- `requirements.txt` - Python dependencies (Flask, python-dotenv, gunicorn)
- `.env.example` - Environment configuration template
- `templates/` - Jinja2 HTML templates (base, index, merchants, rules)
- `budget.db` - SQLite database (auto-created on first run)

### Database Schema

**Core Tables**:
- `categories` - Budget categories with source allocation and percent/fixed amounts
- `incomes` - Income entries by source and date
- `expenses` - Monthly expenses by category
- `merchant_map` - Learned merchant-to-category mappings
- `rules` - Pattern-based categorization rules (keyword/regex)

**Sources**: Fixed list of income sources: "ЗП", "Аванс", "Декретные"

## Development Commands

**Local Development**:
```bash
# Setup
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run development server
python app.py  # http://localhost:8000
```

**Production Deployment**:

**Quick Deploy (Automated)**:
```bash
# Copy files to server
scp -r . root@your-server:/root/budget-app/

# Run deployment script
ssh root@your-server
cd /root/budget-app
./deploy/deploy.sh
```

**Manual Deployment**:
```bash
# Install dependencies
sudo apt update && sudo apt install -y nginx python3-venv

# Setup application
sudo cp deploy/budget.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now budget.service

# Setup Nginx
sudo cp deploy/nginx-budget.conf /etc/nginx/sites-available/budget
sudo ln -sf /etc/nginx/sites-available/budget /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Setup monitoring
sudo cp deploy/health-monitor.sh /root/budget-app/
echo "*/5 * * * * /root/budget-app/deploy/health-monitor.sh" | sudo crontab -
```

**HTTPS Setup (Optional)**:
```bash
./deploy/ssl-setup.sh
# Follow prompts to enter domain and email
```

## Key Features

### CSV Import Workflow
1. **Upload**: Tinkoff CSV file via `/import-csv` endpoint
2. **Parse**: Extract RUB expenses, normalize merchant descriptions
3. **Categorize**: Apply merchant mappings → rules → mark as "unknown"
4. **Learn**: Map unknown merchants to categories for future imports
5. **Store**: Create expense records for the target month

### Budget Calculations
- **Carryover**: `prev_income - prev_expenses` per source
- **Base**: `current_income + carryover - fixed_allocations` per source  
- **Plan**: `fixed_rub` OR `percent * base` per category
- **Remaining**: `plan - spent` per category

### Smart Categorization
1. **Merchant Map**: Exact normalized merchant name → category
2. **Rules**: Keyword/regex patterns → category (processed in reverse order)
3. **Manual**: Unmatched transactions for user assignment

## Data Flow

**Monthly Budget Process**:
1. Add income entries by source and date
2. Import bank CSV (creates expenses + unknown merchants)
3. Map unknown merchants to categories
4. Create rules for recurring patterns
5. View plan vs actual with carryover calculations

**File Processing**:
- CSV fields: "Сумма операции", "Описание", "MCC", "Дата операции"
- Filters: RUB currency, negative amounts (expenses only)
- Normalization: Unicode, lowercase, whitespace cleanup
- Merchant mapping: Stores normalized description → category_id

## API Endpoints

**Core Pages**:
- `GET /` - Main budget view with month selector
- `GET /import-csv` - CSV upload form
- `GET /rules` - Rule management interface
- `GET /export` - JSON export of all data

**CRUD Operations**:
- `POST /category/add|update` - Category management
- `POST /income/add` - Income entry creation
- `POST /minus/add` - Quick expense entry
- `POST /merchants/map` - Merchant categorization
- `POST /rules/add` - Pattern rule creation

## Technical Considerations

### Performance
- SQLite WAL mode for concurrent access
- Single-table queries with proper indexing
- Efficient text normalization and pattern matching

### Data Integrity
- Foreign key constraints with CASCADE deletion
- Input validation and sanitization
- Atomic transactions for import operations

### Deployment
- Minimal resource requirements (1 CPU, 1GB RAM sufficient)
- Systemd service management
- Daily database backup recommended: `cp budget.db backup/budget-$(date +%F).db`

## Monitoring & Maintenance

**Service Management**:
```bash
# Check service status
sudo systemctl status budget.service

# View logs
sudo journalctl -u budget.service -f

# Restart service
sudo systemctl restart budget.service

# Check health endpoint
curl http://localhost/health
```

**Monitoring Logs**:
```bash
# Application logs
tail -f /var/log/budget/access.log
tail -f /var/log/budget/error.log

# Health monitor logs  
tail -f /var/log/budget/health-monitor.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

**Backup & Restore**:
```bash
# Database backup
cp /root/budget-app/budget.db /root/backups/budget-$(date +%F).db

# Full backup via export endpoint
curl -o backup.json http://localhost/export

# Automated daily backup (add to crontab)
echo "0 2 * * * cp /root/budget-app/budget.db /root/backups/budget-\$(date +\%F).db" | crontab -e
```

## Performance & Security

**Resource Requirements**:
- **CPU**: 1 core sufficient for moderate usage
- **RAM**: 512MB minimum, 1GB recommended
- **Storage**: 100MB for app + database growth
- **Network**: Standard DigitalOcean 1GB/s sufficient

**Security Features**:
- Nginx security headers (HSTS, XSS protection, etc.)
- SQLite WAL mode for concurrent access
- Process isolation via systemd
- Health monitoring with auto-restart
- Log rotation and monitoring

## Common Development Tasks

**Adding New Rules**:
- Keywords: `taxi;яндекс;uber` → category
- Regex: `\btaxi\b|\byandex\b` → category

**CSV Import Testing**:
- Use sample Tinkoff export files
- Verify RUB filtering and amount parsing
- Test merchant normalization edge cases

**Database Migration**:
- Export via `/export` endpoint
- Import via `/import` endpoint (replaces all data)
- Manual SQL for schema changes

**Troubleshooting**:
```bash
# Check if ports are listening
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80

# Test internal communication
curl http://127.0.0.1:8000/api/health

# Check firewall (if enabled)
sudo ufw status

# Verify file permissions
ls -la /root/budget-app/
```