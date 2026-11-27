#!/usr/bin/env python3
"""Calcula la renta neta media por persona de cada barrio de Salamanca a partir de
los datos oficiales del INE (Atlas de distribución de renta de los hogares) y la
cartografía de secciones censales del INE. Solo usa la librería estándar.

Uso (desde la raíz del repo, con conexión a internet):
    python3 scripts/renta/generar_renta_barrios_ine.py
    python3 scripts/matcher/generar_barrios_matcher.py   # regenera barrios-matcher.json

Escribe:
  - renta-barrios-ine-2024.json: renta por barrio sobre los límites de barrios-poblacion.json
  - barrios-metricas.json: sustituye el bloque "renta" (límites de barrios-salamanca.json)

Método: cada barrio recibe la media de la renta de las secciones censales que lo
cubren, ponderada por la superficie de solape (rejilla de ~30 m). No pondera por
población. Los límites de barrio son aproximados.
"""
import json
import re
import unicodedata
import urllib.request
from datetime import date

TABLA = 31178                    # INE ADRH, Salamanca (secciones)
ANIO = 2024
MUN = "37274"                    # código INE de Salamanca
BBOX = "-5.75,40.90,-5.58,41.02"
STEP = 0.0003                    # grados de latitud (~33 m)


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"^(la|las|los|el)\s+", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def get(url):
    with urllib.request.urlopen(url, timeout=180) as r:
        return json.load(r)


def renta_secciones():
    datos = get(f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{TABLA}?nult=5&tip=A")
    v = {}
    for x in datos:
        n = x["Nombre"]
        if n.startswith("Salamanca secci") and "Renta neta media por persona" in n and "Dato base" in n:
            cod = n.split("n ")[1][:5]
            for d in x["Data"]:
                if d["Anyo"] == ANIO and d["Valor"] is not None:
                    v[cod] = d["Valor"]
    return v


def poligonos_secciones():
    base = f"https://www.ine.es/geoserver/ogc/features/v1/collections/WMS_INE_SECCIONES_G01:Secciones_{ANIO}/items"
    g = get(f"{base}?f=json&limit=300&bbox={BBOX}")
    out = {}
    for f in g["features"]:
        p = f["properties"]
        if p["CUMUN"] != MUN:
            continue
        geom = f["geometry"]
        coords = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        out[p["CUSEC"][5:]] = [[[(c[1], c[0]) for c in ring] for ring in poly] for poly in coords]
    return out


def pip(lat, lng, ring):
    ins, j = False, len(ring) - 1
    for i in range(len(ring)):
        yi, xi = ring[i]
        yj, xj = ring[j]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            ins = not ins
        j = i
    return ins


def en_multi(lat, lng, multi):
    for poly in multi:
        if pip(lat, lng, poly[0]) and not any(pip(lat, lng, h) for h in poly[1:]):
            return True
    return False


def bbox(multi):
    pts = [c for poly in multi for c in poly[0]]
    return min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)


def renta_barrio(multi, secs, sec_bb, valores):
    la0, la1, lo0, lo1 = bbox(multi)
    acc, n = {}, 0
    la = la0
    while la < la1:
        lo = lo0
        while lo < lo1:
            if en_multi(la, lo, multi):
                n += 1
                for k, m in secs.items():
                    b = sec_bb[k]
                    if b[0] <= la <= b[1] and b[2] <= lo <= b[3] and en_multi(la, lo, m):
                        acc[k] = acc.get(k, 0) + 1
                        break
            lo += STEP * 1.3
        la += STEP
    tot = sum(c for k, c in acc.items() if k in valores)
    if not tot:
        return None
    return round(sum(valores[k] * c for k, c in acc.items() if k in valores) / tot), len(acc)


def main():
    valores = renta_secciones()
    secs = poligonos_secciones()
    sec_bb = {k: bbox(m) for k, m in secs.items()}
    print(len(valores), "secciones con dato;", len(secs), "polígonos")

    # 1) Barrios de barrios-poblacion.json (49) -> renta-barrios-ine-2024.json
    with open("barrios-poblacion.json", encoding="utf8") as f:
        bp = json.load(f)
    pob = {x[0]: x[1] for x in bp["barrios"]}
    barrios = {}
    for nombre, multi in bp["geo"]:
        r = renta_barrio(multi, secs, sec_bb, valores)
        if r:
            barrios[nombre] = {"renta_neta_media_persona": r[0], "secciones_censales": r[1], "habitantes": pob.get(nombre, 0)}
    meta = {
        "titulo": "Renta neta media por persona en los barrios de Salamanca (INE, ADRH %d)" % ANIO,
        "fuente": "INE, Atlas de distribución de renta de los hogares (ADRH), tabla %d (Salamanca, secciones censales), indicador «Renta neta media por persona», año %d" % (TABLA, ANIO),
        "fuente_url": "https://www.ine.es/jaxiT3/Tabla.htm?t=%d" % TABLA,
        "cartografia": "INE, secciones censales %d (geoserver INE, colección Secciones_%d) y límites de barrios de barrios-poblacion.json (aproximados)" % (ANIO, ANIO),
        "metodo": "Cada barrio recibe la media de la renta de las secciones censales que lo cubren, ponderada por la superficie de solape (rejilla de ~30 m). No pondera por población: es una aproximación.",
        "limitaciones": [
            "Los límites de barrio son aproximados y no coinciden exactamente con las secciones censales.",
            "Un barrio con una sola sección toma el valor de esa sección, que puede incluir zonas vecinas.",
            "Marín II, Montalvo, Zaldesa y La Platina no tienen población residente apreciable: su valor es el de la sección que los cubre.",
            "Cuatro secciones (01012, 05016, 05020, 05021) no tienen dato de 2024 en el INE y se ignoran; tampoco hay dato para las secciones agregadas por distrito (xx000).",
        ],
        "generado": date.today().isoformat(),
        "secciones_con_dato": len(valores),
        "unidad": "€/persona/año",
    }
    with open("renta-barrios-ine-2024.json", "w", encoding="utf8") as f:
        json.dump({"metadata": meta, "barrios": barrios}, f, ensure_ascii=False, indent=1)

    # 2) Barrios de barrios-salamanca.json (40, los de mapa y buscador) -> barrios-metricas.json
    with open("barrios-salamanca.json", encoding="utf8") as f:
        osm = json.load(f)["barrios"]
    # Para que el buscador y la página /renta-barrios den la misma cifra, si el barrio
    # existe en barrios-poblacion.json se usa ese valor; si no, se calcula con su polígono.
    por_nombre = {norm(n): v["renta_neta_media_persona"] for n, v in barrios.items()}
    alias = {"montalvos": "montalvo"}
    vals = {}
    for b in osm:
        k = alias.get(norm(b["nombre"]), norm(b["nombre"]))
        if k in por_nombre:
            vals[b["nombre"]] = por_nombre[k]
            continue
        r = renta_barrio([[b["coordenadas"]]], secs, sec_bb, valores)
        if r:
            vals[b["nombre"]] = r[0]
    with open("barrios-metricas.json", encoding="utf8") as f:
        m = json.load(f)
    m["metricas"]["renta"] = {
        "etiqueta": "Renta neta media por persona (INE, %d)" % ANIO,
        "unidad": "€/persona/año",
        "fuente": "/renta-barrios",
        "valores": vals,
    }
    m["nota"] = (
        "La población procede de la capa de indicadores por barrio de la IDE municipal (los barrios sin coincidencia o con menos de 100 habitantes no se colorean). "
        "La renta es la renta neta media por persona de %d del Atlas de distribución de renta de los hogares del INE, agregada desde secciones censales a barrios "
        "(ponderada por superficie; los límites de barrio son aproximados). Los valores de precio de la vivienda proceden del dataset precio-vivienda de este portal "
        "y NO ESTÁN VERIFICADOS: carecen de fuente contrastada." % ANIO
    )
    with open("barrios-metricas.json", "w", encoding="utf8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    print(len(barrios), "barrios (poblacion);", len(vals), "barrios (OSM)")


if __name__ == "__main__":
    main()
