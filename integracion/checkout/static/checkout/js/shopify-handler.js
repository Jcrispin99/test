// Manejo específico de datos provenientes de Shopify
class ShopifyHandler {
  constructor() {
    this.shopifyData = this.parseShopifyData();
  }

  parseShopifyData() {
    console.log('🔍 [ShopifyHandler] parseShopifyData iniciado');
    console.log('🔍 [ShopifyHandler] URL actual:', window.location.href);
    
    const urlParams = new URLSearchParams(window.location.search);
    const dataParam = urlParams.get("data");
    console.log('🔍 [ShopifyHandler] Parámetro data encontrado:', !!dataParam);
    console.log('🔍 [ShopifyHandler] Parámetro data (primeros 100 chars):', dataParam ? dataParam.substring(0, 100) + '...' : 'null');
    
    try {
      const decodedData = decodeURIComponent(dataParam || "{}");
      console.log('🔍 [ShopifyHandler] Datos decodificados:', decodedData);
      
      const parsedData = JSON.parse(decodedData);
      console.log('🔍 [ShopifyHandler] Datos parseados:', parsedData);
      console.log('🔍 [ShopifyHandler] Número de items:', parsedData.items ? parsedData.items.length : 0);
      console.log('🔍 [ShopifyHandler] Email del cliente:', parsedData.email);
      
      return parsedData;
    } catch (error) {
      console.error('❌ [ShopifyHandler] Error parseando datos de Shopify:', error);
      return {};
    }
  }

  getOrderItems() {
    const items = this.shopifyData?.items || [];
    console.log('📦 [ShopifyHandler] getOrderItems() retorna:', items.length, 'items');
    console.log('📦 [ShopifyHandler] Items detalle:', items);
    return items;
  }

  getCustomerInfo() {
    const customerInfo = {
      email: this.shopifyData?.email || null,
      customer: this.shopifyData?.customer || null,
    };
    console.log('👤 [ShopifyHandler] getCustomerInfo() retorna:', customerInfo);
    return customerInfo;
  }

  calculateOrderTotal() {
    const items = this.getOrderItems();
    return items.reduce((total, item) => total + item.line_price, 0);
  }

  // Preparar datos para enviar a Shopify
  prepareShopifyOrder(formData) {
    return {
      email: formData.email,
      items: this.getOrderItems(),
      shipping_address: {
        first_name: formData.first_name,
        last_name: formData.last_name,
        address1: formData.address1,
        address2: formData.address2,
        city: formData.city,
        province: formData.province,
        zip: formData.zip,
      },
      shipping_method: formData.shipping_method,
    };
  }

  clearShopifyData() {
    this.shopifyData.items = [];
    const url = new URL(window.location);
    url.searchParams.delete("data");
    window.history.replaceState({}, document.title, url.pathname);
  }
}
