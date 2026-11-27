#!/usr/bin/env python3
"""Descarga del INE (Atlas de distribución de renta de los hogares, ADRH) las series
2015-2024 de Salamanca capital y escribe renta-salamanca-ine.json. Solo usa la
librería estándar.

Uso (desde la raíz del repo, con conexión a internet):
    python3 scripts/renta/generar_renta_salamanca_ine.py

Tablas del INE usadas:
  - 31178: indicadores de renta media y mediana (secciones, distritos y municipio de Salamanca)
  - 31180: población por debajo de umbrales fijos de ingresos, por sexo
  - 31183: población por debajo/encima de umbrales relativos (% de la mediana), por sexo
"""
import json
import re
import urllib.request
from datetime import date

NULT = 12


def get(tabla):
    url = f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{tabla}?nult={NULT}&tip=A"
    with urllib.request.urlopen(url, timeout=300) as r:
        return json.load(r)


def serie(x):
    return {str(d["Anyo"]): d["Valor"] for d in x["Data"] if d["Valor"] is not None}


def main():
    out = {"renta": {}, "umbrales_fijos": {}, "umbrales_relativos": {}}

    for x in get(31178):
        n = x["Nombre"]
        if n.startswith("Salamanca. Dato base."):
            out["renta"][n.split("Dato base. ")[1].strip(" .")] = serie(x)

    # «Salamanca. Hombres. Población con ingresos por unidad de consumo por debajo 60% de la mediana. Dato base.»
    for tabla, clave in ((31180, "umbrales_fijos"), (31183, "umbrales_relativos")):
        for x in get(tabla):
            m = re.match(r"Salamanca\. (Total|Hombres|Mujeres)\. Población con ingresos por unidad de consumo por (.+?)\. Dato base", x["Nombre"])
            if m:
                out[clave].setdefault(m.group(2), {})[m.group(1)] = serie(x)

    salida = {
        "metadata": {
            "titulo": "Renta y distribución de ingresos en Salamanca capital, 2015-2024 (INE, ADRH)",
            "fuente": "INE, Atlas de distribución de renta de los hogares (ADRH): tablas 31178, 31180 y 31183, municipio de Salamanca",
            "fuente_url": "https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177088&menu=ultiDatos&idp=1254735976608",
            "unidad_renta": "euros por año (renta neta media por persona y por hogar)",
            "unidad_umbrales": "% de la población (por sexo) con ingresos por unidad de consumo por debajo o por encima del umbral",
            "nota": "El ADRH no publica la renta media por sexo: solo el porcentaje de hombres y de mujeres por debajo o por encima de umbrales de ingresos por unidad de consumo del hogar.",
            "generado": date.today().isoformat(),
        },
        **out,
    }
    with open("renta-salamanca-ine.json", "w", encoding="utf8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
    print({k: len(v) for k, v in out.items()})


if __name__ == "__main__":
    main()
