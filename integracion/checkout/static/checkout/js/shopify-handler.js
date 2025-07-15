class ShopifyHandler {
  constructor() {
    this.shopifyData = this.parseShopifyData();
  }

  parseShopifyData() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const dataParam = urlParams.get("data");
      
      if (!dataParam) {
        return this.getMockData();
      }
      
      const decodedData = decodeURIComponent(dataParam);
      const parsedData = JSON.parse(decodedData);
      
      if (!parsedData.items || !Array.isArray(parsedData.items)) {
        parsedData.items = this.getMockItems();
      }
      
      if (parsedData.customer) {
        parsedData.customer = {
          first_name: parsedData.customer.first_name || '',
          last_name: parsedData.customer.last_name || '',
          email: parsedData.customer.email || parsedData.email || '',
          phone: parsedData.customer.phone || '',
          address: {
            address1: parsedData.customer.address?.address1 || '',
            address2: parsedData.customer.address?.address2 || '',
            city: parsedData.customer.address?.city || '',
            province: parsedData.customer.address?.province || '',
            zip: parsedData.customer.address?.zip || '',
            country: parsedData.customer.address?.country || 'Perú'
          }
        };
      }
      
      if (!parsedData.email && parsedData.customer?.email) {
        parsedData.email = parsedData.customer.email;
      }
      
      return parsedData;
    } catch (error) {
      console.error("❌ Error parsing Shopify data:", error);
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
    if (this.shopifyData?.total_price) {
      const total = parseFloat(this.shopifyData.total_price);
      return total.toFixed(2);
    }
    
    const items = this.getOrderItems();
    const totalInCents = items.reduce((total, item) => total + item.line_price, 0);
    const totalDecimal = (totalInCents / 100).toFixed(2);
    return totalDecimal;
  }

  prepareShopifyOrder(formData) {
    const customerInfo = this.getCustomerInfo();
    
    return {
      email: formData.email || customerInfo.email || '',
      items: this.getOrderItems(),
      shipping_address: {
        first_name: formData.first_name || customerInfo.customer?.first_name || '',
        last_name: formData.last_name || customerInfo.customer?.last_name || '',
        address1: formData.address1 || customerInfo.customer?.address?.address1 || '',
        address2: formData.address2 || customerInfo.customer?.address?.address2 || '',
        city: formData.city || customerInfo.customer?.address?.city || '',
        province: formData.province || customerInfo.customer?.address?.province || '',
        zip: formData.zip || customerInfo.customer?.address?.zip || '',
        country: 'Perú'
      },
      shipping_method: formData.shipping_method || 'standard',
      total_price: this.shopifyData?.total_price || 0,
      currency: this.shopifyData?.currency || 'PEN',
      token: this.shopifyData?.token || '',
      _debug: {
        form_data_keys: Object.keys(formData),
        customer_available: !!customerInfo.customer,
        items_count: this.getOrderItems().length
      }
    };
  }

  autoFillForm() {
    if (!this.shopifyData.customer) {
      return;
    }

    const customer = this.shopifyData.customer;
    const fillField = (selector, value) => {
      const field = document.querySelector(selector);
      if (field && value && !field.value) {
        field.value = value;
      }
    };

    fillField('input[name="first_name"]', customer.first_name);
    fillField('input[name="last_name"]', customer.last_name);
    fillField('input[name="email"]', customer.email);
    fillField('input[name="phone"]', customer.phone);

    if (customer.address) {
      fillField('input[name="address1"]', customer.address.address1);
      fillField('input[name="address2"]', customer.address.address2);
      fillField('input[name="city"]', customer.address.city);
      fillField('input[name="zip"]', customer.address.zip);

      const provinceField = document.querySelector('select[name="province"]');
      if (provinceField && customer.address.province) {
        const options = provinceField.querySelectorAll('option');
        for (let option of options) {
          if (option.textContent.toLowerCase().includes(customer.address.province.toLowerCase()) ||
              option.value === customer.address.province) {
            provinceField.value = option.value;
            provinceField.dispatchEvent(new Event('change', { bubbles: true }));
            break;
          }
        }
      }
    }
  }

  clearShopifyData() {
    this.shopifyData.items = [];
    const url = new URL(window.location);
    url.searchParams.delete("data");
    window.history.replaceState({}, document.title, url.pathname);
  }

  getMockData() {
    return {
      items: this.getMockItems(),
      total_price: 50.00,
      currency: 'PEN',
      email: 'test@ejemplo.com',
      customer: {
        first_name: 'Cliente',
        last_name: 'Prueba',
        email: 'test@ejemplo.com',
        phone: '989623418',
        address: {
          address1: 'Av. Test 123',
          address2: '',
          city: 'Lima',
          province: 'Lima',
          zip: '15001',
          country: 'Perú'
        }
      }
    };
  }

  getMockItems() {
    return [
      {
        id: 1,
        name: "Producto de Prueba",
        quantity: 1,
        line_price: 5000, // 50.00 en centavos
        sku: "TEST-001",
        image: "https://via.placeholder.com/150x150/FF6B6B/FFFFFF?text=Producto+Prueba"
      }
    ];
  }
}
