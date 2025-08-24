# Миграция PWA на серверную архитектуру

Инструкция для Claude Code по переводу текущего PWA проекта на архитектуру клиент-сервер с Node.js + Express + SQLite.

## Цель
Перевести приложение с localStorage на централизованное хранение данных на сервере, сохранив весь существующий UI/UX.

## Структура проекта после миграции

```
budet/
├── client/              ← PWA фронтенд (переделанный)
│   ├── index.html
│   ├── manifest.json
│   ├── service-worker.js
│   └── icons/
└── server/              ← новый API сервер
    ├── package.json
    ├── index.js
    └── budget.db        ← SQLite база (создастся автоматически)
```

## Этап 1: Создание серверной части

### 1.1. Создать структуру папок
```bash
mkdir server
mkdir client
# Переместить все текущие файлы в client/
mv index.html manifest.json service-worker.js icons/ README.txt CLAUDE.md client/
```

### 1.2. Создать server/package.json
```json
{
  "name": "budget-server",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "node index.js",
    "dev": "node --watch index.js"
  },
  "dependencies": {
    "better-sqlite3": "^9.0.0",
    "cors": "^2.8.5",
    "express": "^4.18.2"
  }
}
```

### 1.3. Создать server/index.js
```javascript
import express from "express";
import cors from "cors";
import Database from "better-sqlite3";
import path from "path";

const app = express();
const PORT = process.env.PORT || 3000;

// Инициализация базы данных
const db = new Database("budget.db");

app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Создание таблиц
db.exec(`
  CREATE TABLE IF NOT EXISTS user_data (
    id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  
  INSERT OR IGNORE INTO user_data (id, data) VALUES (1, '{}');
`);

// Получить все данные пользователя
app.get("/api/data", (req, res) => {
  try {
    const row = db.prepare("SELECT data FROM user_data WHERE id = 1").get();
    const data = JSON.parse(row?.data || '{}');
    res.json(data);
  } catch (error) {
    console.error('Error fetching data:', error);
    res.status(500).json({ error: 'Failed to fetch data' });
  }
});

// Сохранить все данные пользователя
app.put("/api/data", (req, res) => {
  try {
    const dataString = JSON.stringify(req.body);
    db.prepare("UPDATE user_data SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1")
      .run(dataString);
    res.json({ success: true });
  } catch (error) {
    console.error('Error saving data:', error);
    res.status(500).json({ error: 'Failed to save data' });
  }
});

// Health check
app.get("/api/health", (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Статические файлы для клиента (опционально)
app.use(express.static('../client'));

app.listen(PORT, () => {
  console.log(`Budget API running on http://localhost:${PORT}`);
});

process.on('exit', () => db.close());
process.on('SIGHUP', () => process.exit(128 + 1));
process.on('SIGINT', () => process.exit(128 + 2));
process.on('SIGTERM', () => process.exit(128 + 15));
```

## Этап 2: Модификация клиентской части

### 2.1. Обновить client/index.html

Найти секцию с загрузкой state и заменить на:

**ЗАМЕНИТЬ:**
```javascript
let state = JSON.parse(localStorage.getItem('budget-ios-state')||'null') || {
  budget:100000, rows:defaults, tx:{}, quick:[-500,-1000,-2000], monthFilter:'', currency:'₽'
};
```

**НА:**
```javascript
// API Configuration
const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:3000/api' 
  : `${window.location.origin}/api`;

let state = {
  budget:100000, rows:defaults, tx:{}, quick:[-500,-1000,-2000], monthFilter:'', currency:'₽'
};
let isOnline = navigator.onLine;
let syncInProgress = false;

// API Functions
async function loadFromServer() {
  if (!isOnline || syncInProgress) return false;
  try {
    syncInProgress = true;
    const response = await fetch(`${API_BASE}/data`);
    if (response.ok) {
      const serverState = await response.json();
      if (Object.keys(serverState).length > 0) {
        state = { ...state, ...serverState };
      }
      return true;
    }
  } catch (error) {
    console.log('Offline mode:', error.message);
    return false;
  } finally {
    syncInProgress = false;
  }
  return false;
}

async function saveToServer() {
  if (!isOnline || syncInProgress) {
    // Сохраняем локально как fallback
    localStorage.setItem('budget-ios-state', JSON.stringify(state));
    return;
  }
  
  try {
    syncInProgress = true;
    await fetch(`${API_BASE}/data`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state)
    });
    // Также сохраняем локально для offline режима
    localStorage.setItem('budget-ios-state', JSON.stringify(state));
  } catch (error) {
    console.log('Saving offline:', error.message);
    // Fallback to localStorage
    localStorage.setItem('budget-ios-state', JSON.stringify(state));
  } finally {
    syncInProgress = false;
  }
}

// Network status tracking
window.addEventListener('online', () => {
  isOnline = true;
  loadFromServer().then(loaded => {
    if (loaded) render();
  });
});

window.addEventListener('offline', () => {
  isOnline = false;
});

// Initialize app
async function initApp() {
  // Сначала загружаем из localStorage
  const localState = JSON.parse(localStorage.getItem('budget-ios-state') || 'null');
  if (localState) {
    state = localState;
  }
  
  // Затем пробуем загрузить с сервера
  const serverLoaded = await loadFromServer();
  render();
  
  // Показываем статус подключения
  updateConnectionStatus();
}

function updateConnectionStatus() {
  // Можно добавить индикатор подключения в UI
  const indicator = document.getElementById('connectionStatus');
  if (indicator) {
    indicator.textContent = isOnline ? '🟢 Онлайн' : '🔴 Офлайн';
  }
}
```

**ЗАМЕНИТЬ функцию save():**
```javascript
function save(){ 
  state.budget = Number(budgetInput.value||0); 
  state.monthFilter = monthPicker.value || '';
  localStorage.setItem('budget-ios-state', JSON.stringify(state)); 
}
```

**НА:**
```javascript
function save(){ 
  state.budget = Number(budgetInput.value||0); 
  state.monthFilter = monthPicker.value || '';
  saveToServer(); // Теперь сохраняем на сервер
}
```

### 2.2. Добавить индикатор подключения

В header добавить статус подключения:

**НАЙТИ:**
```html
<div class="pill"><span>База для %:</span> <strong id="base">0 ₽</strong></div>
```

**ДОБАВИТЬ ПОСЛЕ:**
```html
<div class="pill" id="connectionStatus">🟢 Онлайн</div>
```

### 2.3. Заменить вызов render() в конце файла

**ЗАМЕНИТЬ:**
```javascript
render();
```

**НА:**
```javascript
initApp();
```

### 2.4. Обновить service worker версию

В `client/service-worker.js` обновить версию:

**ЗАМЕНИТЬ:**
```javascript
const CACHE = 'budget-ios-v3';
```

**НА:**
```javascript
const CACHE = 'budget-ios-v4';
```

## Этап 3: Обновление manifest и конфигурации

### 3.1. Обновить client/manifest.json

Добавить поддержку offline работы:

```json
{
  "name": "Бюджет — конверты",
  "short_name": "Бюджет",
  "start_url": "./",
  "display": "standalone",
  "background_color": "#1a1a1a",
  "theme_color": "#111111",
  "orientation": "portrait",
  "prefer_related_applications": false,
  "icons": [
    {
      "src": "icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

## Этап 4: Создание .gitignore

Создать `.gitignore` в корне:

```
node_modules/
server/budget.db
server/budget.db-shm
server/budget.db-wal
.env
*.log
.DS_Store
```

## Этап 5: Документация по запуску

### Разработка

1. **Установка зависимостей:**
```bash
cd server
npm install
```

2. **Запуск сервера:**
```bash
cd server
npm start
```

3. **Запуск клиента:**
```bash
cd client
python -m http.server 8080
# или любой другой статический сервер
```

4. **Открыть:** http://localhost:8080

### Production

1. **Сервер:** Деплой на VPS/Railway/Heroku
2. **Клиент:** GitHub Pages или любой статический хостинг
3. **Обновить API_BASE** в client/index.html на продакшн URL

## Особенности работы

1. **Offline-first:** Приложение работает без интернета, используя localStorage
2. **Синхронизация:** При восстановлении соединения данные автоматически синхронизируются
3. **Fallback:** Если сервер недоступен, используется локальное хранилище
4. **Универсальность:** Один API endpoint для всех данных упрощает архитектуру

## Итоговая структура данных

Все данные (budget, categories, transactions, settings) хранятся как единый JSON объект в таблице `user_data`, что обеспечивает:
- Простоту миграции с текущего localStorage
- Легкость бэкапа/восстановления  
- Минимальные изменения в клиентском коде

## Проверка миграции

После выполнения всех шагов:
1. Запустить сервер: `cd server && npm start`
2. Открыть клиент: `cd client && python -m http.server 8080`
3. Проверить работу в онлайн и офлайн режимах
4. Убедиться, что данные синхронизируются между устройствами