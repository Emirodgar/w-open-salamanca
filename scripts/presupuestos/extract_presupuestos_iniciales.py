"""Extrae el presupuesto INICIAL consolidado de Salamanca (CONPREL, fichero Access).

Uso: python extract_presupuestos_iniciales.py <directorio_trabajo> <año> [<año> ...]
Requiere: pip install access-parser
Guarda <directorio_trabajo>/ini_<año>.json con las filas de tb_funcional_cons
(programa x capítulo de gasto) y de tb_economica_cons (ingresos y gastos por
cuenta económica) de la entidad 37274AA000, y borra los ficheros pesados.
"""
import json, os, subprocess, sys, zipfile, shutil
from access_parser import AccessParser

COD = '37274AA000'
URL = ('https://serviciostelematicosext.hacienda.gob.es/SGFAL/CONPREL/Consulta/DescargaFichero'
       '?CCAA=&TipoDato=Presupuestos&Ejercicio={y}&TipoPublicacion=Access')


def procesa(work, y):
    out = os.path.join(work, f'ini_{y}.json')
    if os.path.exists(out):
        return
    d = os.path.join(work, f'p{y}')
    os.makedirs(d, exist_ok=True)
    z = os.path.join(d, 'f.zip')
    subprocess.run(['curl', '-sL', '-m', '900', '-o', z, URL.format(y=y)], check=True)
    with zipfile.ZipFile(z) as zf:
        nombre = next(n for n in zf.namelist() if n.lower().endswith(('.accdb', '.mdb')))
        zf.extract(nombre, d)
    db = AccessParser(os.path.join(d, nombre))
    inv = db.parse_table('tb_inventario')
    sid = next(inv['id'][i] for i in range(len(inv['id'])) if inv['codente'][i].strip() == COD)
    fun = db.parse_table('tb_funcional_cons')
    f = [[fun['cdfgr'][i].strip(), float(fun['importe'][i])]
         for i in range(len(fun['id'])) if fun['id'][i] == sid]
    eco = db.parse_table('tb_economica_cons')
    e = [[eco['tipreig'][i].strip(), eco['cdcta'][i].strip(), float(eco['importe'][i])]
         for i in range(len(eco['id'])) if eco['id'][i] == sid]
    json.dump({'anio': y, 'funcional': f, 'economica': e}, open(out, 'w', encoding='utf8'))
    shutil.rmtree(d, ignore_errors=True)
    print(y, 'ok', len(f), len(e), flush=True)


if __name__ == '__main__':
    work = sys.argv[1]
    os.makedirs(work, exist_ok=True)
    for y in sys.argv[2:]:
        try:
            procesa(work, int(y))
        except Exception as ex:
            print(y, 'ERROR', repr(ex), flush=True)
