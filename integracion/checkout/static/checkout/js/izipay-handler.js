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
      console.log("🔗 Creando Payment Link de Izipay...", orderData);

      const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
      if (!csrfToken) {
        throw new Error("CSRF token no encontrado en el formulario");
      }

      // Generar orderNumber único si no existe
      const orderNumber = orderData.orderNumber || `ORDER-${Date.now()}`;
      console.log(`📦 Order Number: ${orderNumber}`);
      console.log(`💰 Amount: ${orderData.total}`);

      const payload = {
        amount: orderData.total,
        orderNumber: orderNumber,
        customerEmail: billingData.email,
        customerName: `${billingData.firstName} ${billingData.lastName}`,
        billing: billingData,
        shipping: shippingData || billingData,
        currency: this.izipayConfig.currency
      };

      console.log("📤 Enviando payload para Payment Link:", payload);

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
      console.log("📨 Respuesta del Payment Link:", data);

      if (data.success && data.paymentLink) {
        console.log("✅ Payment Link creado exitosamente");
        console.log(`🔗 Payment Link URL: ${data.paymentLink}`);
        
        // Redirigir automáticamente al Payment Link
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
    console.log(`🚀 Redirigiendo a Payment Link: ${paymentLinkUrl}`);
    
    // Abrir en la misma ventana para una mejor experiencia de usuario
    window.location.href = paymentLinkUrl;
    
    // Alternativa: abrir en nueva ventana
    // window.open(paymentLinkUrl, '_blank');
  }

  /**
   * Preparar datos de billing para el Payment Link
   */
  prepareBillingData(formData) {
    const convertedState = this.getRegionNameFromCode(formData.billing_state);
    console.log(`🌍 [Billing] Conversión de región: "${formData.billing_state}" -> "${convertedState}"`);
    
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
    // Si es pickup, usar datos de billing
    if (formData.delivery_option === 'pickup') {
      console.log("📦 Delivery option: pickup - usando datos de billing para shipping");
      return this.prepareBillingData(formData);
    }
    
    const convertedState = this.getRegionNameFromCode(formData.shipping_state);
    console.log(`🌍 [Shipping] Conversión de región: "${formData.shipping_state}" -> "${convertedState}"`);
    
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
      console.log("💳 Procesando pago con Payment Link API...", paymentData);
      
      const { orderData, formData, totalAmount } = paymentData;
      
      // Preparar datos de billing y shipping
      const billingData = this.prepareBillingData(formData);
      const shippingData = this.prepareShippingData(formData);
      
      console.log("👤 Billing data preparado:", billingData);
      console.log("📦 Shipping data preparado:", shippingData);
      
      // Preparar orderData con el total correcto
      const paymentOrderData = {
        ...orderData,
        total: totalAmount,
        orderNumber: orderData.orderNumber || `ORDER-${Date.now()}`
      };
      
      // Crear Payment Link
      const result = await this.createPaymentLink(paymentOrderData, billingData, shippingData);
      
      console.log("✅ Payment Link procesado exitosamente:", result);
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

  /**
   * Manejar error del pago (para compatibilidad con checkout-controller)
   */
  onPaymentError(response) {
    console.error("❌ Error en pago (Payment Link):", response);
    alert(`Error en el pago: ${response.error || "Error desconocido"}`);
  }

  /**
   * Generar referencia de orden única
   */
  generateOrderReference() {
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 1000);
    return `ORDER-${timestamp}-${random}`;
  }

  /**
   * Convertir código de región a nombre (mapeo de regiones peruanas)
   */
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

  // ===== MÉTODOS LEGACY PARA COMPATIBILIDAD =====
  // Estos métodos se mantienen para compatibilidad con el código existente
  // pero no se usan en la nueva implementación de Payment Link

  async generateToken(orderData) {
    console.warn("⚠️ generateToken es un método legacy - usar createPaymentLink en su lugar");
    throw new Error("Método no disponible en Payment Link API");
  }

  async initializeCheckout(orderData, billingData) {
    console.warn("⚠️ initializeCheckout es un método legacy - usar createPaymentLink en su lugar");
    throw new Error("Método no disponible en Payment Link API");
  }

  showPaymentForm(callbackResponse) {
    console.warn("⚠️ showPaymentForm es un método legacy - usar createPaymentLink en su lugar");
    throw new Error("Método no disponible en Payment Link API");
  }

  handlePaymentResponse(response) {
    console.warn("⚠️ handlePaymentResponse es un método legacy - Payment Link maneja las respuestas automáticamente");
    throw new Error("Método no disponible en Payment Link API");
  }

  convertToAmountFormat(amount) {
    console.warn("⚠️ convertToAmountFormat es un método legacy - Payment Link maneja montos automáticamente");
    throw new Error("Método no disponible en Payment Link API");
  }

  prepareIzipayPayment(orderData, totalAmount) {
    console.warn("⚠️ prepareIzipayPayment es un método legacy - usar processPayment en su lugar");
    return this.processPayment({ orderData, totalAmount });
  }

  async generatePaymentLink(orderData, billingData, shippingData) {
    console.warn("⚠️ generatePaymentLink renombrado a createPaymentLink");
    return this.createPaymentLink(orderData, billingData, shippingData);
  }
}

// Crear instancia global para compatibilidad
window.izipayHandler = new IzipayHandler();