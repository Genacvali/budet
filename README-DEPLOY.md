# Budget PWA - Деплой на CentOS 9

## Быстрый старт

### 1. Подготовка переменных окружения

```bash
# Установите переменные для вашего сервера
export SERVER_USER="root"
export SERVER_HOST="your-server-ip"
```

### 2. Первоначальный деплой

```bash
# Убедитесь что TailwindCSS настроен (уже сделано)
cd frontend
npm install
cd ..

# Деплой на сервер
chmod +x deploy-to-server.sh
./deploy-to-server.sh
```

### 3. Обновления

```bash
# Быстрое обновление фронтенда
chmod +x update-server.sh
./update-server.sh
```

## Что происходит при деплое

### Фронтенд (PWA)
- ✅ **TailwindCSS настроен** - работает без CDN
- ✅ **Service Worker без внешних зависимостей** - никаких запросов к Google CDN
- ✅ **Static adapter** - генерирует статичные файлы для nginx
- ✅ **PWA манифест** - приложение устанавливается как нативное

### Бэкенд (Python FastAPI)
- 🐍 **FastAPI с uvicorn** - быстрый ASGI сервер
- 🔒 **Безопасный systemd service** - изолированный пользователь
- 📝 **SQLite база** - в `/opt/budget-pwa/backend/data/`
- 🔄 **Auto-restart** - перезапуск при падении

### Nginx
- 🌐 **Проксирование API** - `/api/*` → FastAPI
- 📦 **Статика фронтенда** - оптимизированное кэширование
- 🚀 **Gzip сжатие** - быстрая загрузка
- 🔒 **Безопасность** - скрытие версий, блокировка служебных файлов

## Структура на сервере

```
/opt/budget-pwa/
├── frontend/           # Собранный Svelte + TailwindCSS
│   ├── index.html
│   ├── service-worker.js
│   ├── manifest.webmanifest
│   └── _app/
├── backend/            # Python FastAPI
│   ├── app/
│   ├── venv/
│   ├── requirements.txt
│   └── data/           # SQLite база
└── logs/
```

## Полезные команды на сервере

```bash
# Статус сервисов
sudo systemctl status budget-api nginx

# Логи приложения
sudo journalctl -u budget-api -f
sudo tail -f /var/log/nginx/budget_*.log

# Перезапуск
sudo systemctl restart budget-api
sudo systemctl reload nginx

# Обновление backend
cd /opt/budget-pwa/backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart budget-api
```

## Безопасность и производительность

### ✅ Офлайн-первое приложение:
- Service Worker кэширует всё локально
- Никаких внешних CDN или API
- Работает без интернета после первой загрузки

### ✅ Защита от DDoS:
- Все статические ресурсы кэшируются nginx
- API проксируется через nginx с лимитами
- FastAPI работает только локально (127.0.0.1)

### ✅ Быстродействие:
- Gzip сжатие
- Долгое кэширование статики
- Service Worker для мгновенной загрузки

## Устранение неполадок

### TailwindCSS не работает
```bash
# Проверьте что PostCSS работает
cd frontend
npm run build
# Должны появиться .tailwind классы в build/_app/
```

### Service Worker ошибки
```bash
# Проверьте в DevTools → Application → Service Workers
# Не должно быть запросов к storage.googleapis.com
```

### API недоступен
```bash
# На сервере:
sudo systemctl status budget-api
sudo journalctl -u budget-api --no-pager
```

## Мониторинг

После деплоя проверьте:
- `http://ваш-сервер` - PWA загружается
- `http://ваш-сервер/api/health` - API работает  
- DevTools → Lighthouse → PWA score > 90
- DevTools → Network → Offline mode - работает