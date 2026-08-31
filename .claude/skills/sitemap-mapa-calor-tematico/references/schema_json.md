# Estructura del JSON de salida

```jsonc
{
  "url_base": "https://www.dominio.es",           // nunca se muestra en textos
  "generado_en": "2026-08-31T11:05:23+00:00",     // timestamp ISO de la ejecución
  "periodo_cubierto": {"desde": "2026-08-22", "hasta": "2026-08-31"}, // o null
  "total_urls_analizadas": 314,
  "secciones_excluidas": ["tu-gaceta", "nacional"],
  "nota_cobertura": "texto explicando el alcance real del análisis",

  "por_seccion": [["deportes", 64], ["sucesos", 54], ...],
  "por_subseccion": [["deportes/futbol-local", 48], ...],
  "por_tipo_contenido": [["noticia", 334], ["galería", 19], ...],

  "heatmap_calendario": [
    {"fecha": "2026-08-22", "total": 6, "deportes": 4, "sucesos": 1, ...},
    ...
  ],

  "conceptos_destacados": [
    {
      "concepto": "Santa Marta de Tormes, entre el deporte y los sustos", // etiqueta legible; Claude puede reescribirla
      "piezas": 6,
      "seccion_principal": "sucesos",
      "desde": "2026-08-23", "hasta": "2026-08-30",
      "evidencia": ["santa marta campeon fase regional copa rfef", ...],   // crudo, solo para verificar
      "ejemplos_redactados": null   // <- Claude lo rellena con 1-2 frases en español correcto
    },
    ...
  ],

  "resumen_borrador": "texto mecánico (cifras + etiquetas) — NO publicar tal cual",
  "resumen": null   // <- Claude lo rellena con el resumen periodístico final (2-3 párrafos)
}
```

Notas:
- El JSON que sale directamente del script **no está listo para publicar**:
  `resumen` y cada `ejemplos_redactados` llegan a `null` a propósito. El
  paso de redacción (obligatorio, lo hace Claude) es lo que los rellena
  antes de generar el widget o entregar el fichero final al usuario.
- `heatmap_calendario` incluye una clave por cada sección detectada en el
  top de `por_seccion` — el número de columnas variará según el medio.
- Todos los recuentos están basados en el número de URLs, no en visitas ni
  en ningún dato de analítica externo.
