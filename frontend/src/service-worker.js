/// <reference lib="webworker" />
/* global self */
importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.6.0/workbox-sw.js');

workbox.core.skipWaiting();
workbox.core.clientsClaim();

// Статика
workbox.precaching.precacheAndRoute(self.__WB_MANIFEST || []);

// Кэш first for API pull (безопасно, с фоллбеком)
workbox.routing.registerRoute(
  ({url}) => url.pathname.startsWith('/api/sync/pull'),
  new workbox.strategies.NetworkFirst({ cacheName: 'pull-cache', networkTimeoutSeconds: 3 })
);

// Background Sync для push
const bgSyncPlugin = new workbox.backgroundSync.BackgroundSyncPlugin('sync-queue', { maxRetentionTime: 24 * 60 });
workbox.routing.registerRoute(
  ({url, request}) => url.pathname.startsWith('/api/sync/push') && request.method === 'POST',
  new workbox.strategies.NetworkOnly({ plugins: [bgSyncPlugin] }),
  'POST'
);

// Кэш картинок/иконок
workbox.routing.registerRoute(
  ({request}) => request.destination === 'image',
  new workbox.strategies.StaleWhileRevalidate({ cacheName: 'images' })
);