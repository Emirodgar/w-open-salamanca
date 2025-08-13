# Open Salamanca - Diseño y Arquitectura del Portal

## Visión General
Portal de datos abiertos y colaborativos para la ciudad de Salamanca con diseño minimalista pero visualmente impactante, centrado en la información y con capacidad de generar páginas dinámicamente desde archivos XML.

## Principios de Diseño

### Minimalismo Visual
- Espacios en blanco generosos
- Tipografía clara y legible
- Paleta de colores reducida pero efectiva
- Elementos visuales enfocados en los datos

### Centrado en la Información
- Los datos son el protagonista
- Visualizaciones claras y comprensibles
- Navegación intuitiva
- Búsqueda prominente

### Colaborativo y Abierto
- Facilidad para contribuir con nuevos datos
- Transparencia en el proceso
- Accesibilidad universal
- Formatos estándar (XML)

## Arquitectura del Sistema

### Estructura de Archivos
```
open-salamanca/
├── index.html                 # Página principal
├── assets/
│   ├── css/
│   │   ├── main.css          # Estilos principales
│   │   ├── components.css    # Componentes reutilizables
│   │   └── visualizations.css # Estilos para gráficos
│   ├── js/
│   │   ├── main.js           # Funcionalidad principal
│   │   ├── xml-parser.js     # Procesador de XML
│   │   ├── template-engine.js # Motor de templates
│   │   └── chart-generator.js # Generador de gráficos
│   └── images/
├── data/
│   ├── xml/                  # Archivos XML de datos
│   │   ├── poblacion.xml
│   │   ├── economia.xml
│   │   ├── educacion.xml
│   │   └── finanzas.xml
│   └── schemas/              # Esquemas XML
├── templates/
│   ├── dataset-page.html     # Template para páginas de datos
│   ├── chart-templates/      # Templates para gráficos
│   └── components/           # Componentes reutilizables
└── pages/                    # Páginas generadas dinámicamente
```

### Componentes Principales

#### 1. Header
- Logo "Open Salamanca"
- Navegación principal
- Barra de búsqueda prominente
- Indicador de contribuciones

#### 2. Hero Section
- Título impactante
- Estadísticas clave en tiempo real
- Call-to-action para explorar datos
- Visualización destacada

#### 3. Categorías de Datos
- Grid visual de categorías
- Iconos representativos
- Contadores de datasets
- Acceso directo a cada categoría

#### 4. Datasets Destacados
- Carrusel de datasets más utilizados
- Previsualizaciones de gráficos
- Metadatos básicos
- Enlaces directos

#### 5. Contribuir
- Sección para subir nuevos XML
- Guías de formato
- Validación en tiempo real
- Proceso de revisión

#### 6. Footer
- Enlaces institucionales
- Información de contacto
- Licencias y términos
- Redes sociales

## Sistema de Templates XML

### Estructura de XML Base
```xml
<?xml version="1.0" encoding="UTF-8"?>
<dataset>
  <metadata>
    <title>Título del Dataset</title>
    <description>Descripción detallada</description>
    <category>Categoría</category>
    <source>Fuente de los datos</source>
    <updated>2025-01-01</updated>
    <license>CC BY 4.0</license>
  </metadata>
  <visualization>
    <type>chart|map|table</type>
    <config>
      <!-- Configuración específica del tipo -->
    </config>
  </visualization>
  <data>
    <!-- Datos estructurados -->
  </data>
</dataset>
```

### Templates de Visualización

#### Template de Gráfico de Barras
- Para datos categóricos
- Comparaciones simples
- Datos temporales

#### Template de Mapa
- Datos geográficos
- Distribución espacial
- Puntos de interés

#### Template de Tabla
- Datos tabulares
- Listados detallados
- Datos de referencia

## Paleta de Colores

### Colores Principales
- **Primario**: #2C5F2D (Verde Salamanca)
- **Secundario**: #97BC62 (Verde claro)
- **Acento**: #F4A261 (Naranja cálido)
- **Neutro**: #264653 (Azul oscuro)

### Colores de Soporte
- **Fondo**: #FEFEFE (Blanco casi puro)
- **Texto**: #2A2A2A (Gris oscuro)
- **Bordes**: #E9ECEF (Gris claro)
- **Éxito**: #28A745
- **Advertencia**: #FFC107
- **Error**: #DC3545

## Tipografía

### Fuente Principal
- **Familia**: Inter (Google Fonts)
- **Pesos**: 300, 400, 500, 600, 700
- **Uso**: Títulos, texto general, navegación

### Fuente de Datos
- **Familia**: JetBrains Mono
- **Uso**: Código, datos numéricos, metadatos

## Responsive Design

### Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

### Adaptaciones
- Navegación colapsable en móvil
- Grid adaptativo para categorías
- Gráficos responsivos
- Texto escalable

## Interacciones y Animaciones

### Micro-interacciones
- Hover states suaves
- Transiciones de 200-300ms
- Loading states elegantes
- Feedback visual inmediato

### Animaciones de Entrada
- Fade-in para contenido
- Slide-up para cards
- Stagger para listas
- Parallax sutil en hero

## Accesibilidad

### Estándares
- WCAG 2.1 AA compliance
- Contraste mínimo 4.5:1
- Navegación por teclado
- Screen reader friendly

### Implementación
- Alt text para imágenes
- ARIA labels apropiados
- Focus indicators visibles
- Estructura semántica HTML5

