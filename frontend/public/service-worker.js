// CommandHub PWA Service Worker - DESACTIVE TEMPORAIREMENT
console.log('[SW] Service Worker desactive');

// Pas de cache, pas de fetch interception
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());
self.addEventListener('fetch', (event) => {
  // Ne pas intercepter les requêtes - laisser passer normalement
  return;
});

// Activation du Service Worker
self.addEventListener('activate', (event) => {
  console.log('[SW] Activation en cours...');
  const currentCaches = [CACHE_NAME, RUNTIME_CACHE];
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return cacheNames.filter((cacheName) => !currentCaches.includes(cacheName));
      })
      .then((cachesToDelete) => {
        return Promise.all(cachesToDelete.map((cacheToDelete) => {
          console.log('[SW] Suppression ancien cache:', cacheToDelete);
          return caches.delete(cacheToDelete);
        }));
      })
      .then(() => {
        console.log('[SW] Activation terminée');
        return self.clients.claim();
      })
  );
});

// Interception des requêtes
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorer les requêtes non-HTTP(S)
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Stratégie: Network First, fallback to Cache
  // Pour les API calls (/api/*), toujours essayer le réseau d'abord
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Si la réponse est OK, la mettre en cache
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Si offline, essayer de servir depuis le cache
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              console.log('[SW] Serving from cache (offline):', request.url);
              return cachedResponse;
            }
            // Si pas en cache, retourner une réponse d'erreur
            return new Response(
              JSON.stringify({ error: 'Offline - donnée non disponible en cache' }),
              {
                status: 503,
                statusText: 'Service Unavailable',
                headers: new Headers({ 'Content-Type': 'application/json' })
              }
            );
          });
        })
    );
    return;
  }

  // Pour les autres requêtes (HTML, CSS, JS, images)
  // Stratégie: Cache First, fallback to Network
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          console.log('[SW] Serving from cache:', request.url);
          return cachedResponse;
        }

        return fetch(request)
          .then((response) => {
            // Ne pas mettre en cache les réponses non-OK
            if (!response || response.status !== 200 || response.type === 'error') {
              return response;
            }

            // Cloner la réponse pour la mettre en cache
            const responseClone = response.clone();
            
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseClone);
            });

            return response;
          })
          .catch((error) => {
            console.error('[SW] Fetch failed:', error);
            
            // Si c'est une requête de navigation et qu'on est offline
            if (request.mode === 'navigate') {
              return caches.match('/');
            }
            
            throw error;
          });
      })
  );
});

// Gestion des messages du client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[SW] SKIP_WAITING reçu');
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLIENTS_CLAIM') {
    console.log('[SW] CLIENTS_CLAIM reçu');
    self.clients.claim();
  }
  
  // Répondre avec le statut du cache
  if (event.data && event.data.type === 'CACHE_STATUS') {
    caches.keys().then((cacheNames) => {
      event.ports[0].postMessage({
        caches: cacheNames,
        version: CACHE_NAME
      });
    });
  }
});

// Gestion de la synchronisation en arrière-plan (Background Sync)
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-data') {
    event.waitUntil(
      // Ici, vous pourriez déclencher une synchronisation automatique
      // des données stockées localement vers le serveur
      Promise.resolve()
    );
  }
});

console.log('[SW] Service Worker chargé - CommandHub v1');
