"""Añade a presupuestos-salamanca.json el gasto por política de gasto (2 dígitos) y capítulo.
Uso: python merge_programas.py <directorio_con_programas_AAAA.json>"""
import json, sys, collections
W = sys.argv[1]
f = 'presupuestos-salamanca.json'
d = json.load(open(f, encoding='utf8'))
NOMBRES = {'01': 'Deuda pública', '13': 'Seguridad y movilidad ciudadana', '15': 'Vivienda y urbanismo',
           '16': 'Bienestar comunitario (limpieza, agua, alumbrado, cementerios)', '17': 'Medio ambiente',
           '21': 'Pensiones', '22': 'Otras prestaciones a empleados', '23': 'Servicios sociales y promoción social',
           '24': 'Fomento del empleo', '31': 'Sanidad', '32': 'Educación', '33': 'Cultura', '34': 'Deporte',
           '43': 'Comercio, turismo y pymes', '44': 'Transporte público', '45': 'Infraestructuras',
           '49': 'Otras actuaciones económicas', '91': 'Órganos de gobierno',
           '92': 'Servicios de carácter general', '93': 'Administración financiera y tributaria'}
d['politicas'] = NOMBRES
CAP = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
for y in range(2010, 2025):
    p = json.load(open(f'{W}/programas_{y}.json', encoding='utf8'))
    acc = collections.defaultdict(lambda: [0.0] * 9)
    for prog, cta, v in p['filas']:
        if len(prog) == 2:
            acc[prog][CAP.index(cta[:1])] += v
    tot = sum(sum(v) for v in acc.values())
    assert abs(tot - d['anios'][str(y)]['total_gastos']) < 5, y
    d['anios'][str(y)]['politicas'] = {k: [round(sum(v), 2), [round(x, 2) for x in v]] for k, v in sorted(acc.items())}
d['nota_politicas'] = 'Gasto por política de gasto (clasificación por programas, 2 dígitos) y capítulo económico 1 a 9. Fuente: CONPREL, fichero de máximo desglose (Access).'
json.dump(d, open(f, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
