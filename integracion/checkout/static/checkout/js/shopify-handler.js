// Manejo específico de datos provenientes de Shopify
class ShopifyHandler {
  constructor() {
    this.shopifyData = this.parseShopifyData();
  }

  parseShopifyData() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const dataParam = urlParams.get("data");
      const decodedData = decodeURIComponent(dataParam || "{}");
      return JSON.parse(decodedData);
    } catch (error) {
      return {};
    }
  }

  getOrderItems() {
    return this.shopifyData?.items || [];
  }

  getCustomerInfo() {
    return {
      email: this.shopifyData?.email || null,
      customer: this.shopifyData?.customer || null,
    };
  }

  calculateOrderTotal() {
    const items = this.getOrderItems();
    const totalInCents = items.reduce((total, item) => total + item.line_price, 0);
    // Convertir de centavos a soles con 2 decimales
    return (totalInCents / 100).toFixed(2);
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
