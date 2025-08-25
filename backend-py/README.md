# Budget PWA Backend

FastAPI-based backend for the Budget PWA application.

## Features

- 🔐 JWT Authentication
- 📊 Categories and Transactions management
- 🔄 Offline-first sync with conflict resolution
- 📱 PWA-optimized API
- 🗄️ SQLite with WAL mode
- 🚀 FastAPI with async support
- 📝 Auto-generated API documentation

## Quick Start

### Development

1. **Setup virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run development server:**
   ```bash
   python run.py
   # or
   uvicorn app.main:app --reload
   ```

5. **Access API:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/health

### Production Deployment

Use the automated deployment script from the project root:

```bash
./deploy-python.sh
```

This will:
- Set up Python environment
- Install dependencies
- Build frontend
- Deploy to `/opt/budget-pwa/`
- Configure systemd service
- Setup Nginx integration

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh token

### Categories
- `GET /api/categories/` - List categories
- `POST /api/categories/` - Create category
- `GET /api/categories/{id}` - Get category
- `PUT /api/categories/{id}` - Update category
- `DELETE /api/categories/{id}` - Delete category

### Transactions
- `GET /api/transactions/` - List transactions (with filters)
- `POST /api/transactions/` - Create transaction
- `GET /api/transactions/{id}` - Get transaction
- `PUT /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction
- `GET /api/transactions/stats/summary` - Get statistics

### Sync
- `POST /api/sync/` - Sync data with conflict resolution
- `GET /api/sync/status` - Get sync status

### System
- `GET /api/health` - Health check
- `GET /` - API info

## Configuration

Environment variables (`.env` file):

```env
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
JWT_SECRET=your-super-secret-key
DATABASE_URL=budget.db
CORS_ORIGINS=http://localhost,https://your-domain.com
LOG_LEVEL=INFO
```

## Database Schema

The application uses SQLite with the following tables:

- **users** - User accounts with email/password
- **categories** - Income/expense categories with colors and icons
- **transactions** - Financial transactions linked to categories

All tables include:
- Auto-incrementing IDs
- Created/updated timestamps
- Foreign key relationships
- Unique constraints for data integrity

## Sync System

The backend implements a Last-Writer-Wins (LWW) conflict resolution system:

1. Client sends local changes with timestamps
2. Server compares with stored versions
3. Conflicts resolved using latest timestamp
4. Server returns unified dataset
5. Client updates local database

## Security

- JWT tokens for authentication
- Password hashing with bcrypt
- CORS protection
- SQL injection prevention with parameterized queries
- Input validation with Pydantic models

## Development

### Testing

```bash
# Run tests (when available)
pytest

# Manual API testing
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

### Code Style

```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
```

## Service Management

### Systemd Commands

```bash
# Start service
sudo systemctl start budget-api

# Stop service
sudo systemctl stop budget-api

# Restart service
sudo systemctl restart budget-api

# Check status
sudo systemctl status budget-api

# View logs
journalctl -u budget-api -f
```

### Database Management

```bash
# Database location
/opt/budget-pwa/backend/budget.db

# Backup database
cp /opt/budget-pwa/backend/budget.db /backup/budget-$(date +%Y%m%d).db

# View database
sqlite3 /opt/budget-pwa/backend/budget.db
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   - Check logs: `journalctl -u budget-api -f`
   - Verify permissions: `ls -la /opt/budget-pwa/backend/`
   - Check Python environment: `sudo -u budget-pwa /opt/budget-pwa/backend/venv/bin/python --version`

2. **Database errors**
   - Ensure SQLite file exists and is writable
   - Check database permissions
   - Review migration logs

3. **Authentication issues**
   - Verify JWT_SECRET is set
   - Check token expiration
   - Ensure CORS is configured correctly

### Performance Tuning

- Enable SQLite WAL mode (done automatically)
- Add database indexes for frequent queries
- Use connection pooling for high load
- Monitor memory usage and add limits

## License

MIT License - see project root for details.