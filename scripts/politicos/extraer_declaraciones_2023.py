#!/usr/bin/env python3
"""Extrae cifras agregadas de la declaración de bienes inicial de 2023 (Corporación 2023-2027)
de cada concejal, a partir de los PDF que el Ayuntamiento enlaza en su ficha oficial.

Es un proceso puntual (el documento de 2023 ya no cambia): el resultado se versiona en
scripts/politicos/fuentes/declaraciones_2023.json y lo leen build_carbayo.py y build_concejales.py.
Los PDF tienen tablas con columnas desalineadas al convertirlos a texto, así que solo se extrae
lo que se puede comprobar de forma fiable: nº de inmuebles con valor catastral y su suma, categorías
de patrimonio mobiliario declaradas (sin importes: mezclan euros y nº de acciones), nº de vehículos
y suma de deudas. Los importes del texto de los PDF no se reescriben.

Uso:  PYTHONUTF8=1 python3 scripts/politicos/extraer_declaraciones_2023.py CARPETA_TEMPORAL
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FICHAS = ROOT / "fuentes" / "fichas_oficiales.json"
OUT = ROOT / "fuentes" / "declaraciones_2023.json"
TITULO = re.compile(r"Inicial|Final 20\d\d-2023")

NUM = re.compile(
    r"(?<![\d.,/])("
    r"\d{1,3}(?:\.\d{3})+(?:,\d{2})?"      # 40.070 / 178.456,35
    r"|\d+,\d{2}"                          # 691,00 / 53,08
    r"|\d{3,}"                             # 98577 (solo con € o EUR, ver abajo)
    r")(?!\d)(\s*(?:€|EUR))?"
)


def a_float(s):
    return float(s.replace(".", "").replace(",", "."))


def importes(txt):
    """Importes en euros de un bloque de texto, descartando %, m2, fechas y nº de acciones."""
    out = []
    for m in NUM.finditer(txt):
        num, eur = m.group(1), m.group(2)
        resto = txt[m.end():m.end() + 14].lower()
        if re.match(r"\s*(m2|m²|metros|acc|partic|%)", resto) or resto.lstrip().startswith("dm"):
            continue
        v = a_float(num)
        con_miles = bool(re.search(r"\.\d{3}", num))
        con_dec = "," in num
        if eur is None and not con_miles and not (con_dec and v > 100):
            continue                      # entero sin símbolo ni miles: año, % o nº
        if eur is None and con_dec and not con_miles and v <= 100:
            continue                      # 33,33 / 6,25: porcentajes
        if 1900 <= v <= 2100 and not con_dec and not con_miles:
            continue
        out.append(v)
    return out


def secciones(parte2):
    """Trocea la parte II por los epígrafes 3 a 7."""
    pat = re.compile(r"(?m)^\s*([3-7])\.\s*-?\s*(PATRIMONIO INMOBILIARIO|PATRIMONIO MOBILIARIO|VEH[ÍI]CULOS|OTROS BIENES|DEUDAS)")
    ms = list(pat.finditer(parte2))
    res = {}
    for i, m in enumerate(ms):
        fin = ms[i + 1].start() if i + 1 < len(ms) else len(parte2)
        cuerpo = parte2[m.end():fin]
        cuerpo = re.split(r"En Salamanca a", cuerpo)[0]
        res[m.group(1)] = cuerpo
    return res


def analizar(txt):
    if len(txt.strip()) < 200:
        return {"estado": "pdf_escaneado_sin_texto"}
    m = re.search(r"Fecha de presentaci[oó]n:\s*([^\n.]+)", txt)
    f = re.search(r"En Salamanca a\s+(\d+ de \w+ de \d{4})", txt)
    partes = re.split(r"II\.\s*-\s*DECLARACI[ÓO]N DE BIENES PATRIMONIALES", txt)
    if len(partes) < 2:
        return {"estado": "formato_no_reconocido"}
    parte1, parte2 = partes[0], partes[1]
    S = secciones(parte2)
    nada = lambda s: bool(re.search(r"Nada que declarar", s or "", re.I))
    inm = S.get("3", "")
    vals = [] if nada(inm) else importes(inm.split("(1) Clase")[0])
    mob = S.get("4", "")
    cats = []
    if not nada(mob):
        if re.search(r"Acciones", mob):
            cats.append("acciones y participaciones")
        if re.search(r"Seguros de vida|planes de\s+pensiones|pensiones", mob):
            cats.append("seguros de vida, planes de pensiones o rentas")
        if re.search(r"Dep[óo]sitos|Cuentas", mob):
            cats.append("depósitos y cuentas")
        if not cats and len(mob.strip()) > 20:
            cats.append("otros (ver documento)")
    veh = S.get("5", "")
    nveh = 0 if nada(veh) else len(re.findall(r"Turismo|SUV|Motocicleta|Ciclomotor|Furgoneta|Cami[óo]n|Todoterreno|Tractor|Quad|Remolque|Embarcaci", veh))
    otros = S.get("6", "")
    deu = S.get("7", "")
    dvals = [] if nada(deu) else importes(deu)
    # Actividades e incompatibilidades (parte I): ¿alguna entidad declarada?
    act = parte1.split("3. CAUSAS")[-1] if "3. CAUSAS" in parte1 else ""
    return {
        "estado": "ok",
        "tipo_documento": "Final 2019-2023 e inicial 2023-2027" if re.search(r"FINAL CORPORACI[ÓO]N 2019-2023|FINAL 20\d\d-2023", txt) else "Inicial 2023-2027",
        "fecha_presentacion": m.group(1).strip() if m else None,
        "fecha_publicacion_secretario": f.group(1) if f else None,
        "inmuebles": {"declara": bool(vals), "n_con_valor": len(vals), "valores_catastrales_eur": vals,
                      "suma_valores_catastrales_eur": round(sum(vals), 2)},
        "mobiliario": {"declara": bool(cats), "categorias": cats},
        "vehiculos": {"n": nveh},
        "otros_bienes": {"declara": not nada(otros) and len(otros.strip()) > 25},
        "deudas": {"declara": bool(dvals), "n": len(dvals), "importes_eur": dvals, "suma_eur": round(sum(dvals), 2)},
        "_actividades_texto": re.sub(r"\s+", " ", act)[:600],
    }


def main(tmp):
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    d = json.loads(FICHAS.read_text(encoding="utf-8"))
    res = {}
    for k, v in d["fichas"].items():
        cand = [x for x in v["declaraciones"] if TITULO.search(x["titulo"])]
        if not cand:
            res[v["url"]] = {"nombre": v["nombre_oficial"], "estado": "sin_documento_inicial_2023"}
            continue
        x = cand[0]
        base = re.sub(r"\W+", "_", k)[:50]
        pdf, txt = tmp / f"{base}.pdf", tmp / f"{base}.txt"
        if not pdf.exists():
            subprocess.run(["curl", "-s", "-L", "-A", "Mozilla/5.0", "-o", str(pdf), x["url"]], check=True)
        subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", str(pdf), str(txt)], check=True)
        r = analizar(txt.read_text(encoding="utf-8"))
        r.update({"nombre": v["nombre_oficial"], "titulo_documento": x["titulo"], "url_documento": x["url"].split("?")[0]})
        res[v["url"]] = r
        print(r["estado"], v["nombre_oficial"], r.get("inmuebles", {}).get("n_con_valor"), r.get("inmuebles", {}).get("suma_valores_catastrales_eur"),
              r.get("vehiculos", {}).get("n"), r.get("mobiliario", {}).get("categorias"), r.get("deudas", {}).get("importes_eur"))
    OUT.write_text(json.dumps({"fuente": "Ayuntamiento de Salamanca, declaraciones de bienes y actividades (final 2019-2023 / inicial 2023-2027)", "por_ficha": res},
                              ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
