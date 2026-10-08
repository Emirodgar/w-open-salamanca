# actualidad-trigger

Disparador externo de los workflows diarios de actualización (lista en la
constante `JOBS` de `src/index.js`: actualidad de opensalamanca.es, hemeroteca
de w-emirodgar-es y tendencias de w-mejor-imposible). GitHub
Actions pierde a veces los avisos de `schedule`; este Worker, con cron de
Cloudflare, lanza el workflow (`workflow_dispatch`) a las 05:45, 07:45 y
09:45 UTC **solo si hoy (hora de Madrid) aún no hay commit de su fichero de control**
(`comprobar` en `JOBS`), ya son las 7:00 en Madrid y no hay una ejecución en curso. Así no duplica trabajo
cuando el cron de GitHub sí ha funcionado.

## Puesta en marcha (una vez)

1. Crea un token en GitHub: Settings → Developer settings → Fine-grained
   tokens → repositorios `w-open-salamanca`, `w-emirodgar-es` y `w-mejor-imposible` → permisos de
   repositorio **Actions: Read and write** y **Contents: Read-only**
   (caducidad larga; ponte un recordatorio para renovarlo).
2. Despliega:
   ```bash
   cd cloudflare-worker/actualidad-trigger
   npx wrangler deploy
   npx wrangler secret put GITHUB_TOKEN    # pega el token
   npx wrangler secret put TRIGGER_KEY     # opcional: clave para probar por GET
   ```
3. Prueba: `https://actualidad-trigger.<tu-subdominio>.workers.dev/?clave=<TRIGGER_KEY>`
   responde "Ya actualizado hoy…" o lanza el workflow. Los disparos
   programados se ven en Cloudflare → Workers → actualidad-trigger → Logs.

## Añadir otro workflow

Añade una entrada a `JOBS` en `src/index.js` (repo, workflow, rama, fichero de
control que solo ese workflow commitea), incluye el repo en el token y vuelve a
desplegar. El workflow debe tener `workflow_dispatch:` en su `on:`.
Las variables `REPO`, `WORKFLOW` y `REF` de versiones anteriores ya no se usan
y se pueden borrar del panel.
