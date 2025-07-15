class IzipayHandler {
  constructor() {
    this.checkout = null;
    this.token = null;
    this.izipayConfig = {
      apiUrl: "/izipay/generate-token/",
      currency: "PEN",
      merchantCode: "4004345",
      publicKey: "VErethUtraQuxas57wuMuquprADrAHAb",
    };
  }

  async generateToken(orderData) {
    try {
      console.log("🔄 Generando token de Izipay...", orderData);

      // PRUEBA: Enviar en centavos al token endpoint también
      const amountInCents = this.convertToAmountFormat(orderData.total);
      console.log(`💰 [Token] PRUEBA - Enviando en centavos: ${orderData.total} -> ${amountInCents}`);

      const response = await fetch(this.izipayConfig.apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
            .value,
        },
        body: JSON.stringify({
          amount: amountInCents, // PRUEBA: Enviar en centavos al token
          orderNumber: orderData.orderNumber || `ORDER-${Date.now()}`,
        }),
      });

      const data = await response.json();

      if (data.success) {
        this.token = data.token;
        console.log("✅ Token generado exitosamente");
        console.log(`💰 [Token Response] Amount recibido: ${data.amount}`);
        return data;
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error("❌ Error generando token:", error);
      throw error;
    }
  }

  async initializeCheckout(orderData, billingData) {
    try {
      console.log("🚀 Inicializando checkout de Izipay...");

      const tokenData = await this.generateToken(orderData);

      // PRUEBA: Usar el mismo monto que el token, sin convertir
      console.log(`💰 [Checkout] Usando monto directo del token: ${tokenData.amount}`);

      const convertedState = this.getRegionNameFromCode(billingData.state);
      console.log(`🌍 [Izipay Config] Conversión de región: "${billingData.state}" -> "${convertedState}"`);

      const iziConfig = {
        transactionId: String(tokenData.transactionId),
        action: "pay",
        merchantCode: String(this.izipayConfig.merchantCode),
        order: {
          orderNumber: String(tokenData.orderNumber),
          currency: this.izipayConfig.currency,
          amount: String(tokenData.amount), // Usar el mismo monto del token
          processType: "AT",
          merchantBuyerId: String(this.izipayConfig.merchantCode),
          dateTimeTransaction: String(Date.now()) + "000",
        },
        billing: {
          firstName: billingData.firstName || "Test",
          lastName: billingData.lastName || "User", 
          email: billingData.email || "test@example.com",
          phoneNumber: billingData.phoneNumber || "987654321",
          street: billingData.street || "Av Test 123",
          city: billingData.city || "Lima",
          state: convertedState || "Lima",
          country: "PE",
          postalCode: billingData.postalCode || "15001",
          documentType: "DNI",
          document: billingData.document || "12345678"
        }
      };

      console.log("⚙️ Configuración del SDK:", iziConfig);

      // Verificar que el SDK esté disponible
      if (typeof Izipay === "undefined") {
        throw new Error("SDK de Izipay no está cargado");
      }

      // Verificar que el container existe
      const container = document.getElementById("izipay-form-container");
      if (!container) {
        throw new Error("Container 'izipay-form-container' no encontrado en el DOM");
      }

      try {
        // Usar la estructura exacta de la documentación oficial
        this.checkout = new Izipay({ config: iziConfig });
        console.log("✅ Checkout inicializado correctamente");
        return true;
      } catch ({Errors, message, date}) {
        console.error("❌ Error inicializando checkout:");
        console.log({Errors, message, date});
        return false;
      }
    } catch (error) {
      console.error("❌ Error inicializando checkout:", error);
      return false;
    }
  }

  showPaymentForm(callbackResponse) {
    try {
      console.log("📋 Mostrando formulario de pago...");

      if (!this.checkout || !this.token) {
        throw new Error("Checkout no inicializado");
      }

      const paymentContainer = document.getElementById("izipay-form-container");
      if (paymentContainer) {
        paymentContainer.style.display = "block";
      }

      const callbackResponsePayment = callbackResponse || this.handlePaymentResponse.bind(this);

      this.checkout.LoadForm({
        authorization: this.token,
        keyRSA: this.izipayConfig.publicKey,
        callbackResponse: callbackResponsePayment,
      });

      console.log("✅ Formulario de pago mostrado");
    } catch ({Errors, message, date}) {
      console.error("❌ Error mostrando formulario:");
      console.log({Errors, message, date});
      throw new Error(message || "Error mostrando formulario");
    }
  }

  handlePaymentResponse(response) {
    console.log("💳 Respuesta del pago recibida:", response);

    if (response && response.success) {
      console.log("✅ Pago exitoso");
      this.onPaymentSuccess(response);
    } else {
      console.log("❌ Pago fallido o cancelado");
      this.onPaymentError(response);
    }
  }

  onPaymentSuccess(response) {
    alert("¡Pago realizado exitosamente!");
  }

  onPaymentError(response) {
    alert("Error en el pago. Por favor, intenta nuevamente.");
    console.log("💥 Error en el pago:", response);
  }

  prepareBillingData(formData) {
    const rawState = formData.get("province") || "";
    
    const billingData = {
      firstName: formData.get("first_name") || "",
      lastName: formData.get("last_name") || "",
      email: formData.get("email") || "",
      phoneNumber: formData.get("phone") || "",
      street: formData.get("address1") || "",
      city: formData.get("city") || "",
      state: rawState,
      country: "PE",
      postalCode: formData.get("zip") || "",
      documentType: "DNI",
      document: formData.get("dni") || "",
    };

    const requiredFields = ['firstName', 'lastName', 'email', 'phoneNumber', 'street', 'city', 'document'];
    const missingFields = requiredFields.filter(field => !billingData[field]);
    
    if (missingFields.length > 0) {
      billingData.firstName = billingData.firstName || "Test";
      billingData.lastName = billingData.lastName || "User";
      billingData.email = billingData.email || "test@example.com";
      billingData.phoneNumber = billingData.phoneNumber || "987654321";
      billingData.street = billingData.street || "Av. Test 123";
      billingData.city = billingData.city || "Lima";
      billingData.state = billingData.state || "Lima";
      billingData.postalCode = billingData.postalCode || "15001";
      billingData.document = billingData.document || "12345678";
    }

    console.log('📋 Datos de billing preparados (antes de conversión):', billingData);
    console.log('🌍 Región original del formulario:', rawState);
    
    return billingData;
  }

  prepareIzipayPayment(orderData, totalAmount) {
    return {
      amount: totalAmount,
      currency: this.izipayConfig.currency,
      customer: {
        email: orderData.email,
        first_name: orderData.shipping_address?.first_name,
        last_name: orderData.shipping_address?.last_name,
      },
      billing_address: orderData.shipping_address,
      order_reference: this.generateOrderReference(),
      return_url: window.location.origin + "/checkout/success/",
      cancel_url: window.location.origin + "/checkout/cancel/",
    };
  }

  generateOrderReference() {
    return (
      "ORDER-" + Date.now() + "-" + Math.random().toString(36).substr(2, 9)
    );
  }

  // Función para convertir monto al formato requerido por Izipay
  convertToAmountFormat(amount) {
    // Izipay espera el monto en centavos (por ejemplo: 45.55 -> 4555)
    const numericAmount = parseFloat(amount);
    const amountInCents = Math.round(numericAmount * 100);
    console.log(`💰 [convertToAmountFormat] Monto convertido: ${amount} (${typeof amount}) -> ${amountInCents} centavos`);
    return amountInCents;
  }

  // Método legacy actualizado
  async processPayment(paymentData) {
    console.log("🔄 Procesando pago con datos:", paymentData);

    try {
      // Convertir datos legacy al nuevo formato
      const orderData = {
        total: paymentData.amount,
        orderNumber: paymentData.order_reference,
      };

      const billingData = this.prepareBillingData(new FormData());

      // Usar el nuevo flujo
      const initialized = await this.initializeCheckout(orderData, billingData);

      if (initialized) {
        this.showPaymentForm();
        return { success: true, message: "Formulario de pago mostrado" };
      } else {
        return { success: false, message: "Error inicializando el pago" };
      }
    } catch (error) {
      console.error("❌ Error en processPayment:", error);
      return { success: false, message: error.message };
    }
  }

  // Función para convertir código de región a nombre
  getRegionNameFromCode(code) {
    const regionMap = {
      '01': 'Amazonas',
      '02': 'Áncash', 
      '03': 'Apurímac',
      '04': 'Arequipa',
      '05': 'Ayacucho',
      '06': 'Cajamarca',
      '07': 'Callao',
      '08': 'Cusco',
      '09': 'Huancavelica',
      '10': 'Huánuco',
      '11': 'Ica',
      '12': 'Junín',
      '13': 'La Libertad',
      '14': 'Lambayeque',
      '15': 'Lima',
      '16': 'Loreto',
      '17': 'Madre de Dios',
      '18': 'Moquegua',
      '19': 'Pasco',
      '20': 'Piura',
      '21': 'Puno',
      '22': 'San Martín',
      '23': 'Tacna',
      '24': 'Tumbes',
      '25': 'Ucayali'
    };

    if (!code) {
      console.log('⚠️ [getRegionNameFromCode] Código vacío, devolviendo "Lima"');
      return 'Lima';
    }

    // Si ya es un nombre (contiene letras), devolverlo tal como está
    if (/[a-zA-ZáéíóúñÁÉÍÓÚÑ]/.test(code)) {
      console.log(`✅ [getRegionNameFromCode] Ya es un nombre: ${code}`);
      return code;
    }

    // Convertir código numérico a string con formato correcto
    const normalizedCode = String(code).padStart(2, '0');
    const regionName = regionMap[normalizedCode];
    
    if (regionName) {
      console.log(`✅ [getRegionNameFromCode] Código convertido: ${code} (${normalizedCode}) -> ${regionName}`);
      return regionName;
    } else {
      console.warn(`⚠️ [getRegionNameFromCode] Código no encontrado: ${code} (${normalizedCode}), devolviendo código original`);
      return code;
    }
  }
}

// Exportar para uso global
window.IzipayHandler = IzipayHandler;
