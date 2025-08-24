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
```bash
# Install dependencies on Ubuntu/Debian
sudo apt update && sudo apt install -y python3-venv

# Setup systemd service
sudo systemctl enable --now budget.service

# Web server (choose one)
# Caddy (automatic HTTPS)
sudo apt install -y caddy
# Nginx (reverse proxy)
sudo apt install -y nginx
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