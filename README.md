# Budget PWA

Современное PWA-приложение для управления личным бюджетом с Go backend и SvelteKit frontend.

## Быстрый запуск

### Backend (Go API)

```bash
# Установка зависимостей
cd backend
go mod tidy

# Запуск сервера (порт 8080)
go run main.go
```

### Frontend (SvelteKit PWA)

```bash
# Установка зависимостей
cd frontend
npm install

# Запуск dev сервера (порт 5173)
npm run dev
```

## Архитектура

### Backend
- **Go + Chi router**: REST API
- **SQLite + WAL**: Локальная база данных
- **JWT**: Авторизация
- **CORS**: Поддержка PWA

### Frontend  
- **SvelteKit**: SSG/SPA фреймворк
- **Dexie.js**: Локальная IndexedDB
- **Tailwind CSS**: Стили
- **Service Worker**: Оффлайн режим

## API Endpoints

### Auth
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход  
- `GET /api/auth/me` - Профиль

### Entities (требует авторизации)
- `GET /api/entities/categories` - Категории
- `POST /api/entities/categories` - Создать/обновить категорию
- `GET /api/entities/operations` - Операции
- `POST /api/entities/operations` - Создать/обновить операцию

### Sync
- `GET /api/sync/pull?since=2024-01-01T00:00:00Z` - Загрузить изменения
- `POST /api/sync/push` - Отправить локальные данные

## Структура данных

### Categories
```json
{
  "id": "uuid",
  "name": "Продукты", 
  "kind": "expense",
  "icon": "🛒",
  "color": "#ef4444"
}
```

### Operations  
```json
{
  "id": "uuid",
  "type": "expense",
  "category_id": "uuid",
  "amount_cents": 150000,
  "date": "2024-01-15T10:30:00Z",
  "note": "Покупки в магазине"
}
```

## Разработка

### Добавление новой страницы
1. Создать файл в `frontend/src/routes/название/+page.svelte`
2. Добавить навигацию в `+layout.svelte`

### База данных
- Миграции в `backend/db/migrate.sql`
- Модели в `backend/internal/models.go`
- Dexie схема в `frontend/src/lib/db.ts`

## Production

### Backend
```bash
go build -o budget-api
./budget-api
```

### Frontend
```bash  
npm run build
# Статика в build/ для Nginx/Caddy
```

### Переменные окружения
- `DB_PATH` - путь к SQLite файлу (по умолчанию `./data/budget.db`)
- `JWT_SECRET` - секрет для подписи токенов

## Особенности

- ✅ PWA с оффлайн режимом
- ✅ Синхронизация между устройствами  
- ✅ Локальная база данных
- ✅ JWT авторизация
- ✅ Responsive дизайн
- ⏳ Background Sync через Service Worker
- ⏳ Push уведомления