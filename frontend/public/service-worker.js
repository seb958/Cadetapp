// CommandHub Service Worker - COMPLETEMENT DESACTIVE
console.log('[SW] Service Worker désactivé - pas de cache, pas d\'interception');

// Installation: skip waiting immédiatement
self.addEventListener('install', (event) => {
  console.log('[SW] Installation - skip waiting');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          console.log('[SW] Suppression du cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => self.skipWaiting())
  );
});

// Activation: supprimer tous les caches et claim
self.addEventListener('activate', (event) => {
  console.log('[SW] Activation - suppression de tous les caches');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          console.log('[SW] Suppression du cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      console.log('[SW] Tous les caches supprimés');
      return self.clients.claim();
    })
  );
});

// Fetch: NE RIEN FAIRE - laisser passer toutes les requêtes sans interception
self.addEventListener('fetch', (event) => {
  // Ne rien faire du tout - pas d'interception, pas de cache
  return;
});
