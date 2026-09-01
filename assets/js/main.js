// Main JavaScript file for Open Salamanca portal
// Handles navigation, search, UI interactions, and initialization

class OpenSalamanca {
    constructor() {
        this.datasets = [];
        this.categories = [];
        this.categoryPages = [];
        this.searchResults = [];
        this.currentView = 'home';
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        this.setupMobileMenu();
        this.setupSearch();
        this.setupUpload();
        
        // Load initial data
        await this.loadData();
        this.renderCategories();
        this.renderFeaturedDatasets();
        this.updateStats();
        this.initializeCharts();
        
        // Add scroll animations
        this.setupScrollAnimations();
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                if (!href || !href.startsWith('#')) {
                    // External link or full URL (e.g. "Inicio"): let the browser navigate normally
                    return;
                }
                e.preventDefault();
                const target = href.substring(1);
                this.scrollToSection(target);
                this.setActiveNavLink(link);
            });
        });
        
        // Search
        const searchBtn = document.getElementById('searchBtn');
        const searchInput = document.getElementById('searchInput');
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.performSearch());
        }
        
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
            
            searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });
        }
    }
    
    setupMobileMenu() {
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const nav = document.querySelector('.nav');
        
        if (mobileMenuBtn && nav) {
            mobileMenuBtn.addEventListener('click', () => {
                nav.classList.toggle('active');
                mobileMenuBtn.classList.toggle('active');
            });
        }
    }
    
    setupSearch() {
        const searchContainer = document.querySelector('.search-container');
        if (!searchContainer) return;
        
        // Create search results container
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'search-results';
        resultsContainer.id = 'searchResults';
        searchContainer.appendChild(resultsContainer);
        
        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchContainer.contains(e.target)) {
                resultsContainer.classList.remove('show');
            }
        });
    }
    
    setupUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileUpload(files[0]);
                }
            });
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileUpload(e.target.files[0]);
                }
            });
        }
    }
    
    async loadData() {
        try {
            const [datasetsResponse, categoriesResponse] = await Promise.all([
                fetch('/datasets.json'),
                fetch('/categories.json')
            ]);
            if (!datasetsResponse.ok) {
                throw new Error(`HTTP ${datasetsResponse.status} (datasets.json)`);
            }
            if (!categoriesResponse.ok) {
                throw new Error(`HTTP ${categoriesResponse.status} (categories.json)`);
            }
            this.datasets = await datasetsResponse.json();
            this.categoryPages = await categoriesResponse.json();
            this.categories = this.extractCategories(this.datasets);
        } catch (error) {
            console.error('Error loading data:', error);
            this.showToast('Error al cargar los datos', 'error');
        }
    }

    // Parses the "DD-MM-YYYY" front-matter date format used by dataset pages
    parseDate(dateStr) {
        if (!dateStr) return null;
        const parts = dateStr.split('-').map(Number);
        if (parts.length !== 3 || parts.some(Number.isNaN)) return null;
        const [day, month, year] = parts;
        return new Date(year, month - 1, day);
    }

    formatDate(date) {
        const months = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
        return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
    }
    
    // Only surfaces categories that have a real categoria-*.html page (site.pages
    // entries exposing a `category` front-matter field, see categories.json) — a
    // dataset whose category has no listing page yet is counted but not linked,
    // so a new dataset can never produce a broken category card on the home page.
    extractCategories(datasets) {
        const counts = new Map();
        datasets.forEach(dataset => {
            counts.set(dataset.category, (counts.get(dataset.category) || 0) + 1);
        });

        return this.categoryPages
            .filter(page => counts.has(page.name))
            .map(page => ({
                name: page.name,
                title: page.title,
                url: page.url,
                count: counts.get(page.name),
                icon: this.getCategoryIcon(page.name)
            }));
    }

    getCategoryIcon(category) {
        const icons = {
            'Demografia': '👥',
            'Economia': '💰',
            'Educacion': '🎓',
            'Finanzas': '📊',
            'Movilidad': '🚌',
            'Urbanismo': '🏙️',
            'Turismo': '🗺️',
            'Mercado Laboral': '💼',
            'Medio Ambiente': '🌱',
            'Cultura y Ocio': '🎭',
            'Hacienda Local': '🏛️',
            'Cultura': '🎭',
            'Deportes': '⚽',
            'Salud': '🏥',
            'Seguridad': '🚔'
        };
        return icons[category] || '📋';
    }
    
    renderCategories() {
        const container = document.getElementById('categoriesGrid');
        if (!container) return;
        
        container.innerHTML = this.categories.map(category => `
            <div class="category-card" onclick="window.location.href = '${category.url}'">
                <div class="category-icon">
                    <span style="font-size: 24px;">${category.icon}</span>
                </div>
                <h4 class="category-title">${category.name}</h4>
                <p style="display:none;" class="category-count">${category.count} datasets</p>
            </div>
        `).join('');
    }
    
    renderFeaturedDatasets() {
        const container = document.getElementById('featuredDatasets');
        if (!container) return;
        
        const featured = this.datasets.slice(0, 3);

        container.innerHTML = featured.map(dataset => {
            const parsedDate = this.parseDate(dataset.date);
            return `
            <div class="dataset-card" onclick="window.location.href = '${dataset.url}'">
                <div class="dataset-header">
                    <h4 class="dataset-title">${dataset.title}</h4>
                    <p class="dataset-description">${dataset.description}</p>
                </div>
                <div class="dataset-meta">
                    <span class="dataset-category">${dataset.category}</span>
                    <span>${parsedDate ? this.formatDate(parsedDate) : ''}</span>
                </div>
            </div>
        `;
        }).join('');
    }
    
    updateStats() {
        const totalDatasets = document.getElementById('totalDatasets');
        const totalCategories = document.getElementById('totalCategories');
        const totalViews = document.getElementById('totalViews');
        const lastUpdate = document.getElementById('lastUpdate');

        if (totalDatasets) {
            this.animateNumber(totalDatasets, this.datasets.length);
        }
        if (totalCategories) {
            this.animateNumber(totalCategories, this.categories.length);
        }

        const parsedDates = this.datasets
            .map(dataset => this.parseDate(dataset.date))
            .filter(Boolean);

        if (totalViews) {
            const currentYear = new Date().getFullYear();
            const publishedThisYear = parsedDates.filter(date => date.getFullYear() === currentYear).length;
            this.animateNumber(totalViews, publishedThisYear);
        }
        if (lastUpdate) {
            const mostRecent = parsedDates.length
                ? new Date(Math.max(...parsedDates.map(date => date.getTime())))
                : null;
            lastUpdate.textContent = mostRecent ? this.formatDate(mostRecent) : 'Hoy';
        }
    }
    
    animateNumber(element, target) {
        let current = 0;
        const increment = target / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current).toLocaleString();
        }, 30);
    }
    
    initializeCharts() {
        // Initialize sample charts
        setTimeout(() => {
            this.createPopulationChart();
            this.createEconomicChart();
            this.createEducationChart();
        }, 500);
    }
    
    createPopulationChart() {
        const canvas = document.getElementById('populationChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const dataset = this.datasets.find(d => d.id === 'poblacion-distritos');
        
        if (dataset) {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: dataset.data.map(d => d.distrito),
                    datasets: [{
                        label: 'Población',
                        data: dataset.data.map(d => d.poblacion),
                        backgroundColor: '#2C5F2D',
                        borderColor: '#97BC62',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
    
    createEconomicChart() {
        const canvas = document.getElementById('economicChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const dataset = this.datasets.find(d => d.id === 'economia-anual');
        
        if (dataset) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dataset.data.map(d => d.año),
                    datasets: [{
                        label: 'PIB (millones €)',
                        data: dataset.data.map(d => d.pib),
                        borderColor: '#2C5F2D',
                        backgroundColor: 'rgba(44, 95, 45, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    }
    
    createEducationChart() {
        const canvas = document.getElementById('educationChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const dataset = this.datasets.find(d => d.id === 'educacion-centros');
        
        if (dataset) {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: dataset.data.map(d => d.tipo),
                    datasets: [{
                        data: dataset.data.map(d => d.cantidad),
                        backgroundColor: [
                            '#2C5F2D',
                            '#97BC62',
                            '#F4A261',
                            '#264653',
                            '#28A745',
                            '#FFC107'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }
    
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        }, observerOptions);
        
        document.querySelectorAll('.category-card, .dataset-card, .viz-card, .stat-card').forEach(el => {
            observer.observe(el);
        });
    }
    
    scrollToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            const headerHeight = document.querySelector('.header').offsetHeight;
            const targetPosition = section.offsetTop - headerHeight - 20;
            
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    }
    
    setActiveNavLink(activeLink) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        activeLink.classList.add('active');
    }
    
    performSearch() {
        const searchInput = document.getElementById('searchInput');
        const query = searchInput.value.trim();
        
        if (query.length < 2) {
            this.hideSearchResults();
            return;
        }
        
        this.searchResults = this.datasets.filter(dataset => 
            dataset.title.toLowerCase().includes(query.toLowerCase()) ||
            dataset.description.toLowerCase().includes(query.toLowerCase()) ||
            dataset.category.toLowerCase().includes(query.toLowerCase())
        );
        
        this.showSearchResults();
    }
    
    handleSearchInput(query) {
        if (query.length >= 2) {
            this.performSearch();
        } else {
            this.hideSearchResults();
        }
    }
    
    showSearchResults() {
        const container = document.getElementById('searchResults');
        if (!container) return;
        
        if (this.searchResults.length === 0) {
            container.innerHTML = '<div class="search-result-item">No se encontraron resultados</div>';
        } else {
            container.innerHTML = this.searchResults.map(dataset => {
                const parsedDate = this.parseDate(dataset.date);
                return `
                <div class="search-result-item" onclick="openSalamanca.viewDataset('${dataset.id}')">
                    <div class="search-result-title">${dataset.title}</div>
                    <div class="search-result-description">${dataset.description}</div>
                    <div class="search-result-meta">${dataset.category}${parsedDate ? ' • ' + this.formatDate(parsedDate) : ''}</div>
                </div>
            `;
            }).join('');
        }
        
        container.classList.add('show');
    }
    
    hideSearchResults() {
        const container = document.getElementById('searchResults');
        if (container) {
            container.classList.remove('show');
        }
    }
    
    filterByCategory(categoryName) {
        const filtered = this.datasets.filter(dataset => dataset.category === categoryName);
        this.showToast(`Mostrando ${filtered.length} datasets de ${categoryName}`, 'success');
        // In a real implementation, this would navigate to a filtered view
    }
    
    viewDataset(datasetId) {
        const dataset = this.datasets.find(d => d.id === datasetId);
        if (dataset && dataset.url) {
            window.location.href = dataset.url;
        }
    }
    
    handleFileUpload(file) {
        if (file.type !== 'text/xml' && !file.name.endsWith('.xml')) {
            this.showToast('Por favor, selecciona un archivo XML válido', 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const xmlContent = e.target.result;
                this.validateXML(xmlContent);
            } catch (error) {
                this.showToast('Error al procesar el archivo XML', 'error');
            }
        };
        reader.readAsText(file);
    }
    
    validateXML(xmlContent) {
        try {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(xmlContent, 'text/xml');
            
            if (xmlDoc.getElementsByTagName('parsererror').length > 0) {
                throw new Error('XML malformado');
            }
            
            this.showValidationResult(true, 'XML válido y listo para procesar');
        } catch (error) {
            this.showValidationResult(false, error.message);
        }
    }
    
    showValidationResult(isValid, message) {
        const container = document.getElementById('validationResult');
        if (!container) return;
        
        container.innerHTML = `
            <div class="validation-message ${isValid ? 'success' : 'error'}">
                <strong>${isValid ? 'Válido' : 'Error'}:</strong> ${message}
            </div>
        `;
        container.style.display = 'block';
    }
    
    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-header">
                <div class="toast-title">${type === 'error' ? 'Error' : type === 'success' ? 'Éxito' : 'Información'}</div>
                <button class="toast-close">&times;</button>
            </div>
            <div class="toast-message">${message}</div>
        `;
        
        // Add event listener for close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        });
        
        // Add to container and show
        container.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }
}

// Global functions for onclick handlers
window.scrollToSection = function(sectionId) {
    if (window.openSalamanca) {
        window.openSalamanca.scrollToSection(sectionId);
    }
};

window.openUploadModal = function() {
    if (window.openSalamanca) {
        window.openSalamanca.showToast('Función de subida disponible en la sección Contribuir', 'info');
    }
};

window.downloadSchema = function() {
    if (window.openSalamanca) {
        window.openSalamanca.showToast('Descargando esquema XML...', 'info');
        // In a real implementation, this would download the XML schema
    }
};

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.openSalamanca = new OpenSalamanca();

    const footerYearEl = document.getElementById('footerYear');
    if (footerYearEl) {
        footerYearEl.textContent = new Date().getFullYear();
    }
});

