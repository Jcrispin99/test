class PeruRegions {
    constructor() {
        this.apiUrl = 'https://api.apis.net.pe/v1/ubigeo?region';
        this.provinceSelect = null;
        this.init();
    }

    init() {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", () => this.initializeRegions());
        } else {
            this.initializeRegions();
        }
    }

    initializeRegions() {
        this.provinceSelect = document.getElementById('province');
        if (!this.provinceSelect) {
            console.error('❌ [PeruRegions] Select de provincia no encontrado');
            return;
        }

        this.loadRegions();
    }

    async loadRegions() {
        try {
            console.log('🌍 [PeruRegions] Cargando regiones desde API...');

            const response = await fetch('https://api.ubigeos.com/v1/ubigeos?nivel=1');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const regions = await response.json();

            this.populateRegions(regions);

        } catch (error) {
            console.warn('⚠️ [PeruRegions] API no disponible, usando regiones por defecto:', error.message);
            this.loadFallbackRegions();
        }
    }

    populateRegions(regions) {
        this.provinceSelect.innerHTML = '<option value="">Seleccionar región</option>';

        regions.forEach(region => {
            const option = document.createElement('option');
            option.value = region.codigo || region.id;
            option.textContent = region.nombre || region.name;
            this.provinceSelect.appendChild(option);
        });

        this.autoSelectRegion();
    }

    autoSelectRegion() {
        const cityInput = document.getElementById('city');
        const provinceInput = document.getElementById('province');
        
        if (!cityInput || !provinceInput) {
            console.log('⚠️ [PeruRegions] No se encontraron campos de ciudad o provincia');
            return;
        }

        const customerCity = cityInput.value.trim();
        
        if (!customerCity) {
            console.log('ℹ️ [PeruRegions] No hay ciudad del cliente para autoseleccionar');
            return;
        }

        const cityToRegionMap = {
            'lima': 'Lima',
            'callao': 'Callao',
            'arequipa': 'Arequipa',
            'cusco': 'Cusco',
            'cuzco': 'Cusco',
            'trujillo': 'La Libertad',
            'chiclayo': 'Lambayeque',
            'piura': 'Piura',
            'iquitos': 'Loreto',
            'huancayo': 'Junín',
            'pucallpa': 'Ucayali',
            'tacna': 'Tacna',
            'ica': 'Ica',
            'huánuco': 'Huánuco',
            'huanuco': 'Huánuco',
            'ayacucho': 'Ayacucho',
            'cajamarca': 'Cajamarca',
            'puno': 'Puno',
            'tumbes': 'Tumbes',
            'moquegua': 'Moquegua',
            'abancay': 'Apurímac',
            'huaraz': 'Áncash',
            'chachapoyas': 'Amazonas',
            'huancavelica': 'Huancavelica',
            'cerro de pasco': 'Pasco',
            'pasco': 'Pasco',
            'moyobamba': 'San Martín',
            'tarapoto': 'San Martín',
            'puerto maldonado': 'Madre de Dios'
        };

        const customerCityLower = customerCity.toLowerCase();
        const matchedRegion = cityToRegionMap[customerCityLower];

        if (matchedRegion) {
            const options = this.provinceSelect.options;
            for (let i = 0; i < options.length; i++) {
                if (options[i].textContent.trim() === matchedRegion) {
                    this.provinceSelect.selectedIndex = i;
                    console.log(`✅ [PeruRegions] Región autoseleccionada: ${matchedRegion} (basada en ciudad: ${customerCity})`);
                    
                    const changeEvent = new Event('change', { bubbles: true });
                    this.provinceSelect.dispatchEvent(changeEvent);
                    return;
                }
            }
        }
    }

    loadFallbackRegions() {
        const fallbackRegions = [
            { codigo: '01', nombre: 'Amazonas' },
            { codigo: '02', nombre: 'Áncash' },
            { codigo: '03', nombre: 'Apurímac' },
            { codigo: '04', nombre: 'Arequipa' },
            { codigo: '05', nombre: 'Ayacucho' },
            { codigo: '06', nombre: 'Cajamarca' },
            { codigo: '07', nombre: 'Callao' },
            { codigo: '08', nombre: 'Cusco' },
            { codigo: '09', nombre: 'Huancavelica' },
            { codigo: '10', nombre: 'Huánuco' },
            { codigo: '11', nombre: 'Ica' },
            { codigo: '12', nombre: 'Junín' },
            { codigo: '13', nombre: 'La Libertad' },
            { codigo: '14', nombre: 'Lambayeque' },
            { codigo: '15', nombre: 'Lima' },
            { codigo: '16', nombre: 'Loreto' },
            { codigo: '17', nombre: 'Madre de Dios' },
            { codigo: '18', nombre: 'Moquegua' },
            { codigo: '19', nombre: 'Pasco' },
            { codigo: '20', nombre: 'Piura' },
            { codigo: '21', nombre: 'Puno' },
            { codigo: '22', nombre: 'San Martín' },
            { codigo: '23', nombre: 'Tacna' },
            { codigo: '24', nombre: 'Tumbes' },
            { codigo: '25', nombre: 'Ucayali' }
        ];

        this.populateRegions(fallbackRegions);
    }

    triggerAutoSelect() {
        if (this.provinceSelect && this.provinceSelect.options.length > 1) {
            this.autoSelectRegion();
        }
    }
}

window.peruRegions = new PeruRegions();
