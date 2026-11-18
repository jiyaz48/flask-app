/**
 * TaskFlow Service Worker
 * Version: taskflow-shell-v1
 *
 * Strategies:
 * 1. API Requests (/api/*) & Non-GET: NEVER cached. Always bypass to network.
 * 2. Navigations (HTML pages): Network-First, fallback to cached shell or /offline.
 * 3. Static Assets (CSS, JS, Icons): Cache-First with network fallback.
 */

const CACHE_PREFIX = 'taskflow-shell-';
const CACHE_NAME = 'taskflow-shell-v1';

const PRECACHE_ASSETS = [
    '/',
    '/offline',
    '/manifest.webmanifest',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/static/icons/icon-maskable-192.png',
    '/static/icons/icon-maskable-512.png'
];

// Install Event: Precache application shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS);
        }).then(() => {
            return self.skipWaiting();
        })
    );
});

// Activate Event: Clean up only old caches belonging to TaskFlow
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    // Only delete old caches that match the TaskFlow cache prefix
                    if (name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME) {
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => {
            return self.clients.claim();
        })
    );
});

// Fetch Event: Routing and Caching Strategies
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // 1. Never intercept or cache non-GET requests (POST, PUT, PATCH, DELETE)
    if (request.method !== 'GET') {
        return;
    }

    // 2. Never cache task API requests (/api/*) or health check (/health)
    // Always fetch directly from network to ensure live SQLite data integrity.
    if ((url.pathname === '/api' || url.pathname.startsWith('/api/')) || url.pathname === '/health') {
        event.respondWith(
            fetch(request).catch(() => {
                return new Response(
                    JSON.stringify({
                        error: 'Network unavailable. Task operations require an active connection.'
                    }),
                    {
                        status: 503,
                        headers: { 'Content-Type': 'application/json' }
                    }
                );
            })
        );
        return;
    }

    // 3. Navigation Requests (Page Visits): Network-First with Offline Fallback
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    // Cache only successful, non-opaque responses
                    if (
                        networkResponse &&
                        networkResponse.ok &&
                        networkResponse.status === 200 &&
                        networkResponse.type !== 'opaque'
                    ) {
                        const responseClone = networkResponse.clone();
                        // Use event.waitUntil to guarantee cache write completes reliably
                        event.waitUntil(
                            caches.open(CACHE_NAME).then((cache) => {
                                return cache.put(request, responseClone);
                            })
                        );
                    }
                    return networkResponse;
                })
                .catch(async () => {
                    const cache = await caches.open(CACHE_NAME);
                    const cachedPage = await cache.match(request);
                    if (cachedPage) {
                        return cachedPage;
                    }
                    const fallback = await cache.match('/offline');
                    return fallback || (await cache.match('/'));
                })
        );
        return;
    }

    // 4. Static Assets (CSS, JS, Icons, Manifest): Cache-First with Network Fallback
    if (
        url.pathname.startsWith('/static/') ||
        url.pathname === '/manifest.webmanifest' ||
        url.hostname === 'fonts.googleapis.com' ||
        url.hostname === 'fonts.gstatic.com'
    ) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(request).then((networkResponse) => {
                    // Cache only successful, non-opaque responses
                    if (
                        networkResponse &&
                        networkResponse.ok &&
                        networkResponse.status === 200 &&
                        networkResponse.type !== 'opaque'
                    ) {
                        const responseClone = networkResponse.clone();
                        // Use event.waitUntil to guarantee cache write completes reliably
                        event.waitUntil(
                            caches.open(CACHE_NAME).then((cache) => {
                                return cache.put(request, responseClone);
                            })
                        );
                    }
                    return networkResponse;
                });
            })
        );
        return;
    }

    // Default: Normal network fetch
    event.respondWith(fetch(request));
});
