"""Genera presupuestos-ciudades.json a partir de ciudades_AAAA.json.
Uso: python merge_ciudades.py <directorio_con_ciudades_AAAA.json>"""
import json, sys
W = sys.argv[1]
ANIOS = list(range(2010, 2025))
datos = {y: json.load(open(f'{W}/ciudades_{y}.json', encoding='utf8'))['ciudades'] for y in ANIOS}
base = json.load(open('presupuestos-salamanca.json', encoding='utf8'))
cods = sorted(datos[2024])  # ciudades de >=50.000 hab. en 2024
pols = base['politicas']
out = {'fuente': 'Ministerio de Hacienda, CONPREL: liquidaciones de presupuestos de entidades locales (ayuntamientos de más de 50.000 habitantes en 2024; presupuesto consolidado, obligaciones reconocidas netas). Fichero de máximo desglose (Access).',
       'unidad': 'euros', 'anios': ANIOS, 'politicas': pols, 'ipc_base2021': base['ipc_base2021'], 'ciudades': {}}
for c in cods:
    e24 = datos[2024][c]
    ent = {'n': e24['nombre'], 'pob': [], 'tot': [], 'p': {k: [] for k in pols}}
    for y in ANIOS:
        e = datos[y].get(c)
        ent['pob'].append(e['pob'] if e else None)
        ent['tot'].append(round(e['total']) if e else None)
        for k in pols:
            ent['p'][k].append(round(e['pol'].get(k, 0)) if e else None)
    ent['p'] = {k: v for k, v in ent['p'].items() if any(x for x in v)}
    out['ciudades'][c] = ent
json.dump(out, open('presupuestos-ciudades.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print(len(cods), 'ciudades')
