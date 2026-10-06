#!/usr/bin/env python3
"""Envía por Telegram el resumen de actualidad.json.

Uso: TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3 scripts/actualidad/telegram.py

Si faltan las variables, sale sin error (el envío es opcional). Solo usa la
librería estándar de Python.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LIMITE = 4000  # Telegram admite 4096 caracteres por mensaje; margen para el HTML


def main():
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Sin TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID: no se envía nada.")
        return
    datos = json.loads((RAIZ / "actualidad.json").read_text(encoding="utf-8"))
    p = datos.get("periodo_cubierto") or {}
    titulo = "Actualidad de Salamanca"
    if p.get("desde") and p.get("hasta"):
        titulo += f" ({p['desde']} a {p['hasta']})"

    pie = '<a href="https://opensalamanca.es/actualidad">Ver la actualidad completa</a>'
    mensajes = partir(f"<b>{escape(titulo)}</b>", [escape(x) for x in datos["resumen"].split("\n\n") if x.strip()], pie)
    try:
        for texto in mensajes:
            enviar(token, chat, texto)
        print(f"Resumen enviado por Telegram en {len(mensajes)} mensaje(s).")
    except urllib.error.HTTPError as e:
        # No se imprime la URL (lleva el token); solo el motivo que da Telegram.
        sys.exit(f"Telegram rechazó el mensaje: HTTP {e.code} {e.read().decode('utf-8', 'replace')[:300]}")


def trocear(parrafo):
    """Parte un párrafo que por sí solo excede el límite, por frases y, si hace falta, por palabras."""
    trozos, actual = [], ""
    for palabra in parrafo.split(" "):
        while len(palabra) > LIMITE:  # "palabra" absurdamente larga: corte duro
            trozos.append(palabra[:LIMITE])
            palabra = palabra[LIMITE:]
        if actual and len(actual) + 1 + len(palabra) > LIMITE:
            trozos.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}" if actual else palabra
    return trozos + [actual]


def partir(titulo, parrafos, pie):
    """Agrupa párrafos en mensajes de hasta LIMITE caracteres sin cortar ninguno por la mitad
    (salvo que un párrafo solo ya sea más largo). El título va en el primero y el enlace en el último."""
    piezas = []
    for p in parrafos:
        piezas += trocear(p) if len(p) > LIMITE else [p]
    mensajes, actual = [], titulo
    for p in piezas:
        if len(actual) + 2 + len(p) > LIMITE:
            mensajes.append(actual)
            actual = p
        else:
            actual += "\n\n" + p
    if len(actual) + 2 + len(pie) > LIMITE:
        mensajes.append(actual)
        actual = pie
    else:
        actual += "\n\n" + pie
    mensajes.append(actual)
    return mensajes


def enviar(token, chat, texto):
    datos = urllib.parse.urlencode({
        "chat_id": chat, "text": texto, "parse_mode": "HTML", "disable_web_page_preview": "true",
    }).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", datos, timeout=30)


if __name__ == "__main__":
    main()
