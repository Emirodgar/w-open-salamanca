#!/usr/bin/env bash
# Regenera votaciones, fichas e índice a partir de lo ya descargado.
# Uso: scripts/politicos/regenerar.sh CARPETA_CACHE_ACTAS   (opcional: FECHA_GENERACION=AAAA-MM-DD)
set -euo pipefail
cache="$1"
python3 scripts/politicos/pleno/parse_actas.py "$cache" > /dev/null
python3 scripts/politicos/pleno/build_pleno.py
python3 scripts/politicos/build_carbayo.py > /dev/null
python3 scripts/politicos/build_concejales.py
