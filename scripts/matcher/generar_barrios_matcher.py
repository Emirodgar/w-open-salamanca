#!/usr/bin/env python3
"""Genera barrios-matcher.json: una ficha con indicadores por barrio para el
buscador de barrios (/barrio-ideal). Solo usa la librería estándar.

Uso (desde la raíz del repo):
    python3 scripts/matcher/generar_barrios_matcher.py

Combina datos que ya publica el portal: límites (barrios-salamanca.json),
población y edades (barrios-poblacion.json), renta y precio de vivienda
(barrios-metricas.json, NO verificados), paradas de bus (paradas-bus.json),
centros de salud (centros-salud.json) y sedes universitarias (coordenadas de
la IDE, las mismas de /centros-universitarios-salamanca).
"""
import json
import math
import re
import unicodedata
from datetime import date

MIN_HABITANTES = 500  # por debajo, los ratios de edad y densidad no son fiables

PLAZA_MAYOR = (40.96505, -5.66378)
# Sedes universitarias de la IDE municipal (lat, lon), ver centros-universitarios-salamanca.html
SEDES_UNI = [
    (40.98276429, -5.66156662), (40.96580832, -5.67713413), (40.9724592, -5.67700804),
    (40.96497467, -5.67605439), (40.96848862, -5.6803525), (40.96782321, -5.68066848),
    (40.96776854, -5.67788026), (40.96490392, -5.67790395), (40.96062699, -5.67044384),
    (40.9591685, -5.65973538), (40.96183829, -5.66651301), (40.96102172, -5.66717844),
    (40.96302415, -5.66622339), (40.96276734, -5.66798226),
]


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"^(la|las|los|el)\s+", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def carga(n):
    with open(n, encoding="utf8") as f:
        return json.load(f)


def metros(a, b):
    r = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def main():
    poligonos = carga("barrios-salamanca.json")["barrios"]
    metricas = carga("barrios-metricas.json")["metricas"]
    pob = {norm(b[0]): b for b in carga("barrios-poblacion.json")["barrios"]}
    paradas = carga("paradas-bus.json")
    salud = [(c["lat"], c["lng"]) for c in carga("centros-salud.json")["centros"]]

    bus = {}
    for p in paradas:
        d = bus.setdefault(norm(p[2]), {"paradas": 0, "lineas": set()})
        d["paradas"] += 1
        d["lineas"].update(p[1])

    # El portal usa "Montalvos" en los límites y "Montalvo" en población: norm() no los une
    alias = {"montalvos": "montalvo"}

    barrios, excluidos = [], []
    for b in poligonos:
        nombre = b["nombre"]
        k = alias.get(norm(nombre), norm(nombre))
        fila = pob.get(k)
        if not fila or fila[1] < MIN_HABITANTES:
            excluidos.append(nombre)
            continue
        _, hab, h0, h15, h65, _, _, km2 = fila
        coords = b["coordenadas"]
        c = (sum(p[0] for p in coords) / len(coords), sum(p[1] for p in coords) / len(coords))
        bd = bus.get(k, {"paradas": 0, "lineas": set()})
        barrios.append({
            "nombre": nombre,
            "habitantes": hab,
            "km2": km2,
            "densidad": round(hab / km2) if km2 else None,
            "pct_0_14": round(100 * h0 / hab, 1),
            "pct_65": round(100 * h65 / hab, 1),
            "paradas": bd["paradas"],
            "lineas": len(bd["lineas"]),
            "renta": metricas["renta"]["valores"].get(nombre),
            "vivienda": metricas["vivienda"]["valores"].get(nombre),
            "dist_centro_m": round(metros(c, PLAZA_MAYOR)),
            "dist_salud_m": round(min(metros(c, s) for s in salud)),
            "dist_univ_m": round(min(metros(c, s) for s in SEDES_UNI)),
        })

    salida = {
        "nota": "Indicadores por barrio para el buscador /barrio-ideal. Las distancias se miden en línea recta desde el centro aproximado del barrio (media de los vértices de su límite, que es aproximado). La renta y el precio de la vivienda NO ESTÁN VERIFICADOS (ver /renta-barrios y /precio-vivienda). Solo se incluyen barrios con 500 habitantes o más.",
        "generado": date.today().isoformat(),
        "excluidos": excluidos,
        "barrios": sorted(barrios, key=lambda x: x["nombre"]),
    }
    with open("barrios-matcher.json", "w", encoding="utf8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    print(len(barrios), "barrios;", "excluidos:", ", ".join(excluidos))


if __name__ == "__main__":
    main()
