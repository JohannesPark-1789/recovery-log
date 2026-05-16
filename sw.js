// Recovery Log Service Worker
// Strategy: NETWORK-FIRST for app shell, with cache fallback for offline
// Update CACHE version when you want to force eviction of old cached assets

const CACHE = 'recovery-log-v9-2026-05-16-sync';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './costs.json'
];

// On install, pre-cache assets and immediately activate
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(ASSETS))
      .catch(() => {})
  );
  self.skipWaiting(); // Don't wait for old SW to be released
});

// On activate, delete old caches and take control of all open clients
self.addEventListener('activate', (e) => {
  e.waitUntil(
    Promise.all([
      // Delete all caches that aren't the current one
      caches.keys().then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      ),
      // Take control of all clients immediately
      self.clients.claim()
    ])
  );
});

// Network-first fetch strategy:
// 1. Try network — get fresh content
// 2. On success, update cache silently
// 3. On failure (offline), serve from cache
self.addEventListener('fetch', (e) => {
  const req = e.request;

  // Only handle GET requests
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // For navigation (HTML page loads) and same-origin requests, always try network first
  if (req.mode === 'navigate' || url.origin === location.origin) {
    e.respondWith(
      fetch(req)
        .then((res) => {
          // Network succeeded → cache the fresh copy and return it
          if (res && res.status === 200) {
            const copy = res.clone();
            caches.open(CACHE).then((cache) => cache.put(req, copy)).catch(() => {});
          }
          return res;
        })
        .catch(() => {
          // Network failed (offline) → try cache
          return caches.match(req).then((cached) => {
            return cached || caches.match('./index.html'); // fallback to root
          });
        })
    );
    return;
  }

  // For cross-origin requests (fonts, CDNs), use stale-while-revalidate:
  // serve from cache if available, but always update in background
  e.respondWith(
    caches.match(req).then((cached) => {
      const fetchPromise = fetch(req)
        .then((res) => {
          if (res && res.status === 200) {
            const copy = res.clone();
            caches.open(CACHE).then((cache) => cache.put(req, copy)).catch(() => {});
          }
          return res;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});

// Listen for skipWaiting messages from page (manual refresh trigger)
self.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
