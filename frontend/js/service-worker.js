const CACHE_NAME = 'dropship-v2';
const STATIC_ASSETS = [
    '/',
    '/html/index.html',
    '/html/checkout.html',
    '/html/products.html',
    '/html/account.html',
    '/html/cart.html',
    '/manifest.json',
    '/css/style.css',
    '/js/main.js',
    '/js/api.js',
    '/js/account.js',
    '/js/help.js',
    '/images/logo.svg',
    '/images/icon-192.svg',
    '/images/icon-512.svg',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

const CACHE_STRATEGIES = {
    CACHE_FIRST: 'cache-first',
    NETWORK_FIRST: 'network-first',
    STALE_WHILE_REVALIDATE: 'stale-while-revalidate'
};

function log(msg, data) {
    console.log(`[SW] ${msg}`, data || '');
}

self.addEventListener('install', (event) => {
    log('Installing service worker...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                log('Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    log('Activating service worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        }).then(() => self.clients.claim())
    );
});

function fetchWithCache(request, strategy = CACHE_STRATEGIES.NETWORK_FIRST) {
    return new Promise((resolve, reject) => {
        if (strategy === CACHE_STRATEGIES.CACHE_FIRST) {
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    return resolve(cachedResponse);
                }
                fetch(request).then((response) => {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                    resolve(response);
                }).catch(reject);
            });
        } else if (strategy === CACHE_STRATEGIES.NETWORK_FIRST) {
            fetch(request).then((response) => {
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(request, responseClone);
                });
                resolve(response);
            }).catch(() => {
                caches.match(request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return resolve(cachedResponse);
                    }
                    reject(new Error('No cache available'));
                });
            });
        } else if (strategy === CACHE_STRATEGIES.STALE_WHILE_REVALIDATE) {
            const cachedPromise = caches.match(request);
            fetch(request).then((response) => {
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(request, responseClone);
                });
                resolve(response);
            }).catch(() => {
                cachedPromise.then((cachedResponse) => {
                    if (cachedResponse) {
                        return resolve(cachedResponse);
                    }
                    reject(new Error('No cache available'));
                });
            });
        }
    });
}

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    if (url.pathname.startsWith('/api/') || url.origin.includes('api')) {
        event.respondWith(fetchWithCache(event.request, CACHE_STRATEGIES.NETWORK_FIRST));
        return;
    }
    
    if (url.pathname.endsWith('.js') || url.pathname.endsWith('.css') || url.pathname.endsWith('.json')) {
        event.respondWith(fetchWithCache(event.request, CACHE_STRATEGIES.STALE_WHILE_REVALIDATE));
        return;
    }
    
    if (event.request.method !== 'GET') {
        return;
    }
    
    event.respondWith(fetchWithCache(event.request, CACHE_STRATEGIES.CACHE_FIRST));
});

self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});