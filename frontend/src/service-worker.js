/// <reference lib="webworker" />
/* global self */

const CACHE_NAME = 'budget-pwa-v1';
const API_CACHE = 'api-cache-v1';
const STATIC_CACHE = 'static-v1';

// Базовые файлы для кэширования
const STATIC_ASSETS = [
  '/',
  '/manifest.webmanifest',
  // Добавьте другие статические ресурсы
];

// Установка SW
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: Installing');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Активация SW
self.addEventListener('activate', (event) => {
  console.log('🎯 Service Worker: Activated');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE && cacheName !== STATIC_CACHE) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Обработка запросов
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API sync/pull - Network First (с фоллбеком на кэш)
  if (url.pathname.startsWith('/api/sync/pull')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          const responseClone = response.clone();
          caches.open(API_CACHE).then(cache => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => {
          return caches.match(request).then(cachedResponse => {
            return cachedResponse || new Response('Offline', { status: 503 });
          });
        })
    );
    return;
  }

  // API sync/push - только сеть (с очередью для офлайн)
  if (url.pathname.startsWith('/api/sync/push') && request.method === 'POST') {
    event.respondWith(
      fetch(request).catch(error => {
        // Сохраняем в IndexedDB для последующей отправки
        return request.clone().json().then(data => {
          return saveForLaterSync(data).then(() => {
            return new Response('Queued for sync', { status: 202 });
          });
        });
      })
    );
    return;
  }

  // Статические ресурсы - Cache First
  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then(response => {
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, responseClone);
            });
          }
          return response;
        });
      })
      .catch(() => {
        // Фоллбек для навигации
        if (request.mode === 'navigate') {
          return caches.match('/');
        }
        return new Response('Offline', { status: 503 });
      })
  );
});

// Функция для сохранения данных для последующей синхронизации
async function saveForLaterSync(data) {
  // Используем IndexedDB напрямую или через Dexie (который уже есть в проекте)
  const db = await new Promise((resolve, reject) => {
    const request = indexedDB.open('budget-sync', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending')) {
        db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
  
  const transaction = db.transaction(['pending'], 'readwrite');
  const store = transaction.objectStore('pending');
  await store.add({ data, timestamp: Date.now() });
}