# opina-votos — contador de votos para /opina

Backend serverless (Cloudflare Worker + KV) que guarda cuántos votos tiene
cada opción de cada pregunta de la sección "Opina" de opensalamanca.es. No
hay base de datos: Cloudflare KV es un simple almacén clave-valor gestionado
por Cloudflare, gratuito hasta 100.000 lecturas y 1.000 escrituras al día.

## Desplegarlo (una sola vez)

1. Crea una cuenta gratuita en [cloudflare.com](https://dash.cloudflare.com/sign-up)
   si todavía no tienes una.
2. Instala Wrangler (la CLI de Cloudflare) si no la tienes:
   ```bash
   npm install -g wrangler
   ```
3. Inicia sesión (abrirá el navegador):
   ```bash
   wrangler login
   ```
4. Desde esta carpeta (`cloudflare-worker/opina-votos`), crea el namespace de KV:
   ```bash
   wrangler kv namespace create OPINA_VOTOS
   ```
   Este comando imprime un `id`. Cópialo y pégalo en `wrangler.toml`, sustituyendo
   `REEMPLAZA_CON_TU_ID_DE_KV`.
5. Despliega el Worker:
   ```bash
   wrangler deploy
   ```
   Al terminar te dará una URL del tipo `https://opina-votos.<tu-subdominio>.workers.dev`.
6. Copia esa URL y pégala como valor de `"worker_url"` en `opina.json`
   (en la raíz del repo del sitio), sustituyendo el placeholder.
7. Haz commit y push de `opina.json` — la página `/opina` ya podrá votar.

## Actualizar el Worker más adelante

Si cambias `src/index.js`, solo hace falta volver a ejecutar `wrangler deploy`
desde esta carpeta — no hace falta recrear el namespace de KV ni cambiar la URL.

## Ver los votos guardados (opcional)

```bash
wrangler kv key list --namespace-id=<el-id-de-tu-namespace>
wrangler kv key get "poll:eventos-septiembre-2026" --namespace-id=<el-id-de-tu-namespace>
```

## Archivar una pregunta (retirarla de /opina)

Cuando una pregunta deja de ser de actualidad y quieres quitarla de la
votación activa, sigue estos 4 pasos — en este orden, para no perder votos
por el camino:

1. **Consulta el resultado final** desde esta carpeta:
   ```bash
   wrangler kv key get "poll:<id-de-la-pregunta>" --namespace-id=<el-id-de-tu-namespace>
   ```
   Te devuelve el JSON `{"opcion1": 12, "opcion2": 8, ...}`.
2. **Añade una entrada** al array `preguntas_archivadas` de
   `opina-archivo.json` (en la raíz del repo del sitio) con ese resultado:
   ```json
   {
     "id": "eventos-septiembre-2026",
     "pregunta": "¿A cuál de estos eventos de septiembre tienes más ganas de ir?",
     "opciones": ["SALAMAQ", "Ferias de Salamanca (conciertos)", "Feria del Caballo de Ciudad Rodrigo", "A ninguno, paso este año"],
     "basado_en": "eventos.json",
     "fecha_creacion": "2026-09-01",
     "fecha_archivado": "2026-09-20",
     "resultados": { "SALAMAQ": 12, "Ferias de Salamanca (conciertos)": 8 },
     "total_votos": 20
   }
   ```
3. **Quita la pregunta** del array `preguntas` de `opina.json` (y, si era la
   marcada como `"destacada": true`, pon esa marca en otra pregunta que
   siga activa, para que la home siga mostrando una).
4. **Cierra la pregunta en el Worker**, para que nadie pueda seguir votándola
   llamando directamente a la API (la web ya no se lo permite, pero esto lo
   bloquea también del lado del servidor):
   ```bash
   wrangler kv key put "closed:<id-de-la-pregunta>" "1" --namespace-id=<el-id-de-tu-namespace>
   ```
5. Haz commit y push de `opina.json` y `opina-archivo.json`. La pregunta
   desaparecerá de `/opina` y aparecerá con su resultado final en
   `/opina-archivo`.

## Notas de diseño

- No hay ningún sistema anti-fraude robusto: es un contador de opinión
  ligero para una web ciudadana, no una votación oficial. La única
  protección es que la propia página web no deja volver a votar la misma
  pregunta desde el mismo navegador (guardado en `localStorage`), algo que
  cualquiera puede saltarse borrando datos del navegador — es una
  limitación aceptada, no un descuido.
- El CORS del Worker solo permite peticiones desde `https://opensalamanca.es`
  (ver `ORIGEN_PERMITIDO` en `src/index.js`). Si pruebas en local, verás
  errores de CORS al votar — es esperado; para probar de verdad hazlo sobre
  el dominio real ya desplegado, o cambia temporalmente ese valor mientras
  pruebas.
