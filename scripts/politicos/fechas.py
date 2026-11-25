"""Fechas de generación comunes a los scripts de fichas y votaciones.

Todas las fichas llevan la fecha del día en que se regeneran (no una fecha
fija), de modo que el workflow semanal las mantiene al día.
"""
import re
from datetime import date
from pathlib import Path

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
HOY = date.today()


def iso():
    return HOY.isoformat()


def dmy():
    return f"{HOY.day:02d}-{HOY.month:02d}-{HOY.year}"


def largo():
    return f"{HOY.day} de {MESES[HOY.month - 1]} de {HOY.year}"


def anio():
    return str(HOY.year)


def tocar_modified(ruta):
    """Actualiza la línea `modified:` del front matter de una página estática."""
    p = Path(ruta)
    with open(p, encoding="utf-8", newline="") as f:
        s = f.read()
    n = re.sub(r"(?m)^modified: .*$", f"modified: {dmy()}", s, count=1)
    if n != s:
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(n)
