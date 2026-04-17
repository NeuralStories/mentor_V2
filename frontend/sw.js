// Mentor by EgeAI Service Worker
const CACHE_NAME = 'mentor-v2.0.0';
const STATIC_CACHE = 'mentor-static-v2.0.0';
const DYNAMIC_CACHE = 'mentor-dynamic-v2.0.0';

// Recursos a cachear inicialmente
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/manifest.json',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Instalar Service Worker
self.addEventListener('install', (event) => {
    console.log('Service Worker instalándose...');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Cacheando recursos estáticos...');
                return cache.addAll(STATIC_ASSETS);
            })
            .catch(error => {
                console.error('Error cacheando recursos:', error);
            })
    );
    // Forzar activación inmediata
    self.skipWaiting();
});

// Activar Service Worker
self.addEventListener('activate', (event) => {
    console.log('Service Worker activándose...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                        console.log('Eliminando cache antiguo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Tomar control de todos los clientes
            return self.clients.claim();
        })
    );
});

// Interceptar requests
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Estrategia Cache First para recursos estáticos
    if (STATIC_ASSETS.some(asset => request.url.includes(asset))) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // Estrategia Network First para API calls
    if (request.url.includes('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Estrategia Stale While Revalidate para otros recursos
    event.respondWith(staleWhileRevalidate(request));
});

// Estrategia Cache First
async function cacheFirst(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.error('Cache First error:', error);
        // Fallback para recursos críticos
        if (request.url.includes('index.html')) {
            return caches.match('/index.html');
        }
    }
}

// Estrategia Network First
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('Network First fallback to cache:', error);
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        // Fallback para API calls
        return new Response(JSON.stringify({
            error: 'Sin conexión',
            message: 'La aplicación está funcionando en modo offline'
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Estrategia Stale While Revalidate
async function staleWhileRevalidate(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cachedResponse = await cache.match(request);

    const fetchPromise = fetch(request).then(networkResponse => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    });

    return cachedResponse || fetchPromise;
}

// Manejar mensajes del cliente
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// Manejar notificaciones push (futuro)
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/icon-192.png',
            badge: '/icon-192.png',
            vibrate: [100, 50, 100],
            data: {
                dateOfArrival: Date.now(),
                primaryKey: 1
            }
        };

        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Manejar clicks en notificaciones
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    event.waitUntil(
        clients.openWindow('/')
    );
});

// Background sync para mensajes offline (futuro)
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync-messages') {
        event.waitUntil(syncMessages());
    }
});

async function syncMessages() {
    // Implementar sincronización de mensajes offline
    console.log('Sincronizando mensajes en background...');
}