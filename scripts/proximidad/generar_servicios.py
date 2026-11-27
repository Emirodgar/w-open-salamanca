#!/usr/bin/env python3
"""Genera servicios-proximidad-salamanca.json: servicios con coordenadas para la
herramienta /ciudad-15-minutos-salamanca. Solo usa la librería estándar.

Uso (desde la raíz del repo):
    python3 scripts/proximidad/generar_servicios.py

Combina datos que ya publica el portal:
  - salud: centros-salud.json (centros de salud públicos de atención primaria)
  - colegio: centros-educativos-salamanca.json (centros con etapa Infantil o Primaria)
  - parque: capa «Parques y jardines» de la IDE municipal (zonas-verdes.html)
  - biblioteca: capa «Bibliotecas» de la IDE municipal (bibliotecas-municipales-salamanca.html)
  - bus: paradas de lineas-autobus.json (una por referencia de parada)
"""
import json
from datetime import date

BARRA = chr(92)


def carga(n):
    with open(n, encoding="utf8") as f:
        return json.load(f)


def array_js(fichero, nombre):
    """Extrae un array literal `const nombre = [...]` de un HTML y lo parsea como JSON."""
    with open(fichero, encoding="utf8") as f:
        s = f.read()
    ini = s.index("const " + nombre + " = ") + len("const " + nombre + " = ")
    prof, j = 0, ini
    while True:
        c = s[j]
        if c == "[":
            prof += 1
        elif c == "]":
            prof -= 1
            if prof == 0:
                break
        elif c == '"':
            j += 1
            while s[j] != '"':
                if s[j] == BARRA:
                    j += 1
                j += 1
        j += 1
    return json.loads(s[ini:j + 1])


def main():
    servicios = []

    for c in carga("centros-salud.json")["centros"]:
        servicios.append(["salud", c["nombre"], c["lat"], c["lng"]])

    for c in carga("centros-educativos-salamanca.json")["centros"]:
        if c.get("lat") and ("Infantil" in c["etapas"] or "Primaria" in c["etapas"]):
            servicios.append(["colegio", c["nombre"], c["lat"], c["lon"]])

    # [id, nombre, dirección, lat, lng, ...]
    for p in array_js("zonas-verdes.html", "parques"):
        servicios.append(["parque", p[1], p[3], p[4]])

    for b in array_js("bibliotecas-municipales-salamanca.html", "bibliotecas"):
        servicios.append(["biblioteca", b[0], b[2], b[3]] if isinstance(b[2], float) else None)
    servicios = [s for s in servicios if s]

    vistas = set()
    for linea in carga("lineas-autobus.json"):
        for p in linea["paradas"]:
            if p["ref"] in vistas:
                continue
            vistas.add(p["ref"])
            servicios.append(["bus", p["name"], p["lat"], p["lng"]])

    cuenta = {}
    for s in servicios:
        cuenta[s[0]] = cuenta.get(s[0], 0) + 1
    salida = {
        "nota": "Servicios con coordenadas para /ciudad-15-minutos-salamanca. Cada fila es [categoria, nombre, lat, lng].",
        "generado": date.today().isoformat(),
        "categorias": cuenta,
        "servicios": servicios,
    }
    with open("servicios-proximidad-salamanca.json", "w", encoding="utf8") as f:
        json.dump(salida, f, ensure_ascii=False, separators=(",", ":"))
    print(cuenta)


if __name__ == "__main__":
    main()
