class IzipayHandler {
  constructor() {
    this.checkout = null;
    this.token = null;
    this.izipayConfig = {
      paymentLinkUrl: "/izipay/payment-link/",
      currency: "PEN",
      merchantCode: "4004345",
      publicKey: "VErethUtraQuxas57wuMuquprADrAHAb",
    };
  }

  /**
   * Crear Payment Link usando la nueva API de Izipay
   */
  async createPaymentLink(orderData, billingData, shippingData) {
    try {
      const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
      if (!csrfToken) {
        throw new Error("CSRF token no encontrado en el formulario");
      }

      const orderNumber = orderData.orderNumber || `ORDER-${Date.now()}`;

      const payload = {
        amount: orderData.total,
        orderNumber: orderNumber,
        customerEmail: billingData.email,
        customerName: `${billingData.firstName} ${billingData.lastName}`,
        billing: billingData,
        shipping: shippingData || billingData,
        currency: this.izipayConfig.currency
      };

      const response = await fetch(this.izipayConfig.paymentLinkUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken.value,
        },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("❌ Response error:", errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }      
      const data = await response.json();

      if (data.success && data.paymentLink) {
        this.redirectToPaymentLink(data.paymentLink);
        return data;
      } else {
        throw new Error(data.error || "Error desconocido creando Payment Link");
      }
    } catch (error) {
      console.error("❌ Error creando Payment Link:", error);
      throw error;
    }
  }

  /**
   * Redirigir al usuario al Payment Link
   */
  redirectToPaymentLink(paymentLinkUrl) {
    window.location.href = paymentLinkUrl;
  }

  /**
   * Preparar datos de billing para el Payment Link
   */
  prepareBillingData(formData) {
    const convertedState = this.getRegionNameFromCode(formData.billing_state);
    
    return {
      firstName: formData.billing_first_name || "Test",
      lastName: formData.billing_last_name || "User",
      email: formData.billing_email || "test@example.com",
      phoneNumber: formData.billing_phone || "987654321",
      street: formData.billing_address || "Av Test 123",
      city: formData.billing_city || "Lima",
      state: convertedState || "Lima",
      country: "PE",
      postalCode: formData.billing_postal_code || "15001",
      documentType: "DNI",
      document: formData.billing_document || "12345678"
    };
  }

  /**
   * Preparar datos de shipping para el Payment Link
   */
  prepareShippingData(formData) {
    if (formData.delivery_option === 'pickup') {
      console.log("📦 Delivery option: pickup - usando datos de billing para shipping");
      return this.prepareBillingData(formData);
    }
    
    const convertedState = this.getRegionNameFromCode(formData.shipping_state);
    
    return {
      firstName: formData.shipping_first_name || formData.billing_first_name || "Test",
      lastName: formData.shipping_last_name || formData.billing_last_name || "User",
      email: formData.billing_email || "test@example.com",
      phoneNumber: formData.shipping_phone || formData.billing_phone || "987654321",
      street: formData.shipping_address || formData.billing_address || "Av Test 123",
      city: formData.shipping_city || formData.billing_city || "Lima",
      state: convertedState || "Lima",
      country: "PE",
      postalCode: formData.shipping_postal_code || formData.billing_postal_code || "15001",
      documentType: "DNI",
      document: formData.billing_document || "12345678"
    };
  }

  /**
   * Procesar pago usando Payment Link API
   */
  async processPayment(paymentData) {
    try {
      const { orderData, formData, totalAmount } = paymentData;
      
      const billingData = this.prepareBillingData(formData);
      const shippingData = this.prepareShippingData(formData);
      
      const paymentOrderData = {
        ...orderData,
        total: totalAmount,
        orderNumber: orderData.orderNumber || `ORDER-${Date.now()}`
      };
      
      const result = await this.createPaymentLink(paymentOrderData, billingData, shippingData);
      return result;
      
    } catch (error) {
      console.error("❌ Error procesando pago:", error);
      this.onPaymentError({ error: error.message });
      throw error;
    }
  }

  /**
   * Manejar éxito del pago (para compatibilidad con checkout-controller)
   */
  onPaymentSuccess(response) {
    console.log("✅ Pago exitoso (Payment Link):", response);
  }

  onPaymentError(response) {
    console.error("❌ Error en pago (Payment Link):", response);
    alert(`Error en el pago: ${response.error || "Error desconocido"}`);
  }

  generateOrderReference() {
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 1000);
    return `ORDER-${timestamp}-${random}`;
  }

  getRegionNameFromCode(code) {
    const regionMapping = {
      "AMA": "Amazonas",
      "ANC": "Áncash", 
      "APU": "Apurímac",
      "ARE": "Arequipa",
      "AYA": "Ayacucho",
      "CAJ": "Cajamarca",
      "CAL": "Callao",
      "CUS": "Cusco",
      "HUV": "Huancavelica",
      "HUC": "Huánuco",
      "ICA": "Ica",
      "JUN": "Junín",
      "LAL": "La Libertad",
      "LAM": "Lambayeque",
      "LIM": "Lima",
      "LOR": "Loreto",
      "MDD": "Madre de Dios",
      "MOQ": "Moquegua",
      "PAS": "Pasco",
      "PIU": "Piura",
      "PUN": "Puno",
      "SAM": "San Martín",
      "TAC": "Tacna",
      "TUM": "Tumbes",
      "UCA": "Ucayali"
    };
    
    return regionMapping[code] || code;
  }

  async generateToken() {
    throw new Error("Método no disponible en Payment Link API");
  }  
  async initializeCheckout() {
    throw new Error("Método no disponible en Payment Link API");
  }

  showPaymentForm() {
    throw new Error("Método no disponible en Payment Link API");
  }

  handlePaymentResponse() {
    throw new Error("Método no disponible en Payment Link API");
  }

  convertToAmountFormat() {
    throw new Error("Método no disponible en Payment Link API");
  }

  prepareIzipayPayment(orderData, totalAmount) {
    return this.processPayment({ orderData, totalAmount });
  }

  async generatePaymentLink(orderData, billingData, shippingData) {
    return this.createPaymentLink(orderData, billingData, shippingData);
  }
}

window.izipayHandler = new IzipayHandler();