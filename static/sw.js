// todo licensing

/*
this.addEventListener('fetch', function(event) {
  console.log('got fetch')

  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    })
  );
});
*/

this.addEventListener('fetch', function(event) {
  console.log('got feeetch')
  event.respondWith(
    caches.match(event.request).then(function(resp) {
      if (resp) {
        console.log('omg it is cached hooray yes')
        return resp
      }

      return fetch(event.request).then(function(response) {
        return caches.open('v1').then(function(cache) {
          cache.put(event.request, response.clone())
          return response
        });
      });
    })
  );
});
