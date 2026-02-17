const CACHE_NAME = "kairos-cds-v1";
const PRECACHE_URLS = ["/", "/index.html"];

// Install — precache critical assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// Activate — clean old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch — network-first with cache fallback (SPA-friendly)
self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Skip non-GET, WebSocket, and API calls
  if (
    request.method !== "GET" ||
    request.url.includes("/api/") ||
    request.url.includes("/ws/") ||
    request.url.includes("/health") ||
    request.url.includes("/metrics")
  ) {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cache successful responses
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        // Fallback to cache
        return caches.match(request).then((cached) => {
          return cached || caches.match("/index.html");
        });
      })
  );
});
