# actualidad-trigger

Disparador externo del workflow `.github/workflows/actualidad.yml`. GitHub
Actions pierde a veces los avisos de `schedule`; este Worker, con cron de
Cloudflare, lanza el workflow (`workflow_dispatch`) a las 05:45, 07:45 y
09:45 UTC **solo si hoy (hora de Madrid) aún no hay commit de
`actualidad.json`** y no hay ya una ejecución en curso. Así no duplica trabajo
cuando el cron de GitHub sí ha funcionado.

## Puesta en marcha (una vez)

1. Crea un token en GitHub: Settings → Developer settings → Fine-grained
   tokens → repositorio `Emirodgar/w-open-salamanca` → permisos de
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
