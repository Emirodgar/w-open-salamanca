// XML Parser for Open Salamanca
// Handles parsing, validation, and processing of XML data files

class XMLParser {
    constructor() {
        this.schemas = new Map();
        this.loadSchemas();
    }
    
    async loadSchemas() {
        // Define XML schemas for different data types
        this.schemas.set('dataset', {
            required: ['metadata', 'data'],
            metadata: {
                required: ['title', 'description', 'category', 'source', 'updated', 'license'],
                optional: ['tags', 'contact', 'frequency']
            },
            visualization: {
                required: ['type'],
                optional: ['config', 'template']
            },
            data: {
                required: true,
                types: ['array', 'object']
            }
        });
        
        this.schemas.set('category', {
            required: ['name', 'description'],
            optional: ['icon', 'color', 'parent']
        });
    }
    
    /**
     * Parse XML string and return structured data
     * @param {string} xmlString - XML content as string
     * @param {string} schemaType - Type of schema to validate against
     * @returns {Object} Parsed and validated data
     */
    parseXML(xmlString, schemaType = 'dataset') {
        try {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xmlString, 'text/xml');
            
            // Check for parsing errors
            const parseError = xmlDoc.getElementsByTagName('parsererror')[0];
            if (parseError) {
                throw new Error(`XML Parse Error: ${parseError.textContent}`);
            }
            
            // Get root element
            const rootElement = xmlDoc.documentElement;
            
            // Parse based on schema type
            switch (schemaType) {
                case 'dataset':
                    return this.parseDataset(rootElement);
                case 'category':
                    return this.parseCategory(rootElement);
                default:
                    throw new Error(`Unknown schema type: ${schemaType}`);
            }
            
        } catch (error) {
            throw new Error(`XML Processing Error: ${error.message}`);
        }
    }
    
    /**
     * Parse dataset XML structure
     * @param {Element} rootElement - Root XML element
     * @returns {Object} Dataset object
     */
    parseDataset(rootElement) {
        const dataset = {
            id: this.generateId(),
            metadata: {},
            visualization: {},
            data: null
        };
        
        // Parse metadata
        const metadataElement = rootElement.getElementsByTagName('metadata')[0];
        if (!metadataElement) {
            throw new Error('Missing required metadata section');
        }
        
        dataset.metadata = this.parseMetadata(metadataElement);
        
        // Parse visualization config (optional)
        const vizElement = rootElement.getElementsByTagName('visualization')[0];
        if (vizElement) {
            dataset.visualization = this.parseVisualization(vizElement);
        }
        
        // Parse data
        const dataElement = rootElement.getElementsByTagName('data')[0];
        if (!dataElement) {
            throw new Error('Missing required data section');
        }
        
        dataset.data = this.parseData(dataElement);
        
        // Validate against schema
        this.validateDataset(dataset);
        
        return dataset;
    }
    
    /**
     * Parse metadata section
     * @param {Element} metadataElement - Metadata XML element
     * @returns {Object} Metadata object
     */
    parseMetadata(metadataElement) {
        const metadata = {};
        const schema = this.schemas.get('dataset').metadata;
        
        // Parse required fields
        schema.required.forEach(field => {
            const element = metadataElement.getElementsByTagName(field)[0];
            if (!element) {
                throw new Error(`Missing required metadata field: ${field}`);
            }
            metadata[field] = element.textContent.trim();
        });
        
        // Parse optional fields
        schema.optional.forEach(field => {
            const element = metadataElement.getElementsByTagName(field)[0];
            if (element) {
                if (field === 'tags') {
                    // Parse tags as array
                    metadata[field] = element.textContent.split(',').map(tag => tag.trim());
                } else {
                    metadata[field] = element.textContent.trim();
                }
            }
        });
        
        // Validate date format
        if (metadata.updated && !this.isValidDate(metadata.updated)) {
            throw new Error('Invalid date format in updated field. Use YYYY-MM-DD format.');
        }
        
        return metadata;
    }
    
    /**
     * Parse visualization configuration
     * @param {Element} vizElement - Visualization XML element
     * @returns {Object} Visualization config
     */
    parseVisualization(vizElement) {
        const visualization = {};
        
        // Parse type
        const typeElement = vizElement.getElementsByTagName('type')[0];
        if (!typeElement) {
            throw new Error('Missing required visualization type');
        }
        
        visualization.type = typeElement.textContent.trim();
        
        // Validate visualization type
        const validTypes = ['bar', 'line', 'pie', 'doughnut', 'scatter', 'area', 'map', 'table', 'heatmap'];
        if (!validTypes.includes(visualization.type)) {
            throw new Error(`Invalid visualization type: ${visualization.type}`);
        }
        
        // Parse config (optional)
        const configElement = vizElement.getElementsByTagName('config')[0];
        if (configElement) {
            visualization.config = this.parseConfig(configElement);
        }
        
        // Parse template (optional)
        const templateElement = vizElement.getElementsByTagName('template')[0];
        if (templateElement) {
            visualization.template = templateElement.textContent.trim();
        }
        
        return visualization;
    }
    
    /**
     * Parse configuration object
     * @param {Element} configElement - Config XML element
     * @returns {Object} Configuration object
     */
    parseConfig(configElement) {
        const config = {};
        
        // Parse all child elements as config properties
        Array.from(configElement.children).forEach(child => {
            const key = child.tagName;
            const value = child.textContent.trim();
            
            // Try to parse as JSON if it looks like an object/array
            if (value.startsWith('{') || value.startsWith('[')) {
                try {
                    config[key] = JSON.parse(value);
                } catch (e) {
                    config[key] = value;
                }
            } else if (value === 'true' || value === 'false') {
                config[key] = value === 'true';
            } else if (!isNaN(value) && value !== '') {
                config[key] = Number(value);
            } else {
                config[key] = value;
            }
        });
        
        return config;
    }
    
    /**
     * Parse data section
     * @param {Element} dataElement - Data XML element
     * @returns {Array|Object} Parsed data
     */
    parseData(dataElement) {
        // Check if data is in JSON format
        const jsonData = dataElement.getElementsByTagName('json')[0];
        if (jsonData) {
            try {
                return JSON.parse(jsonData.textContent);
            } catch (e) {
                throw new Error('Invalid JSON data format');
            }
        }
        
        // Check if data is in CSV format
        const csvData = dataElement.getElementsByTagName('csv')[0];
        if (csvData) {
            return this.parseCSV(csvData.textContent);
        }
        
        // Parse as structured XML
        const records = dataElement.getElementsByTagName('record');
        if (records.length > 0) {
            return this.parseRecords(records);
        }
        
        // Parse as simple key-value pairs
        const items = dataElement.getElementsByTagName('item');
        if (items.length > 0) {
            return this.parseItems(items);
        }
        
        throw new Error('No valid data format found. Use json, csv, record, or item elements.');
    }
    
    /**
     * Parse CSV data
     * @param {string} csvText - CSV content
     * @returns {Array} Array of objects
     */
    parseCSV(csvText) {
        const lines = csvText.trim().split('\\n');
        if (lines.length < 2) {
            throw new Error('CSV must have at least header and one data row');
        }
        
        const headers = lines[0].split(',').map(h => h.trim());
        const data = [];
        
        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',').map(v => v.trim());
            if (values.length !== headers.length) {
                throw new Error(`CSV row ${i} has ${values.length} values but expected ${headers.length}`);
            }
            
            const row = {};
            headers.forEach((header, index) => {
                let value = values[index];
                // Try to convert to number if possible
                if (!isNaN(value) && value !== '') {
                    value = Number(value);
                }
                row[header] = value;
            });
            data.push(row);
        }
        
        return data;
    }
    
    /**
     * Parse record elements
     * @param {NodeList} records - Record elements
     * @returns {Array} Array of record objects
     */
    parseRecords(records) {
        const data = [];
        
        Array.from(records).forEach((record, index) => {
            const recordData = {};
            
            Array.from(record.children).forEach(field => {
                const key = field.tagName;
                let value = field.textContent.trim();
                
                // Try to convert to appropriate type
                if (!isNaN(value) && value !== '') {
                    value = Number(value);
                } else if (value === 'true' || value === 'false') {
                    value = value === 'true';
                }
                
                recordData[key] = value;
            });
            
            data.push(recordData);
        });
        
        return data;
    }
    
    /**
     * Parse item elements
     * @param {NodeList} items - Item elements
     * @returns {Array} Array of items
     */
    parseItems(items) {
        const data = [];
        
        Array.from(items).forEach(item => {
            const key = item.getAttribute('key') || item.getAttribute('name');
            let value = item.textContent.trim();
            
            // Try to convert to appropriate type
            if (!isNaN(value) && value !== '') {
                value = Number(value);
            } else if (value === 'true' || value === 'false') {
                value = value === 'true';
            }
            
            if (key) {
                data.push({ [key]: value });
            } else {
                data.push(value);
            }
        });
        
        return data;
    }
    
    /**
     * Parse category XML structure
     * @param {Element} rootElement - Root XML element
     * @returns {Object} Category object
     */
    parseCategory(rootElement) {
        const category = {
            id: this.generateId()
        };
        
        const schema = this.schemas.get('category');
        
        // Parse required fields
        schema.required.forEach(field => {
            const element = rootElement.getElementsByTagName(field)[0];
            if (!element) {
                throw new Error(`Missing required category field: ${field}`);
            }
            category[field] = element.textContent.trim();
        });
        
        // Parse optional fields
        schema.optional.forEach(field => {
            const element = rootElement.getElementsByTagName(field)[0];
            if (element) {
                category[field] = element.textContent.trim();
            }
        });
        
        return category;
    }
    
    /**
     * Validate dataset against schema
     * @param {Object} dataset - Dataset to validate
     */
    validateDataset(dataset) {
        const schema = this.schemas.get('dataset');
        
        // Check required sections
        schema.required.forEach(section => {
            if (!dataset[section]) {
                throw new Error(`Missing required section: ${section}`);
            }
        });
        
        // Validate metadata
        const metadataSchema = schema.metadata;
        metadataSchema.required.forEach(field => {
            if (!dataset.metadata[field]) {
                throw new Error(`Missing required metadata field: ${field}`);
            }
        });
        
        // Validate data is not empty
        if (!dataset.data || (Array.isArray(dataset.data) && dataset.data.length === 0)) {
            throw new Error('Data section cannot be empty');
        }
        
        // Validate category
        const validCategories = [
            'Demografia', 'Economia', 'Educacion', 'Finanzas', 'Transporte',
            'Medio Ambiente', 'Cultura', 'Deportes', 'Salud', 'Seguridad'
        ];
        
        if (!validCategories.includes(dataset.metadata.category)) {
            console.warn(`Category '${dataset.metadata.category}' is not in the standard list`);
        }
        
        // Validate license
        const validLicenses = ['CC BY 4.0', 'CC BY-SA 4.0', 'CC0 1.0', 'ODbL', 'Public Domain'];
        if (!validLicenses.includes(dataset.metadata.license)) {
            console.warn(`License '${dataset.metadata.license}' is not in the recommended list`);
        }
    }
    
    /**
     * Generate unique ID
     * @returns {string} Unique identifier
     */
    generateId() {
        return 'dataset_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Validate date format (YYYY-MM-DD)
     * @param {string} dateString - Date string to validate
     * @returns {boolean} True if valid
     */
    isValidDate(dateString) {
        const regex = /^\\d{4}-\\d{2}-\\d{2}$/;
        if (!regex.test(dateString)) return false;
        
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date);
    }
    
    /**
     * Convert dataset back to XML
     * @param {Object} dataset - Dataset object
     * @returns {string} XML string
     */
    datasetToXML(dataset) {
        let xml = '<?xml version="1.0" encoding="UTF-8"?>\\n';
        xml += '<dataset>\\n';
        
        // Metadata section
        xml += '  <metadata>\\n';
        Object.entries(dataset.metadata).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                xml += `    <${key}>${value.join(', ')}</${key}>\\n`;
            } else {
                xml += `    <${key}>${this.escapeXML(value)}</${key}>\\n`;
            }
        });
        xml += '  </metadata>\\n';
        
        // Visualization section (if exists)
        if (dataset.visualization && Object.keys(dataset.visualization).length > 0) {
            xml += '  <visualization>\\n';
            xml += `    <type>${dataset.visualization.type}</type>\\n`;
            
            if (dataset.visualization.config) {
                xml += '    <config>\\n';
                Object.entries(dataset.visualization.config).forEach(([key, value]) => {
                    if (typeof value === 'object') {
                        xml += `      <${key}>${JSON.stringify(value)}</${key}>\\n`;
                    } else {
                        xml += `      <${key}>${this.escapeXML(value)}</${key}>\\n`;
                    }
                });
                xml += '    </config>\\n';
            }
            
            if (dataset.visualization.template) {
                xml += `    <template>${this.escapeXML(dataset.visualization.template)}</template>\\n`;
            }
            
            xml += '  </visualization>\\n';
        }
        
        // Data section
        xml += '  <data>\\n';
        xml += '    <json>\\n';
        xml += JSON.stringify(dataset.data, null, 6);
        xml += '\\n    </json>\\n';
        xml += '  </data>\\n';
        
        xml += '</dataset>';
        
        return xml;
    }
    
    /**
     * Escape XML special characters
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeXML(text) {
        if (typeof text !== 'string') {
            text = String(text);
        }
        
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
    
    /**
     * Get XML schema template for a given type
     * @param {string} type - Schema type
     * @returns {string} XML template
     */
    getSchemaTemplate(type = 'dataset') {
        switch (type) {
            case 'dataset':
                return `<?xml version="1.0" encoding="UTF-8"?>
<dataset>
  <metadata>
    <title>Título del Dataset</title>
    <description>Descripción detallada del dataset</description>
    <category>Categoria</category>
    <source>Fuente de los datos</source>
    <updated>2025-01-01</updated>
    <license>CC BY 4.0</license>
    <tags>tag1, tag2, tag3</tags>
    <contact>email@ejemplo.com</contact>
  </metadata>
  
  <visualization>
    <type>bar</type>
    <config>
      <title>Título del Gráfico</title>
      <xAxis>Eje X</xAxis>
      <yAxis>Eje Y</yAxis>
      <colors>["#2C5F2D", "#97BC62", "#F4A261"]</colors>
    </config>
  </visualization>
  
  <data>
    <json>
    [
      {"campo1": "valor1", "campo2": 100},
      {"campo1": "valor2", "campo2": 200}
    ]
    </json>
  </data>
</dataset>`;
            
            case 'category':
                return `<?xml version="1.0" encoding="UTF-8"?>
<category>
  <name>Nombre de la Categoría</name>
  <description>Descripción de la categoría</description>
  <icon>📊</icon>
  <color>#2C5F2D</color>
</category>`;
            
            default:
                throw new Error(`No template available for type: ${type}`);
        }
    }
}

// Export for use in other modules
window.XMLParser = XMLParser;

