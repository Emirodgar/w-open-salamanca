#!/usr/bin/env python3
"""Genera una página HTML por cada línea regular de autobús (1-15) a partir de
lineas-autobus.json: recorrido, tabla de paradas, conexiones y mapa.

Uso (desde la raíz del repo):  python scripts/lineas-bus/build_paginas.py
Las páginas son estáticas: vuelve a ejecutar el script si cambia lineas-autobus.json.
"""
import collections, html, json, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINEAS = json.loads((ROOT / 'lineas-autobus.json').read_text(encoding='utf-8'))
HOY = date.today().strftime('%d-%m-%Y')
MAX_REGULAR = 15


def esc(s):
    return html.escape(s, quote=True)


def limpia(s):
    return re.sub(r'\s+', ' ', s).strip()


def nombre(l):
    s = limpia(l['nombre']).replace('LADRLLO', 'LADRILLO')
    return s.title().replace(' - ', ' – ').replace('Por ', 'por ').replace(' Ii', ' II')


def trayecto(l):
    s = limpia(l.get('trayecto', '')).replace('Julían', 'Julián').replace('B. Blanco', 'Barrio Blanco')
    s = re.sub(r'(\w)\(', r'\1 (', s)
    return [limpia(p) for p in s.split('>')]


def slug(i):
    return f'linea-{i}-autobus-salamanca'


regulares = [l for l in LINEAS if int(l['id']) <= MAX_REGULAR]
por_ref = collections.defaultdict(set)
for l in LINEAS:
    for p in l['paradas']:
        por_ref[p['ref']].add(l['id'])


def conexiones(l):
    c = collections.Counter()
    for p in l['paradas']:
        for o in por_ref[p['ref']]:
            if o != l['id']:
                c[o] += 1
    return sorted(c.items(), key=lambda kv: (-kv[1], int(kv[0])))


def plural(k):
    return 'parada' if k == 1 else 'paradas'


PLANTILLA = """---
layout: default
title: "@TITULO@"
description: "@DESC@"
date: @FECHA@
crumb_category: Movilidad
parent_url: /mapa-lineas-autobus
parent_title: Mapa de líneas de autobús
permalink: @SLUG@
dataset_files:
  - lineas-autobus.json
dataset_source: "Salamanca de Transportes (información de líneas)"
dataset_source_url: https://salamancadetransportes.com/informacion-de-lineas/lineas/
---

    <section class="featured dataset" id="datos">
        <div class="container">
            <div class="section-header">
                <h1 class="section-title">{{ page.title }}</h1>
                <p class="section-description">{{ page.description }}</p>
            </div>

            <div id="section-content">

  <p class="answer-first"><b>¿Por dónde va la línea @I@ del autobús de Salamanca?</b> La línea @I@ (@NOM@), de Salamanca de Transportes, tiene <b>@N@ paradas</b> en este mapa, de <b>@INI@</b> a <b>@FIN@</b>. El número entre paréntesis es el código de la parada.</p>

  <div id="mapaLinea" class="bus-map-canvas" role="img" aria-label="Mapa del recorrido de la línea @I@ de autobús de Salamanca"></div>
  <p class="bus-map-nota">Haz clic en una parada para ver su nombre y su código. El trazado une las paradas en el orden de la línea (dato de <a href="https://salamancadetransportes.com/informacion-de-lineas/lineas/" target="_blank" rel="noopener">Salamanca de Transportes</a>); no es el recorrido exacto calle a calle.</p>
  <p>@NAV@</p>

  <h2>Paradas de la línea @I@ en orden</h2>
  <table class="bus-lineas-tabla" border="1" cellpadding="5" cellspacing="0">
    <caption>Paradas de la línea @I@ (@NOM@)</caption>
    <thead><tr><th scope="col">Nº</th><th scope="col">Parada</th><th scope="col">Código</th></tr></thead>
    <tbody>
@FILAS@    </tbody>
  </table>

  <h2>Conexiones con otras líneas</h2>
  <p>@CON_HTML@ Consulta el <a href="/mapa-lineas-autobus">mapa de todas las líneas</a> y el <a href="/transporte-urbano-bus">uso del autobús urbano</a> para ver la red completa.</p>

  <h2>Preguntas frecuentes sobre la línea @I@</h2>
  <h3>¿Cuál es el recorrido de la línea @I@ del autobús de Salamanca?</h3>
  <p>@RESP_REC@</p>
  <h3>¿Con qué otras líneas conecta la línea @I@?</h3>
  <p>@RESP_CON@</p>
  <script type="application/ld+json">@FAQ@</script>

  <p style="font-size:0.9em; color:#555;">Datos: <a href="/lineas-autobus.json">lineas-autobus.json</a>, elaborado a partir de la información de líneas de Salamanca de Transportes. Para horarios y frecuencias, consulta la web del operador.</p>

            </div>
        </div>
    </section>

    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
    (function () {
        var mapa = L.map('mapaLinea').setView([40.9650, -5.6630], 13);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png?key=cb1_2izw_1_55d93b51ded1dcecfa044181', {
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            maxZoom: 19
        }).addTo(mapa);
        fetch('/lineas-autobus.json')
            .then(function (r) { return r.json(); })
            .then(function (lineas) {
                var linea = lineas.filter(function (l) { return l.id === '@I@'; })[0];
                if (!linea) return;
                var pts = linea.paradas.map(function (p) { return [p.lat, p.lng]; });
                var pl = L.polyline(pts, { color: linea.color, weight: 4, opacity: 0.85, lineJoin: 'round' }).addTo(mapa);
                linea.paradas.forEach(function (p, k) {
                    L.circleMarker([p.lat, p.lng], { radius: 5, weight: 2, color: '#ffffff', fillColor: linea.color, fillOpacity: 1 })
                        .bindPopup('<b>Línea ' + linea.id + '</b><br>' + (k + 1) + '. ' + p.name + '<br>Parada ' + p.ref)
                        .addTo(mapa);
                });
                mapa.fitBounds(pl.getBounds(), { padding: [20, 20] });
            });
    })();
    </script>
"""

for idx, l in enumerate(regulares):
    i = l['id']
    n = len(l['paradas'])
    tr = trayecto(l)
    if len(tr) >= 2:
        ini, fin = tr[0], tr[-1]
    else:
        ini, fin = limpia(l['paradas'][0]['name']), limpia(l['paradas'][-1]['name'])
    ini_s = re.sub(r'\s*\(\d+\)$', '', ini)
    fin_s = re.sub(r'\s*\(\d+\)$', '', fin)
    nom = nombre(l)
    con = conexiones(l)
    con_html = [(f'<a href="/{slug(o)}">línea {o}</a>' if int(o) <= MAX_REGULAR else f'línea {o}')
                + f' ({k} {plural(k)})' for o, k in con]
    con_plano = [f'línea {o} ({k} {plural(k)})' for o, k in con]
    filas = ''.join(
        f'      <tr><td>{j}</td><td>{esc(limpia(p["name"]))}</td><td>{esc(p["ref"])}</td></tr>\n'
        for j, p in enumerate(l['paradas'], 1))
    prev_l = regulares[idx - 1]['id'] if idx > 0 else None
    next_l = regulares[idx + 1]['id'] if idx < len(regulares) - 1 else None
    nav = ' · '.join(x for x in [
        f'<a href="/{slug(prev_l)}">← Línea {prev_l}</a>' if prev_l else '',
        '<a href="/mapa-lineas-autobus">Todas las líneas</a>',
        f'<a href="/{slug(next_l)}">Línea {next_l} →</a>' if next_l else ''] if x)
    resp_rec = f'La línea {i} ({nom}) recorre {n} paradas entre {ini_s} y {fin_s}.'
    resp_con = (f'Comparte paradas con {", ".join(con_plano)}.' if con
                else 'En los datos de este mapa no comparte paradas con otras líneas.')
    con_html_txt = (f'Comparte paradas (mismo código de parada) con {", ".join(con_html)}.' if con
                    else 'En los datos de este mapa no comparte paradas con otras líneas.')
    faq = json.dumps({
        '@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': f'¿Cuál es el recorrido de la línea {i} del autobús de Salamanca?',
             'acceptedAnswer': {'@type': 'Answer', 'text': resp_rec}},
            {'@type': 'Question', 'name': f'¿Con qué otras líneas conecta la línea {i}?',
             'acceptedAnswer': {'@type': 'Answer', 'text': resp_con}}]}, ensure_ascii=False)
    desc = (f'Recorrido de la línea {i} del autobús urbano de Salamanca ({nom}): '
            f'{n} paradas, mapa y conexiones con otras líneas')
    valores = {
        'TITULO': f'Línea {i} de autobús de Salamanca: recorrido y paradas', 'DESC': esc(desc),
        'FECHA': HOY, 'SLUG': slug(i), 'I': i, 'NOM': esc(nom), 'N': n, 'INI': esc(ini), 'FIN': esc(fin),
        'NAV': nav, 'FILAS': filas, 'CON_HTML': con_html_txt, 'RESP_REC': esc(resp_rec),
        'RESP_CON': esc(resp_con), 'FAQ': faq}
    page = PLANTILLA
    for k, v in valores.items():
        page = page.replace(f'@{k}@', str(v))
    with open(ROOT / f'{slug(i)}.html', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(page)
    print('OK', slug(i))
