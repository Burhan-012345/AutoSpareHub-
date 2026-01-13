/**
 * AutoSpareHub Service Worker
 * For PWA functionality and offline support
 */

const CACHE_NAME = 'autosparehub-v1';
const OFFLINE_URL = '/offline.html';

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/static/css/theme.css',
  '/static/css/animations.css',
  '/static/js/main.js',
  '/static/js/pwa.js',
  '/static/images/logo.png',
  '/static/images/favicon.ico',
  '/static/images/icons/icon-192x192.png',
  '/static/images/icons/icon-512x512.png',
  '/manifest.json'
];

// Install event - cache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching app shell');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => {
        console.log('Service Worker installed');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker activated');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) return;

  // Skip API calls and admin routes
  if (event.request.url.includes('/api/') || 
      event.request.url.includes('/admin/') ||
      event.request.url.includes('/auth/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        // Return cached response if found
        if (cachedResponse) {
          return cachedResponse;
        }

        // Clone the request because it can only be used once
        const fetchRequest = event.request.clone();

        return fetch(fetchRequest)
          .then(response => {
            // Check if we received a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response because it can only be used once
            const responseToCache = response.clone();

            // Cache the new response
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // If network fails and no cache, show offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
            
            // For other requests, return a generic offline response
            return new Response('Network error occurred', {
              status: 408,
              headers: { 'Content-Type': 'text/plain' }
            });
          });
      })
  );
});

// Push notification event
self.addEventListener('push', event => {
  let data = {};
  
  if (event.data) {
    data = event.data.json();
  }
  
  const options = {
    body: data.body || 'New notification from AutoSpareHub',
    icon: data.icon || '/static/images/icons/icon-192x192.png',
    badge: data.badge || '/static/images/icons/icon-192x192.png',
    vibrate: [100, 50, 100],
    data: data.data || {},
    actions: [
      {
        action: 'view',
        title: 'View'
      },
      {
        action: 'close',
        title: 'Close'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(
      data.title || 'AutoSpareHub',
      options
    )
  );
});

// Notification click event
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  const urlToOpen = event.notification.data.url || '/';

  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(windowClients => {
      // Check if there's already a window/tab open with the target URL
      for (let client of windowClients) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }

      // If not, open a new window/tab
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Background sync for offline data
self.addEventListener('sync', event => {
  if (event.tag === 'sync-cart') {
    event.waitUntil(syncCart());
  }
});

// Sync cart data when online
async function syncCart() {
  const requests = await getSyncRequests();
  
  for (const request of requests) {
    try {
      await fetch(request.url, request.options);
      await deleteSyncRequest(request.id);
    } catch (error) {
      console.error('Sync failed:', error);
    }
  }
}

// Helper functions for background sync
async function getSyncRequests() {
  const db = await openSyncDB();
  const requests = await db.getAll('sync-requests');
  db.close();
  return requests;
}

async function deleteSyncRequest(id) {
  const db = await openSyncDB();
  await db.delete('sync-requests', id);
  db.close();
}

async function openSyncDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('autosparehub-sync', 1);
    
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('sync-requests')) {
        db.createObjectStore('sync-requests', { keyPath: 'id' });
      }
    };
    
    request.onsuccess = event => resolve(event.target.result);
    request.onerror = event => reject(event.target.error);
  });
}

// Periodic sync for background updates
self.addEventListener('periodicsync', event => {
  if (event.tag === 'update-products') {
    event.waitUntil(updateProductCache());
  }
});

// Update product cache periodically
async function updateProductCache() {
  try {
    const response = await fetch('/api/products/recent');
    const products = await response.json();
    
    const cache = await caches.open(CACHE_NAME);
    const urls = products.map(p => `/shop/product/${p.slug}`);
    
    for (const url of urls) {
      const productResponse = await fetch(url);
      if (productResponse.ok) {
        await cache.put(url, productResponse);
      }
    }
    
    console.log('Product cache updated');
  } catch (error) {
    console.error('Failed to update product cache:', error);
  }
}