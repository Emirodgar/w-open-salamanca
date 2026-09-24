---
name: hemeroteca
description: >
  Actualiza `hemeroteca.json` (raíz del repo), que alimenta
  `hemeroteca.html`, con las noticias de los últimos 20 días de la prensa
  local de Salamanca (Tribuna Salamanca, Salamanca24Horas, La Gaceta de
  Salamanca y Salamancahoy). Es un proceso puramente mecánico: solo
  recopila título, fecha, medio y enlace desde los sitemaps/RSS de cada
  medio, sin resumir ni analizar el contenido. Al terminar, hace commit y
  push automáticamente si hay cambios. Úsala SIEMPRE que el usuario pida
  "actualiza la hemeroteca", "refresca hemeroteca.json", "recopila las
  últimas noticias de la prensa local", o cualquier variación sobre
  refrescar el listado de noticias de `/hemeroteca` — aunque no mencionen
  el nombre del fichero explícitamente. También se ejecuta sola cada día a
  las 7:00 (hora de Madrid) vía `.github/workflows/hemeroteca.yml`.
---

# Hemeroteca de prensa local (opensalamanca.es)

## Qué hace

1. Ejecuta el script determinista que ya recopila las noticias:

   ```bash
   node scripts/hemeroteca/build.mjs
   ```

   Este script descarga los sitemaps/RSS de las cuatro fuentes definidas
   en `FUENTES` (dentro del propio script), se queda con las noticias de
   los últimos 20 días (`DIAS_VENTANA`), resuelve el título cuando el
   sitemap no lo trae (pide `og:title`/`<title>` a la página real), y
   sobrescribe `hemeroteca.json` en la raíz del repo. Conserva del fichero
   anterior cualquier noticia que siga dentro de la ventana aunque el
   medio ya no la liste en su sitemap.

2. **No hay ningún paso de curación editorial aquí** (a diferencia de la
   skill `sitemap-mapa-calor-tematico`): no resumas, no reclasifiques ni
   reescribas títulos — el script ya hace todo el trabajo de contenido.
   Tu única responsabilidad además de ejecutarlo es el commit (paso
   siguiente).

3. Comprueba si `hemeroteca.json` ha cambiado (`git diff --quiet --
   hemeroteca.json`). Si no ha cambiado, no hagas commit ni push: informa
   de que no había noticias nuevas y termina.

## Commit y push automáticos al terminar

Igual que `sitemap-mapa-calor-tematico`, esta skill sí debe terminar
haciendo commit y push por su cuenta, sin pedir confirmación en el chat —
instrucción permanente del usuario específica de esta skill.

1. `git add hemeroteca.json` (solo ese fichero; el script no toca ningún
   otro).
2. Commit con un mensaje breve, p.ej. `Actualiza hemeroteca.json`.
3. `git push` a la rama actual contra `origin`. No uses `--force` ni
   `--no-verify`; si el push falla, no lo resuelvas forzando — informa del
   fallo.

## Limitaciones a comunicar siempre que sean relevantes

- Si un sitemap no responde (timeout de 10s) el script sigue con las
  demás fuentes y solo avisa por `console.error`; una fuente caída
  puntualmente no es un fallo del proceso completo.
- El título que ve el usuario puede venir del propio slug de la URL como
  último recurso (`tituloDesdeSlug`) si ni el sitemap ni la página traen
  uno mejor — no es un resumen, es una aproximación mecánica.
