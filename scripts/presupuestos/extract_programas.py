"""Extrae el gasto de Salamanca por programa y capítulo económico de CONPREL (Access).

Uso: python extract_programas.py <directorio_trabajo> <año> [<año> ...]
Requiere: pip install access-parser
Por cada año descarga el ZIP del Ministerio de Hacienda, lee tb_funcional_cons
(presupuesto consolidado, obligaciones reconocidas netas), guarda un JSON pequeño
en <directorio_trabajo>/programas_<año>.json y borra los ficheros grandes.
"""
import json, os, subprocess, sys, zipfile, shutil
from access_parser import AccessParser

COD = '37274AA000'  # Ayuntamiento de Salamanca (consolidado)
URL = ('https://serviciostelematicosext.hacienda.gob.es/SGFAL/CONPREL/Consulta/DescargaFichero'
       '?CCAA=&TipoDato=Liquidaciones&Ejercicio={y}&TipoPublicacion=Access')


def procesa(work, y):
    out = os.path.join(work, f'programas_{y}.json')
    if os.path.exists(out):
        return
    d = os.path.join(work, f'a{y}')
    os.makedirs(d, exist_ok=True)
    z = os.path.join(d, 'f.zip')
    subprocess.run(['curl', '-sL', '-m', '900', '-o', z, URL.format(y=y)], check=True)
    with zipfile.ZipFile(z) as zf:
        nombre = next(n for n in zf.namelist() if n.lower().endswith(('.accdb', '.mdb')))
        zf.extract(nombre, d)
    db = AccessParser(os.path.join(d, nombre))
    inv = db.parse_table('tb_inventario')
    sid = next(inv['id'][i] for i in range(len(inv['id'])) if inv['codente'][i].strip() == COD)
    pr = db.parse_table('tb_cuentasProgramas')
    nombres = {pr['cdfgr'][i].strip(): pr['nombre'][i].strip() for i in range(len(pr['cdfgr']))}
    tb = db.parse_table('tb_funcional_cons')
    filas = [[tb['cdfgr'][i].strip(), tb['cdcta'][i].strip(), float(tb['importe'][i])]
             for i in range(len(tb['id'])) if tb['id'][i] == sid]
    json.dump({'anio': y, 'nombres': nombres, 'filas': filas}, open(out, 'w', encoding='utf8'),
              ensure_ascii=False)
    shutil.rmtree(d, ignore_errors=True)
    print(y, 'ok', len(filas), flush=True)


if __name__ == '__main__':
    work = sys.argv[1]
    os.makedirs(work, exist_ok=True)
    for y in sys.argv[2:]:
        try:
            procesa(work, int(y))
        except Exception as e:  # sigue con el siguiente año
            print(y, 'ERROR', repr(e), flush=True)
