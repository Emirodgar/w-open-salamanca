// Template Engine for Open Salamanca
// Generates dynamic pages from XML data using predefined templates

class TemplateEngine {
    constructor() {
        this.templates = new Map();
        this.loadTemplates();
    }
    
    loadTemplates() {
        // Dataset detail page template
        this.templates.set('dataset-detail', {
            html: `
                <div class="dataset-detail">
                    <header class="dataset-header">
                        <div class="container">
                            <nav class="breadcrumb">
                                <a href="#inicio">Inicio</a> > 
                                <a href="#datos">Datos</a> > 
                                <span>{{metadata.title}}</span>
                            </nav>
                            <h1 class="dataset-title">{{metadata.title}}</h1>
                            <p class="dataset-description">{{metadata.description}}</p>
                            <div class="dataset-meta">
                                <span class="badge badge-primary">{{metadata.category}}</span>
                                <span class="meta-item">
                                    <strong>Fuente:</strong> {{metadata.source}}
                                </span>
                                <span class="meta-item">
                                    <strong>Actualizado:</strong> {{metadata.updated}}
                                </span>
                                <span class="meta-item">
                                    <strong>Licencia:</strong> {{metadata.license}}
                                </span>
                            </div>
                        </div>
                    </header>
                    
                    <main class="dataset-content">
                        <div class="container">
                            <div class="content-grid">
                                <div class="main-content">
                                    {{#if visualization}}
                                    <section class="visualization-section">
                                        <h2>Visualización</h2>
                                        <div class="viz-container">
                                            <div id="datasetChart" class="chart-container"></div>
                                        </div>
                                    </section>
                                    {{/if}}
                                    
                                    <section class="data-section">
                                        <h2>Datos</h2>
                                        <div class="data-controls">
                                            <button class="btn btn-secondary" onclick="downloadData('json')">
                                                Descargar JSON
                                            </button>
                                            <button class="btn btn-secondary" onclick="downloadData('csv')">
                                                Descargar CSV
                                            </button>
                                            <button class="btn btn-secondary" onclick="downloadData('xml')">
                                                Descargar XML
                                            </button>
                                        </div>
                                        <div class="data-table-container">
                                            {{dataTable}}
                                        </div>
                                    </section>
                                </div>
                                
                                <aside class="sidebar">
                                    <div class="info-card">
                                        <h3>Información del Dataset</h3>
                                        <dl class="info-list">
                                            <dt>Categoría</dt>
                                            <dd>{{metadata.category}}</dd>
                                            
                                            <dt>Fuente</dt>
                                            <dd>{{metadata.source}}</dd>
                                            
                                            <dt>Última actualización</dt>
                                            <dd>{{metadata.updated}}</dd>
                                            
                                            <dt>Licencia</dt>
                                            <dd>{{metadata.license}}</dd>
                                            
                                            {{#if metadata.tags}}
                                            <dt>Etiquetas</dt>
                                            <dd>
                                                {{#each metadata.tags}}
                                                <span class="tag">{{this}}</span>
                                                {{/each}}
                                            </dd>
                                            {{/if}}
                                            
                                            {{#if metadata.contact}}
                                            <dt>Contacto</dt>
                                            <dd>{{metadata.contact}}</dd>
                                            {{/if}}
                                        </dl>
                                    </div>
                                    
                                    <div class="stats-card">
                                        <h3>Estadísticas</h3>
                                        <div class="stat-item">
                                            <span class="stat-value">{{stats.records}}</span>
                                            <span class="stat-label">Registros</span>
                                        </div>
                                        <div class="stat-item">
                                            <span class="stat-value">{{stats.fields}}</span>
                                            <span class="stat-label">Campos</span>
                                        </div>
                                        <div class="stat-item">
                                            <span class="stat-value">{{stats.size}}</span>
                                            <span class="stat-label">Tamaño</span>
                                        </div>
                                    </div>
                                </aside>
                            </div>
                        </div>
                    </main>
                </div>
            `,
            css: `
                .dataset-detail {
                    padding-top: 80px;
                }
                
                .dataset-header {
                    background: linear-gradient(135deg, rgba(44, 95, 45, 0.05) 0%, rgba(151, 188, 98, 0.05) 100%);
                    padding: var(--spacing-xl) 0;
                    border-bottom: 1px solid var(--border-color);
                }
                
                .breadcrumb {
                    font-size: 0.875rem;
                    margin-bottom: var(--spacing-md);
                    color: var(--neutral-color);
                }
                
                .breadcrumb a {
                    color: var(--primary-color);
                    text-decoration: none;
                }
                
                .dataset-title {
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: var(--primary-color);
                    margin-bottom: var(--spacing-md);
                }
                
                .dataset-description {
                    font-size: 1.125rem;
                    color: var(--neutral-color);
                    margin-bottom: var(--spacing-lg);
                    line-height: 1.6;
                }
                
                .dataset-meta {
                    display: flex;
                    flex-wrap: wrap;
                    gap: var(--spacing-md);
                    align-items: center;
                }
                
                .meta-item {
                    font-size: 0.875rem;
                    color: var(--neutral-color);
                }
                
                .content-grid {
                    display: grid;
                    grid-template-columns: 1fr 300px;
                    gap: var(--spacing-2xl);
                    margin: var(--spacing-2xl) 0;
                }
                
                @media (max-width: 768px) {
                    .content-grid {
                        grid-template-columns: 1fr;
                    }
                }
                
                .visualization-section,
                .data-section {
                    margin-bottom: var(--spacing-2xl);
                }
                
                .visualization-section h2,
                .data-section h2 {
                    font-size: 1.5rem;
                    font-weight: 600;
                    color: var(--primary-color);
                    margin-bottom: var(--spacing-lg);
                }
                
                .viz-container {
                    background: white;
                    border-radius: 12px;
                    padding: var(--spacing-lg);
                    box-shadow: var(--shadow-md);
                    border: 1px solid var(--border-color);
                }
                
                .chart-container {
                    height: 400px;
                }
                
                .data-controls {
                    display: flex;
                    gap: var(--spacing-sm);
                    margin-bottom: var(--spacing-lg);
                    flex-wrap: wrap;
                }
                
                .data-table-container {
                    background: white;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: var(--shadow-md);
                    border: 1px solid var(--border-color);
                }
                
                .info-card,
                .stats-card {
                    background: white;
                    border-radius: 12px;
                    padding: var(--spacing-lg);
                    box-shadow: var(--shadow-md);
                    border: 1px solid var(--border-color);
                    margin-bottom: var(--spacing-lg);
                }
                
                .info-card h3,
                .stats-card h3 {
                    font-size: 1.125rem;
                    font-weight: 600;
                    color: var(--primary-color);
                    margin-bottom: var(--spacing-md);
                }
                
                .info-list {
                    display: grid;
                    gap: var(--spacing-sm);
                }
                
                .info-list dt {
                    font-weight: 600;
                    color: var(--text-color);
                    font-size: 0.875rem;
                }
                
                .info-list dd {
                    color: var(--neutral-color);
                    font-size: 0.875rem;
                    margin-bottom: var(--spacing-md);
                }
                
                .tag {
                    display: inline-block;
                    background: var(--secondary-color);
                    color: white;
                    padding: var(--spacing-xs) var(--spacing-sm);
                    border-radius: 4px;
                    font-size: 0.75rem;
                    margin-right: var(--spacing-xs);
                    margin-bottom: var(--spacing-xs);
                }
                
                .stat-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: var(--spacing-sm) 0;
                    border-bottom: 1px solid var(--border-color);
                }
                
                .stat-item:last-child {
                    border-bottom: none;
                }
                
                .stat-value {
                    font-weight: 600;
                    color: var(--primary-color);
                    font-family: var(--font-mono);
                }
                
                .stat-label {
                    font-size: 0.875rem;
                    color: var(--neutral-color);
                }
            `
        });
        
        // Category page template
        this.templates.set('category-page', {
            html: `
                <div class="category-page">
                    <header class="category-header">
                        <div class="container">
                            <nav class="breadcrumb">
                                <a href="#inicio">Inicio</a> > 
                                <a href="#categorias">Categorías</a> > 
                                <span>{{category.name}}</span>
                            </nav>
                            <h1 class="category-title">
                                <span class="category-icon">{{category.icon}}</span>
                                {{category.name}}
                            </h1>
                            <p class="category-description">{{category.description}}</p>
                            <div class="category-stats">
                                <span class="stat">{{datasets.length}} datasets disponibles</span>
                            </div>
                        </div>
                    </header>
                    
                    <main class="category-content">
                        <div class="container">
                            <div class="filters-section">
                                <div class="filter-group">
                                    <label class="filter-label">Ordenar por:</label>
                                    <select class="filter-select" id="sortSelect">
                                        <option value="title">Título</option>
                                        <option value="updated">Fecha de actualización</option>
                                        <option value="views">Popularidad</option>
                                    </select>
                                </div>
                                
                                <div class="filter-group">
                                    <label class="filter-label">Tipo de visualización:</label>
                                    <select class="filter-select" id="typeSelect">
                                        <option value="">Todos</option>
                                        <option value="chart">Gráficos</option>
                                        <option value="map">Mapas</option>
                                        <option value="table">Tablas</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="datasets-grid" id="categoryDatasets">
                                {{#each datasets}}
                                <div class="dataset-card" data-type="{{visualization.type}}" onclick="viewDataset('{{id}}')">
                                    <div class="dataset-header">
                                        <h3 class="dataset-title">{{metadata.title}}</h3>
                                        <p class="dataset-description">{{metadata.description}}</p>
                                    </div>
                                    <div class="dataset-meta">
                                        <span class="dataset-source">{{metadata.source}}</span>
                                        <span class="dataset-updated">{{metadata.updated}}</span>
                                    </div>
                                    <div class="dataset-stats">
                                        <span class="stat-item">
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                                <circle cx="12" cy="12" r="3"></circle>
                                            </svg>
                                            {{views}}
                                        </span>
                                        <span class="stat-item">
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                                <polyline points="7,10 12,15 17,10"></polyline>
                                                <line x1="12" y1="15" x2="12" y2="3"></line>
                                            </svg>
                                            {{downloads}}
                                        </span>
                                    </div>
                                </div>
                                {{/each}}
                            </div>
                        </div>
                    </main>
                </div>
            `,
            css: `
                .category-page {
                    padding-top: 80px;
                }
                
                .category-header {
                    background: linear-gradient(135deg, rgba(44, 95, 45, 0.05) 0%, rgba(151, 188, 98, 0.05) 100%);
                    padding: var(--spacing-xl) 0;
                    border-bottom: 1px solid var(--border-color);
                }
                
                .category-title {
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: var(--primary-color);
                    margin-bottom: var(--spacing-md);
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-md);
                }
                
                .category-icon {
                    font-size: 3rem;
                }
                
                .category-description {
                    font-size: 1.125rem;
                    color: var(--neutral-color);
                    margin-bottom: var(--spacing-lg);
                }
                
                .category-stats {
                    font-size: 0.875rem;
                    color: var(--neutral-color);
                }
                
                .filters-section {
                    background: white;
                    padding: var(--spacing-lg);
                    border-radius: 12px;
                    margin: var(--spacing-xl) 0;
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--border-color);
                }
                
                .datasets-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: var(--spacing-lg);
                }
            `
        });
        
        // Search results template
        this.templates.set('search-results', {
            html: `
                <div class="search-results-page">
                    <header class="search-header">
                        <div class="container">
                            <h1 class="search-title">Resultados de búsqueda</h1>
                            <p class="search-query">Búsqueda: "{{query}}"</p>
                            <p class="search-count">{{results.length}} resultados encontrados</p>
                        </div>
                    </header>
                    
                    <main class="search-content">
                        <div class="container">
                            {{#if results.length}}
                            <div class="results-grid">
                                {{#each results}}
                                <div class="result-card" onclick="viewDataset('{{id}}')">
                                    <h3 class="result-title">{{metadata.title}}</h3>
                                    <p class="result-description">{{metadata.description}}</p>
                                    <div class="result-meta">
                                        <span class="result-category">{{metadata.category}}</span>
                                        <span class="result-source">{{metadata.source}}</span>
                                    </div>
                                </div>
                                {{/each}}
                            </div>
                            {{else}}
                            <div class="no-results">
                                <div class="no-results-icon">🔍</div>
                                <h2>No se encontraron resultados</h2>
                                <p>Intenta con otros términos de búsqueda o explora nuestras categorías.</p>
                                <a href="#categorias" class="btn btn-primary">Ver Categorías</a>
                            </div>
                            {{/if}}
                        </div>
                    </main>
                </div>
            `,
            css: `
                .search-results-page {
                    padding-top: 80px;
                }
                
                .search-header {
                    background: linear-gradient(135deg, rgba(44, 95, 45, 0.05) 0%, rgba(151, 188, 98, 0.05) 100%);
                    padding: var(--spacing-xl) 0;
                    border-bottom: 1px solid var(--border-color);
                }
                
                .search-title {
                    font-size: 2rem;
                    font-weight: 600;
                    color: var(--primary-color);
                    margin-bottom: var(--spacing-sm);
                }
                
                .search-query {
                    font-size: 1.125rem;
                    color: var(--text-color);
                    margin-bottom: var(--spacing-xs);
                }
                
                .search-count {
                    font-size: 0.875rem;
                    color: var(--neutral-color);
                }
                
                .results-grid {
                    display: grid;
                    gap: var(--spacing-lg);
                    margin: var(--spacing-xl) 0;
                }
                
                .result-card {
                    background: white;
                    padding: var(--spacing-lg);
                    border-radius: 12px;
                    box-shadow: var(--shadow-md);
                    border: 1px solid var(--border-color);
                    cursor: pointer;
                    transition: var(--transition-normal);
                }
                
                .result-card:hover {
                    transform: translateY(-2px);
                    box-shadow: var(--shadow-lg);
                }
                
                .result-title {
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: var(--primary-color);
                    margin-bottom: var(--spacing-sm);
                }
                
                .result-description {
                    color: var(--neutral-color);
                    margin-bottom: var(--spacing-md);
                    line-height: 1.5;
                }
                
                .result-meta {
                    display: flex;
                    gap: var(--spacing-md);
                    font-size: 0.875rem;
                }
                
                .result-category {
                    background: var(--secondary-color);
                    color: white;
                    padding: var(--spacing-xs) var(--spacing-sm);
                    border-radius: 4px;
                }
                
                .result-source {
                    color: var(--neutral-color);
                }
                
                .no-results {
                    text-align: center;
                    padding: var(--spacing-3xl);
                    color: var(--neutral-color);
                }
                
                .no-results-icon {
                    font-size: 4rem;
                    margin-bottom: var(--spacing-lg);
                }
                
                .no-results h2 {
                    font-size: 1.5rem;
                    margin-bottom: var(--spacing-md);
                    color: var(--text-color);
                }
                
                .no-results p {
                    margin-bottom: var(--spacing-lg);
                }
            `
        });
    }
    
    /**
     * Render a template with data
     * @param {string} templateName - Name of the template
     * @param {Object} data - Data to render
     * @returns {Object} Rendered HTML and CSS
     */
    render(templateName, data) {
        const template = this.templates.get(templateName);
        if (!template) {
            throw new Error(`Template not found: ${templateName}`);
        }
        
        const html = this.processTemplate(template.html, data);
        const css = template.css || '';
        
        return { html, css };
    }
    
    /**
     * Process template with data using simple templating
     * @param {string} template - Template string
     * @param {Object} data - Data object
     * @returns {string} Processed template
     */
    processTemplate(template, data) {
        let processed = template;
        
        // Process simple variables {{variable}}
        processed = processed.replace(/\\{\\{([^}]+)\\}\\}/g, (match, path) => {
            return this.getNestedValue(data, path.trim()) || '';
        });
        
        // Process conditionals {{#if condition}}...{{/if}}
        processed = processed.replace(/\\{\\{#if\\s+([^}]+)\\}\\}([\\s\\S]*?)\\{\\{\\/if\\}\\}/g, (match, condition, content) => {
            const value = this.getNestedValue(data, condition.trim());
            return value ? content : '';
        });
        
        // Process loops {{#each array}}...{{/each}}
        processed = processed.replace(/\\{\\{#each\\s+([^}]+)\\}\\}([\\s\\S]*?)\\{\\{\\/each\\}\\}/g, (match, arrayPath, itemTemplate) => {
            const array = this.getNestedValue(data, arrayPath.trim());
            if (!Array.isArray(array)) return '';
            
            return array.map(item => {
                let itemHtml = itemTemplate;
                // Replace {{this}} with current item
                itemHtml = itemHtml.replace(/\\{\\{this\\}\\}/g, item);
                // Replace {{property}} with item.property
                itemHtml = itemHtml.replace(/\\{\\{([^}]+)\\}\\}/g, (match, prop) => {
                    if (prop.trim() === 'this') return item;
                    return this.getNestedValue(item, prop.trim()) || '';
                });
                return itemHtml;
            }).join('');
        });
        
        return processed;
    }
    
    /**
     * Get nested value from object using dot notation
     * @param {Object} obj - Object to search
     * @param {string} path - Dot notation path
     * @returns {*} Value or undefined
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => {
            return current && current[key] !== undefined ? current[key] : undefined;
        }, obj);
    }
    
    /**
     * Generate data table HTML from dataset
     * @param {Array} data - Array of data objects
     * @param {number} maxRows - Maximum rows to display
     * @returns {string} HTML table
     */
    generateDataTable(data, maxRows = 100) {
        if (!Array.isArray(data) || data.length === 0) {
            return '<p class="no-data">No hay datos disponibles</p>';
        }
        
        const displayData = data.slice(0, maxRows);
        const headers = Object.keys(data[0]);
        
        let html = '<table class="data-table">';
        
        // Header
        html += '<thead><tr>';
        headers.forEach(header => {
            html += `<th>${this.escapeHtml(header)}</th>`;
        });
        html += '</tr></thead>';
        
        // Body
        html += '<tbody>';
        displayData.forEach(row => {
            html += '<tr>';
            headers.forEach(header => {
                const value = row[header];
                const cellClass = typeof value === 'number' ? 'numeric' : '';
                html += `<td class="${cellClass}">${this.escapeHtml(String(value))}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody>';
        
        html += '</table>';
        
        if (data.length > maxRows) {
            html += `<p class="table-note">Mostrando ${maxRows} de ${data.length} registros</p>`;
        }
        
        return html;
    }
    
    /**
     * Generate dataset statistics
     * @param {Array} data - Dataset data
     * @returns {Object} Statistics object
     */
    generateStats(data) {
        if (!Array.isArray(data) || data.length === 0) {
            return { records: 0, fields: 0, size: '0 KB' };
        }
        
        const records = data.length;
        const fields = Object.keys(data[0]).length;
        const sizeBytes = JSON.stringify(data).length;
        const size = this.formatBytes(sizeBytes);
        
        return { records, fields, size };
    }
    
    /**
     * Format bytes to human readable format
     * @param {number} bytes - Number of bytes
     * @returns {string} Formatted size
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * Escape HTML special characters
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Create a new page from template and data
     * @param {string} templateName - Template to use
     * @param {Object} data - Data for the template
     * @param {string} containerId - ID of container to render into
     */
    createPage(templateName, data, containerId = 'main-content') {
        const rendered = this.render(templateName, data);
        
        // Create or get container
        let container = document.getElementById(containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = containerId;
            document.body.appendChild(container);
        }
        
        // Set content
        container.innerHTML = rendered.html;
        
        // Add CSS if not already added
        const styleId = `template-${templateName}-styles`;
        if (!document.getElementById(styleId)) {
            const style = document.createElement('style');
            style.id = styleId;
            style.textContent = rendered.css;
            document.head.appendChild(style);
        }
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    /**
     * Add a new template
     * @param {string} name - Template name
     * @param {Object} template - Template object with html and css
     */
    addTemplate(name, template) {
        this.templates.set(name, template);
    }
    
    /**
     * Get available templates
     * @returns {Array} Array of template names
     */
    getTemplateNames() {
        return Array.from(this.templates.keys());
    }
}

// Export for use in other modules
window.TemplateEngine = TemplateEngine;

