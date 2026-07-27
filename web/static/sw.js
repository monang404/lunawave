// ── Service Worker — LunaWave ──
// Strategy: Cache-first untuk static assets, network-first untuk API/WS

// PATCH-2026-07-24-222: precache list ditulis ulang total mengikuti struktur
// shared/ + pages/ (root shared/js/*.js lama sudah dipindah sesi-sesi
// sebelumnya, sw.js belum pernah ikut disinkronkan -- lihat PATCHLOG).
const CACHE_VERSION = 'lunawave-20260724-offline-v3';
const STATIC_CACHE = `${CACHE_VERSION}-static`;

// Assets yang di-cache saat install
const PRECACHE_ASSETS = [
    // ── App shell routes (server-rendered, bukan file statis) ──
    '/',
    '/admin',
    '/admin/logs',

    '/static/manifest.json',

    // ── Icons ──
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',

    // ── Fonts (self-hosted, dipakai radio-hero.css) ──
    '/static/media/fonts/fraunces/fraunces-latin-500-italic.woff2',
    '/static/media/fonts/space-grotesk/space-grotesk-latin-400-normal.woff2',
    '/static/media/fonts/space-grotesk/space-grotesk-latin-500-normal.woff2',
    '/static/media/fonts/space-grotesk/space-grotesk-latin-600-normal.woff2',

    // ── Vendor (self-hosted, offline-safe) ──
    '/static/shared/css/vendor/tabler-icons.min.css',
    '/static/media/fonts/vendor/tabler-icons.woff2',
    '/static/media/fonts/vendor/tabler-icons.woff',
    '/static/media/fonts/vendor/tabler-icons.ttf',

    // ── CSS: Base ──
    '/static/shared/css/tokens.css',
    '/static/shared/css/portal.css',
    '/static/shared/css/base/reset.css',
    '/static/shared/css/base/typography.css',
    '/static/shared/css/base/animations.css',

    // ── CSS: Layout ──
    '/static/shared/css/layout/app-shell.css',
    '/static/shared/css/layout/nav.css',
    '/static/shared/css/layout/grid.css',

    // ── CSS: Components ──
    '/static/shared/css/components/player-bar.css',
    '/static/shared/css/components/player-controls.css',
    '/static/shared/css/components/cards.css',
    '/static/shared/css/components/lyrics.css',
    '/static/shared/css/components/queue.css',
    '/static/shared/css/components/search.css',
    '/static/shared/css/components/settings-sheet.css',
    '/static/shared/css/components/toasts.css',
    '/static/shared/css/components/radio-hero.css',
    '/static/shared/css/components/discover-cards.css',
    '/static/shared/css/components/discover-search.css',

    // ── CSS: Platform ──
    '/static/shared/css/platform/mobile.css',
    '/static/shared/css/platform/desktop.css',
    '/static/shared/css/platform/tablet.css',
    '/static/shared/css/platform/landscape.css',
    '/static/shared/css/platform/safe-area.css',

    // ── CSS: Page-specific ──
    '/static/pages/client/chat.css',

    // ── JS: Core ──
    '/static/shared/js/store.js',
    '/static/shared/js/dom.js',
    '/static/shared/js/ws.js',
    '/static/shared/js/portal.js',
    '/static/shared/js/config.js',

    // ── JS: Utils ──
    '/static/shared/js/utils/format.js',
    '/static/shared/js/utils/cover-art.js',

    // ── JS: Events ──
    '/static/shared/js/events/index.js',
    '/static/shared/js/events/action-modal-events.js',
    '/static/shared/js/events/click-delegation-events.js',
    '/static/shared/js/events/discover-search-events.js',
    '/static/shared/js/events/drag-scroll-events.js',
    '/static/shared/js/events/keyboard-shortcut-events.js',
    '/static/shared/js/events/lyrics-events.js',
    '/static/shared/js/events/progress-events.js',
    '/static/shared/js/events/queue-events.js',
    '/static/shared/js/events/search-input-events.js',
    '/static/shared/js/events/settings-events.js',
    '/static/shared/js/events/transport-events.js',

    // ── JS: Render ──
    '/static/shared/js/render/player.js',
    '/static/shared/js/render/search.js',
    '/static/shared/js/render/lyrics.js',
    '/static/shared/js/render/queue.js',
    '/static/shared/js/render/now-playing.js',
    '/static/shared/js/render/discover-tab.js',
    '/static/shared/js/render/discover-search.js',
    '/static/shared/js/render/discover-personalize.js',
    '/static/shared/js/render/radio-tab.js',
    '/static/shared/js/render/radio-hero-moon.js',
    '/static/shared/js/render/full-state.js',
    '/static/shared/js/render/toast.js',

    // ── JS: Services ──
    '/static/shared/js/services/auth.js',

    // ── JS: Platform ──
    '/static/shared/js/platform/keyboard.js',
    '/static/shared/js/platform/touch.js',
    '/static/shared/js/platform/viewport.js',

    // ── JS: Audio ──
    '/static/shared/js/audio/playback-sync.js',
    '/static/shared/js/audio/visualizer.js',

    // ── JS: Page entry points ──
    '/static/pages/app/main.js',
    '/static/pages/client/client.js',
    '/static/pages/client/chat.js',
    '/static/pages/admin-logs/admin-logs.js',
];

// Install: pre-cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                return Promise.all(
                    PRECACHE_ASSETS.map(url =>
                        cache.add(url).catch(err => console.warn('Cache add failed for', url, err))
                    )
                );
            })
            .then(() => self.skipWaiting())
    );
});

// Activate: hapus cache lama
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(key => key !== STATIC_CACHE)
                    .map(key => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch: cache-first untuk static, network-only untuk WS dan API
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip WebSocket dan API requests
    if (url.pathname.startsWith('/ws') || url.pathname.startsWith('/api')) {
        return; // Biarkan browser handle secara normal
    }

    // Cache-first untuk static assets
    if (event.request.method === 'GET') {
        event.respondWith(
            caches.match(event.request).then(cached => {
                if (cached) return cached;
                return fetch(event.request).then(response => {
                    // Cache response baru
                    if (response.ok) {
                        const cloned = response.clone();
                        caches.open(STATIC_CACHE).then(cache => cache.put(event.request, cloned));
                    }
                    return response;
                });
            }).catch(() => {
                // Offline fallback
                // Catatan (PATCH-2026-07-24-222): '/static/index.html' tidak pernah
                // ada -- yang di-serve server adalah route '/', '/admin', dan
                // '/admin/logs' (lihat server/app.py), bukan file statis. Fallback
                // diarahkan ke shell route yang sesuai, semuanya sudah di-precache.
                if ((event.request.headers.get('accept') || '').includes('text/html')) {
                    if (url.pathname.startsWith('/admin/logs')) {
                        return caches.match('/admin/logs');
                    }
                    if (url.pathname.startsWith('/admin')) {
                        return caches.match('/admin');
                    }
                    return caches.match('/');
                }
            })
        );
    }
});
