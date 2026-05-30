var CACHE_VERSION = 'v2.0.0';
var CACHE_NAME = 'gulicalc-' + CACHE_VERSION;
var SHELL_FILES = [
  '/',
  '/css/style.css',
  '/js/calculator.js',
  '/images/logo-nav.png',
  '/manifest.json'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(SHELL_FILES).catch(function(){});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k.startsWith('gulicalc-') && k !== CACHE_NAME; })
            .map(function(k) { return caches.delete(k); })
      );
    }).then(function() { return self.clients.claim(); })
  );
});

// 網路優先：線上一律拿最新內容，離線時才用快取備援。
// （原本「快取優先」會讓更新後的頁面被舊快取卡住，導致改動看不到。）
self.addEventListener('fetch', function(event) {
  var req = event.request;
  if (req.method !== 'GET') return;
  // 即時股價 API 不經 SW 快取
  if (req.url.indexOf('/api/') !== -1) return;
  event.respondWith(
    fetch(req).then(function(res) {
      if (res && res.status === 200 && res.type === 'basic') {
        var copy = res.clone();
        caches.open(CACHE_NAME).then(function(c) { c.put(req, copy); }).catch(function(){});
      }
      return res;
    }).catch(function() {
      return caches.match(req).then(function(c) { return c || caches.match('/'); });
    })
  );
});
