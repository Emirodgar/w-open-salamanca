// Chart Generator for Open Salamanca
// Creates dynamic charts and visualizations from dataset configurations

class ChartGenerator {
    constructor() {
        this.defaultColors = [
            '#2C5F2D', '#97BC62', '#F4A261', '#264653', 
            '#28A745', '#FFC107', '#DC3545', '#17A2B8',
            '#6F42C1', '#E83E8C', '#20C997', '#FD7E14'
        ];
        
        this.chartInstances = new Map();
    }
    
    /**
     * Generate chart from dataset configuration
     * @param {Object} dataset - Dataset with visualization config
     * @param {string} canvasId - ID of canvas element
     * @returns {Chart} Chart.js instance
     */
    generateChart(dataset, canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            throw new Error(`Canvas element not found: ${canvasId}`);
        }
        
        // Destroy existing chart if it exists
        if (this.chartInstances.has(canvasId)) {
            this.chartInstances.get(canvasId).destroy();
        }
        
        const ctx = canvas.getContext('2d');
        const config = this.buildChartConfig(dataset);
        
        const chart = new Chart(ctx, config);
        this.chartInstances.set(canvasId, chart);
        
        return chart;
    }
    
    /**
     * Build Chart.js configuration from dataset
     * @param {Object} dataset - Dataset object
     * @returns {Object} Chart.js configuration
     */
    buildChartConfig(dataset) {
        const { visualization, data } = dataset;
        const type = visualization.type || 'bar';
        const config = visualization.config || {};
        
        switch (type) {
            case 'bar':
                return this.buildBarChart(data, config);
            case 'line':
                return this.buildLineChart(data, config);
            case 'pie':
            case 'doughnut':
                return this.buildPieChart(data, config, type);
            case 'scatter':
                return this.buildScatterChart(data, config);
            case 'area':
                return this.buildAreaChart(data, config);
            case 'radar':
                return this.buildRadarChart(data, config);
            case 'polarArea':
                return this.buildPolarAreaChart(data, config);
            default:
                throw new Error(`Unsupported chart type: ${type}`);
        }
    }
    
    /**
     * Build bar chart configuration
     * @param {Array} data - Chart data
     * @param {Object} config - Chart configuration
     * @returns {Object} Chart.js config
     */
    buildBarChart(data, config) {
        const labels = this.extractLabels(data, config);
        const datasets = this.extractDatasets(data, config, 'bar');
        
        return {
            type: 'bar',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: !!config.title,
                        text: config.title,
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: datasets.length > 1,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: !!config.xAxis,
                            text: config.xAxis
                        },
                        grid: {
                            display: config.showGrid !== false
                        }
                    },
                    y: {
                        title: {
                            display: !!config.yAxis,
                            text: config.yAxis
                        },
                        beginAtZero: config.beginAtZero !== false,
                        grid: {
                            display: config.showGrid !== false
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        };
    }
    
    /**
     * Build line chart configuration
     * @param {Array} data - Chart data
     * @param {Object} config - Chart configuration
     * @returns {Object} Chart.js config
     */
    buildLineChart(data, config) {
        const labels = this.extractLabels(data, config);
        const datasets = this.extractDatasets(data, config, 'line');
        
        return {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: !!config.title,
                        text: config.title,
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: datasets.length > 1,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: !!config.xAxis,
                            text: config.xAxis
                        },
                        grid: {
                            display: config.showGrid !== false
                        }
                    },
                    y: {
                        title: {
                            display: !!config.yAxis,
                            text: config.yAxis
                        },
                        beginAtZero: config.beginAtZero !== false,
                        grid: {
                            display: config.showGrid !== false
                        }
                    }
                },
                elements: {
                    line: {
                        tension: config.tension || 0.4
                    },
                    point: {
                        radius: config.pointRadius || 4,
                        hoverRadius: config.pointHoverRadius || 6
                    }
                }
            }
        };
    }
    
    /**
     * Build pie/doughnut chart configuration
     * @param {Array} data - Chart data
     * @param {Object} config - Chart configuration
     * @param {string} type - Chart type (pie or doughnut)
     * @returns {Object} Chart.js config
     */
    buildPieChart(data, config, type = 'pie') {
        const labels = this.extractLabels(data, config);
        const values = this.extractValues(data, config);
        const colors = config.colors || this.defaultColors.slice(0, labels.length);
        
        return {
            type: type,
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderColor: colors.map(color => this.darkenColor(color, 0.2)),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: !!config.title,
                        text: config.title,
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        position: config.legendPosition || 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        };
    }
    
    /**
     * Build scatter chart configuration
     * @param {Array} data - Chart data
     * @param {Object} config - Chart configuration
     * @returns {Object} Chart.js config
     */
    buildScatterChart(data, config) {
        const datasets = this.extractScatterDatasets(data, config);
        
        return {
            type: 'scatter',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: !!config.title,
                        text: config.title,
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: datasets.length > 1,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: !!config.xAxis,
                            text: config.xAxis
                        }
                    },
                    y: {
                        title: {
                            display: !!config.yAxis,
                            text: config.yAxis
                        }
                    }
                }
            }
        };
    }
    
    /**
     * Build area chart configuration
     * @param {Array} data - Chart data
     * @param {Object} config - Chart configuration
     * @returns {Object} Chart.js config
     */
    buildAreaChart(data, config) {
        const lineConfig = this.buildLineChart(data, config);
        
        // Modify for area chart
        lineConfig.data.datasets.forEach((dataset, index) => {
            dataset.fill = true;
            dataset.backgroundColor = this.hexToRgba(dataset.borderColor, 0.2);
        });
        
        return lineConfig;
    }
    
    /**
     * Build radar chart configuration
     * @param {Array} data - Chart data
     * @param {Object} config - Chart configuration
     * @returns {Object} Chart.js config
     */
    buildRadarChart(data, config) {
        const labels = this.extractLabels(data, config);
        const datasets = this.extractDatasets(data, config, 'radar');
        
        return {
            type: 'radar',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: !!config.title,
                        text: config.title,
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: datasets.length > 1,
                        position: 'top'
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        pointLabels: {
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        };
    }
    
    /**
     * Build polar area chart configuration
     * @param {Array} data - Chart data
     * @param {Object} config - Chart configuration
     * @returns {Object} Chart.js config
     */
    buildPolarAreaChart(data, config) {
        const pieConfig = this.buildPieChart(data, config, 'polarArea');
        return pieConfig;
    }
    
    /**
     * Extract labels from data
     * @param {Array} data - Data array
     * @param {Object} config - Configuration
     * @returns {Array} Labels array
     */
    extractLabels(data, config) {
        if (!Array.isArray(data) || data.length === 0) return [];
        
        const labelField = config.labelField || this.guessLabelField(data[0]);
        return data.map(item => item[labelField] || '');
    }
    
    /**
     * Extract datasets for multi-series charts
     * @param {Array} data - Data array
     * @param {Object} config - Configuration
     * @param {string} chartType - Chart type
     * @returns {Array} Datasets array
     */
    extractDatasets(data, config, chartType) {
        if (!Array.isArray(data) || data.length === 0) return [];
        
        const labelField = config.labelField || this.guessLabelField(data[0]);
        const valueFields = config.valueFields || this.guessValueFields(data[0], labelField);
        
        return valueFields.map((field, index) => {
            const color = (config.colors && config.colors[index]) || this.defaultColors[index % this.defaultColors.length];
            
            const dataset = {
                label: config.datasetLabels ? config.datasetLabels[index] : field,
                data: data.map(item => item[field] || 0),
                borderColor: color,
                backgroundColor: chartType === 'line' ? this.hexToRgba(color, 0.1) : color
            };
            
            if (chartType === 'line') {
                dataset.tension = config.tension || 0.4;
                dataset.fill = config.fill || false;
            }
            
            return dataset;
        });
    }
    
    /**
     * Extract values for single-series charts
     * @param {Array} data - Data array
     * @param {Object} config - Configuration
     * @returns {Array} Values array
     */
    extractValues(data, config) {
        if (!Array.isArray(data) || data.length === 0) return [];
        
        const labelField = config.labelField || this.guessLabelField(data[0]);
        const valueField = config.valueField || this.guessValueFields(data[0], labelField)[0];
        
        return data.map(item => item[valueField] || 0);
    }
    
    /**
     * Extract datasets for scatter charts
     * @param {Array} data - Data array
     * @param {Object} config - Configuration
     * @returns {Array} Scatter datasets
     */
    extractScatterDatasets(data, config) {
        if (!Array.isArray(data) || data.length === 0) return [];
        
        const xField = config.xField || 'x';
        const yField = config.yField || 'y';
        const groupField = config.groupField;
        
        if (groupField) {
            // Group data by groupField
            const groups = {};
            data.forEach(item => {
                const group = item[groupField];
                if (!groups[group]) groups[group] = [];
                groups[group].push({ x: item[xField], y: item[yField] });
            });
            
            return Object.entries(groups).map(([group, points], index) => ({
                label: group,
                data: points,
                backgroundColor: this.defaultColors[index % this.defaultColors.length],
                borderColor: this.defaultColors[index % this.defaultColors.length]
            }));
        } else {
            // Single dataset
            return [{
                label: config.label || 'Data',
                data: data.map(item => ({ x: item[xField], y: item[yField] })),
                backgroundColor: this.defaultColors[0],
                borderColor: this.defaultColors[0]
            }];
        }
    }
    
    /**
     * Guess label field from data structure
     * @param {Object} sample - Sample data object
     * @returns {string} Likely label field
     */
    guessLabelField(sample) {
        const fields = Object.keys(sample);
        const labelCandidates = ['name', 'label', 'category', 'distrito', 'año', 'mes', 'fecha', 'tipo'];
        
        for (const candidate of labelCandidates) {
            if (fields.includes(candidate)) return candidate;
        }
        
        // Return first string field
        for (const field of fields) {
            if (typeof sample[field] === 'string') return field;
        }
        
        return fields[0];
    }
    
    /**
     * Guess value fields from data structure
     * @param {Object} sample - Sample data object
     * @param {string} labelField - Label field to exclude
     * @returns {Array} Likely value fields
     */
    guessValueFields(sample, labelField) {
        const fields = Object.keys(sample);
        return fields.filter(field => 
            field !== labelField && 
            typeof sample[field] === 'number'
        );
    }
    
    /**
     * Convert hex color to rgba
     * @param {string} hex - Hex color
     * @param {number} alpha - Alpha value
     * @returns {string} RGBA color
     */
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    /**
     * Darken a color by a percentage
     * @param {string} color - Hex color
     * @param {number} percent - Percentage to darken (0-1)
     * @returns {string} Darkened hex color
     */
    darkenColor(color, percent) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent * 100);
        const R = (num >> 16) - amt;
        const G = (num >> 8 & 0x00FF) - amt;
        const B = (num & 0x0000FF) - amt;
        return '#' + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
    }
    
    /**
     * Update chart with new data
     * @param {string} canvasId - Canvas ID
     * @param {Object} newDataset - New dataset
     */
    updateChart(canvasId, newDataset) {
        const chart = this.chartInstances.get(canvasId);
        if (!chart) {
            throw new Error(`Chart not found: ${canvasId}`);
        }
        
        const newConfig = this.buildChartConfig(newDataset);
        chart.data = newConfig.data;
        chart.options = newConfig.options;
        chart.update();
    }
    
    /**
     * Destroy chart instance
     * @param {string} canvasId - Canvas ID
     */
    destroyChart(canvasId) {
        const chart = this.chartInstances.get(canvasId);
        if (chart) {
            chart.destroy();
            this.chartInstances.delete(canvasId);
        }
    }
    
    /**
     * Export chart as image
     * @param {string} canvasId - Canvas ID
     * @param {string} format - Image format (png, jpeg)
     * @returns {string} Data URL
     */
    exportChart(canvasId, format = 'png') {
        const chart = this.chartInstances.get(canvasId);
        if (!chart) {
            throw new Error(`Chart not found: ${canvasId}`);
        }
        
        return chart.toBase64Image(format, 1.0);
    }
    
    /**
     * Get chart statistics
     * @param {string} canvasId - Canvas ID
     * @returns {Object} Chart statistics
     */
    getChartStats(canvasId) {
        const chart = this.chartInstances.get(canvasId);
        if (!chart) {
            throw new Error(`Chart not found: ${canvasId}`);
        }
        
        const data = chart.data;
        const stats = {
            type: chart.config.type,
            datasets: data.datasets.length,
            dataPoints: 0,
            labels: data.labels ? data.labels.length : 0
        };
        
        data.datasets.forEach(dataset => {
            if (Array.isArray(dataset.data)) {
                stats.dataPoints += dataset.data.length;
            }
        });
        
        return stats;
    }
    
    /**
     * Get all active chart instances
     * @returns {Array} Array of canvas IDs
     */
    getActiveCharts() {
        return Array.from(this.chartInstances.keys());
    }
}

// Export for use in other modules
window.ChartGenerator = ChartGenerator;

