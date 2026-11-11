// G-Toolbox Service Worker: keeps the app shell available when the server is
// unreachable. Served from /sw.js so its scope covers the whole app ("/").
// Note: browsers only enable service workers on secure origins, which includes
// http://127.0.0.1 / localhost but not plain-HTTP LAN addresses.
const CACHE_NAME = 'gtoolbox-shell-v2';
const SHELL = [
  '/',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/vendor/tailwind.css',
  '/static/vendor/fontawesome/css/all.min.css',
  '/static/vendor/fontawesome/webfonts/fa-solid-900.woff2',
  '/static/vendor/fontawesome/webfonts/fa-regular-400.woff2',
  '/static/vendor/fontawesome/webfonts/fa-brands-400.woff2',
  '/static/vendor/fonts/fonts.css',
  '/static/favicon.ico',
  '/static/icon.png',
  '/static/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  // Only the app shell (page + static assets) is cached; API calls, uploads
  // and downloads always go to the network.
  const isShell = url.origin === self.location.origin &&
    (url.pathname === '/' || url.pathname.startsWith('/static/'));
  if (req.method !== 'GET' || !isShell) return;

  // Network first so updates show up immediately; cache as offline fallback.
  event.respondWith(
    fetch(req)
      .then((resp) => {
        if (resp.ok) {
          const copy = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        }
        return resp;
      })
      .catch(() => caches.match(req))
  );
});
