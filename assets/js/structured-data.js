/*
 * Datos estructurados para listados cuyos datos se cargan desde un JSON.
 * Descarga el fichero, lo convierte en un ItemList de entidades schema.org
 * (Museum, Hospital, School...) e inyecta un <script type="application/ld+json">.
 *
 * Uso (al final de la página):
 *   OpenSalamancaLD.itemList({
 *     file: '/museos-salamanca.json',
 *     type: 'Museum',
 *     pick: d => d.capital.concat(d.provincia),
 *     map: r => ({ name: r.nombre_oficial, address: r.direccion, lat: r.coordenadas.lat, lon: r.coordenadas.lon, url: r.web_oficial })
 *   });
 */
(function () {
  'use strict';

  function postalAddress(raw) {
    if (!raw) return undefined;
    var m = String(raw).match(/^(.*?),?\s*(\d{5})\s+(.+)$/);
    var addr = { '@type': 'PostalAddress', addressCountry: 'ES' };
    if (m) {
      addr.streetAddress = m[1].trim();
      addr.postalCode = m[2];
      addr.addressLocality = m[3].trim();
    } else {
      addr.streetAddress = String(raw).trim();
      addr.addressLocality = 'Salamanca';
    }
    return addr;
  }

  function entity(type, r) {
    if (!r || !r.name) return null;
    var e = { '@type': type, name: String(r.name).trim() };
    var addr = postalAddress(r.address);
    if (addr) e.address = addr;
    if (typeof r.lat === 'number' && typeof r.lon === 'number') {
      e.geo = { '@type': 'GeoCoordinates', latitude: r.lat, longitude: r.lon };
    }
    if (r.url && /^https?:\/\//i.test(r.url)) e.url = r.url;
    if (r.telephone) e.telephone = String(r.telephone).trim();
    return e;
  }

  function itemList(opts) {
    fetch(opts.file)
      .then(function (res) { return res.json(); })
      .then(function (data) {
        var items = [];
        opts.pick(data).forEach(function (rec) {
          var e = entity(opts.type, opts.map(rec));
          if (e) items.push(e);
        });
        if (!items.length) return;
        var ld = {
          '@context': 'https://schema.org',
          '@type': 'ItemList',
          name: opts.name || document.title.replace(/\s*\|\s*Open Salamanca$/, ''),
          numberOfItems: items.length,
          itemListElement: items.map(function (item, i) {
            return { '@type': 'ListItem', position: i + 1, item: item };
          })
        };
        var s = document.createElement('script');
        s.type = 'application/ld+json';
        s.textContent = JSON.stringify(ld);
        document.head.appendChild(s);
      })
      .catch(function () { /* el marcado es opcional: si falla la carga, la página sigue igual */ });
  }

  window.OpenSalamancaLD = { itemList: itemList };
})();
