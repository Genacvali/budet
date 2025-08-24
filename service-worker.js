// ↑ УВЕЛИЧИ версию при каждом деплое
const CACHE = 'budget-ios-v3';
const ASSETS = [
  './', './index.html', './manifest.json',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'
];

// Быстро активируем новую версию
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});
self.addEventListener('activate', e => {
  e.waitUntil(
    Promise.all([
      caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))),
      self.clients.claim()
    ])
  );
});

// HTML (навигация) — сначала сеть, потом кэш (чтобы index.html всегда обновлялся)
self.addEventListener('fetch', e => {
  const req = e.request;
  const accept = req.headers.get('accept') || '';
  if (req.mode === 'navigate' || accept.includes('text/html')) {
    e.respondWith(
      fetch(req).then(resp => {
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
        return resp;
      }).catch(() => caches.match('./index.html'))
    );
    return;
  }
  // Остальное — кэш, потом сеть (и подкладываем в кэш)
  e.respondWith(
    caches.match(req).then(res => res || fetch(req).then(resp => {
      const copy = resp.clone();
      caches.open(CACHE).then(c => c.put(req, copy));
      return resp;
    }))
  );
});

// Позволяем странице попросить немедленную активацию
self.addEventListener('message', e => {
  if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting();
});