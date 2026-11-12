"""Extrae el gasto por política (2 dígitos) de todos los ayuntamientos grandes de CONPREL.

Uso: python extract_ciudades.py <directorio_trabajo> <año> [<año> ...]
Requiere: pip install access-parser
Por año guarda <directorio_trabajo>/ciudades_<año>.json con, para cada ayuntamiento
(entidad principal AA000) de al menos MIN_POB habitantes: nombre, población, gasto
total y gasto por política (obligaciones reconocidas netas, presupuesto consolidado).
"""
import json, os, subprocess, sys, zipfile, shutil, collections
from access_parser import AccessParser

MIN_POB = 50000
URL = ('https://serviciostelematicosext.hacienda.gob.es/SGFAL/CONPREL/Consulta/DescargaFichero'
       '?CCAA=&TipoDato=Liquidaciones&Ejercicio={y}&TipoPublicacion=Access')


def procesa(work, y):
    out = os.path.join(work, f'ciudades_{y}.json')
    if os.path.exists(out):
        return
    d = os.path.join(work, f'c{y}')
    os.makedirs(d, exist_ok=True)
    z = os.path.join(d, 'f.zip')
    subprocess.run(['curl', '-sL', '-m', '900', '-o', z, URL.format(y=y)], check=True)
    with zipfile.ZipFile(z) as zf:
        nombre = next(n for n in zf.namelist() if n.lower().endswith(('.accdb', '.mdb')))
        zf.extract(nombre, d)
    db = AccessParser(os.path.join(d, nombre))
    inv = db.parse_table('tb_inventario')
    sel = {}
    for i in range(len(inv['id'])):
        cod = inv['codente'][i].strip()
        if inv['id'][i] == inv['idente'][i] and cod.endswith('AA000') and float(inv['poblacion'][i]) >= MIN_POB:
            sel[inv['id'][i]] = {'cod': cod[:5], 'nombre': inv['nombreente'][i].strip(),
                                 'pob': int(float(inv['poblacion'][i])), 'pol': collections.defaultdict(float), 'total': 0.0}
    tb = db.parse_table('tb_funcional_cons')
    for i in range(len(tb['id'])):
        e = sel.get(tb['id'][i])
        if e is None:
            continue
        prog = tb['cdfgr'][i].strip()
        v = float(tb['importe'][i])
        if len(prog) == 1:
            e['total'] += v
        elif len(prog) == 2:
            e['pol'][prog] += v
    res = {}
    for e in sel.values():
        if e['total'] > 0:
            res[e['cod']] = {'nombre': e['nombre'], 'pob': e['pob'], 'total': round(e['total'], 2),
                             'pol': {k: round(v, 2) for k, v in sorted(e['pol'].items())}}
    json.dump({'anio': y, 'ciudades': res}, open(out, 'w', encoding='utf8'), ensure_ascii=False)
    shutil.rmtree(d, ignore_errors=True)
    print(y, 'ok', len(res), flush=True)


if __name__ == '__main__':
    work = sys.argv[1]
    os.makedirs(work, exist_ok=True)
    for y in sys.argv[2:]:
        try:
            procesa(work, int(y))
        except Exception as e:
            print(y, 'ERROR', repr(e), flush=True)
