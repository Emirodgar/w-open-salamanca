#!/usr/bin/env python3
"""Archiva en este repo lo que Atalaya publica sobre las elecciones.

- elecciones/proximas.json  -> candidaturas y gobierno de Salamanca (provincia 37) de la convocatoria abierta.
- elecciones/encuestas.json -> archivo permanente de sondeos. Solo añade: nunca borra ni pisa uno existente.

Uso:  python scripts/elecciones/snapshot.py
Cuando una convocatoria se celebre, sus resultados por municipio se añaden como un JSON
nuevo en elecciones/ y una entrada en elecciones/index.json; la entrada de proximas.json
se conserva como registro de quién se presentó.
"""
import json, os, urllib.request, datetime

AT = 'https://emirodgar.es/atalaya/data/'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
OUT = os.path.join(ROOT, 'elecciones')
CONVOCATORIA = {
    'id': 'generales-2026-11',
    'tipo': 'Generales (Congreso)',
    'fecha': '2026-11-29',
    'etiqueta': 'Generales, 29 de noviembre de 2026',
}


# Partidos de ámbito autonómico que no concurren en la circunscripción de Salamanca.
# Atalaya los incluye (p. ej. un PNV por Salamanca viene de un error de su fuente): aquí se descartan.
NO_CONCURREN = {'PNV', 'EHB', 'BILDU', 'ERC', 'JUNTS', 'BNG', 'CC', 'UPN', 'COMPROMIS', 'SALF'}


def get(name):
    with urllib.request.urlopen(AT + name, timeout=30) as r:
        return json.loads(r.read().decode('utf8'))


def dump(path, obj):
    with open(path, 'w', encoding='utf8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write('\n')


def load(path, default):
    return json.load(open(path, encoding='utf8')) if os.path.exists(path) else default


hoy = datetime.date.today().isoformat()

# --- candidaturas (se actualizan hasta que se celebre la convocatoria) ---
pol = get('politicos_prov.json')
prov = pol['prov']['37']
p_path = os.path.join(OUT, 'proximas.json')
prox = load(p_path, {'convocatorias': []})
conv = next((c for c in prox['convocatorias'] if c['id'] == CONVOCATORIA['id']), None)
if conv is None:
    conv = dict(CONVOCATORIA, estado='pendiente')
    prox['convocatorias'].append(conv)
if conv.get('estado') == 'pendiente':
    conv['candidaturas'] = [c for c in prov['candidatos'] if c['partido'] not in NO_CONCURREN]
    nac = get('politicos.json')['politicos']
    conv['nacionales'] = [
        {'nombre': x['nombre'], 'partido': x['partidoId'], 'cargo': x.get('cargo'), 'wiki': x.get('wiki')}
        for x in nac if x.get('estado') == 'candidato' and x.get('nombre') and x['partidoId'] not in NO_CONCURREN]
    sanchez = next((x for x in nac if x['id'] == 'pedro-snchez'), None)
    gob = [dict(g) for g in prov['gobierno']]
    if sanchez:
        gob.insert(0, {'rol': 'Presidente del Gobierno de España', 'ambito': 'nacional', 'nombre': sanchez['nombre'],
                       'partido': 'PSOE', 'wiki': sanchez.get('wiki'), 'fuente': 'Atalaya'})
    conv['gobierno'] = gob
    conv['fuente'] = 'Atalaya (emirodgar.es/atalaya): Wikipedia y Wikidata'
    conv['capturado'] = hoy
prox['actualizado'] = hoy
dump(p_path, prox)

# --- encuestas (solo se añaden) ---
e_path = os.path.join(OUT, 'encuestas.json')
arch = load(e_path, {'descripcion': 'Archivo permanente de sondeos. Solo se añaden filas.', 'encuestas': []})
clave = lambda e: '|'.join(str(e.get(k, '')) for k in ('fecha', 'empresa', 'medio', 'ambito', 'convocatoria'))
vistas = {clave(e) for e in arch['encuestas']}
nuevas = 0
for e in get('encuestas.json')['encuestas']:
    if clave(e) not in vistas:
        arch['encuestas'].append({k: e[k] for k in ('fecha', 'empresa', 'medio', 'muestra', 'tipo', 'ambito', 'convocatoria', 'voto') if k in e})
        nuevas += 1
arch['encuestas'].sort(key=lambda e: e['fecha'])
arch['actualizado'] = hoy
dump(e_path, arch)
print('candidaturas:', len(conv.get('candidaturas', [])), '| encuestas nuevas:', nuevas, '| total:', len(arch['encuestas']))
