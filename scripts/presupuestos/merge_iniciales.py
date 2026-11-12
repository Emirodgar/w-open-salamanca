"""Añade a presupuestos-salamanca.json el presupuesto inicial (clave 'inicial') por año.
Uso: python merge_iniciales.py <directorio_con_ini_AAAA.json>"""
import json, sys, collections
W = sys.argv[1]
f = 'presupuestos-salamanca.json'
d = json.load(open(f, encoding='utf8'))
ING = ['impuestos_directos', 'impuestos_indirectos', 'tasas_otros', 'transf_corrientes', 'patrimoniales',
       'enajenacion', 'transf_capital', 'activos_fin', 'pasivos_fin']
GAS = ['personal', 'bienes_servicios', 'financieros', 'transf_corrientes', 'contingencia', 'inversiones',
       'transf_capital', 'activos_fin', 'pasivos_fin']
for y in range(2010, 2025):
    p = json.load(open(f'{W}/ini_{y}.json'))
    g = collections.defaultdict(float); i = collections.defaultdict(float)
    for t, c, v in p['economica']:
        if len(c) == 1:
            (g if t == 'G' else i)[c] += v
    pol = collections.defaultdict(float)
    for k, v in p['funcional']:
        if len(k) == 2:
            pol[k] += v
    tg = sum(g.values()); ti = sum(i.values())
    assert abs(sum(pol.values()) - tg) < 200, y  # Hacienda: +99 EUR en 2012-2014
    d['anios'][str(y)]['inicial'] = {
        'total_gastos': round(tg, 2), 'total_ingresos': round(ti, 2),
        'gastos': {GAS[int(c) - 1]: round(v, 2) for c, v in sorted(g.items())},
        'ingresos': {ING[int(c) - 1]: round(v, 2) for c, v in sorted(i.items())},
        'politicas': {k: round(v, 2) for k, v in sorted(pol.items())}}
d['nota_inicial'] = 'Presupuesto inicial consolidado (créditos y previsiones iniciales, antes de modificaciones). Fuente: CONPREL, fichero de máximo desglose de presupuestos (Access).'
json.dump(d, open(f, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
