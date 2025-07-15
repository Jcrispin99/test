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
      console.log('✅ [PeruRegions] Regiones cargadas:', regions);
      
      this.populateRegions(regions);
      
    } catch (error) {
      console.error('❌ [PeruRegions] Error cargando regiones:', error);
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
    
    console.log('✅ [PeruRegions] Select poblado con', regions.length, 'regiones');
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
}

window.peruRegions = new PeruRegions();
