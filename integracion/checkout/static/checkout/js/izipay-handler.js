// Manejo específico para integración con Izipay
class IzipayHandler {
  constructor() {
    this.checkout = null;
    this.token = null;
    this.izipayConfig = {
      apiUrl: "/izipay/generate-token/",
      currency: "PEN",
      merchantCode: "4004396",
      publicKey: "VErethUtraQuxas57wuMuquprADrAHAb",
    };
  }

  async generateToken(orderData) {
    try {
      console.log("🔄 Generando token de Izipay...", orderData);

      const response = await fetch(this.izipayConfig.apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
            .value,
        },
        body: JSON.stringify({
          amount: orderData.total,
          orderNumber: orderData.orderNumber || `ORDER-${Date.now()}`,
        }),
      });

      const data = await response.json();

      if (data.success) {
        this.token = data.token;
        console.log("✅ Token generado exitosamente");
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

      // Generar token
      const tokenData = await this.generateToken(orderData);

      // Configurar SDK según documentación oficial de Izipay
      const iziConfig = {
        transactionId: String(tokenData.transactionId),
        action: "pay",
        merchantCode: String(this.izipayConfig.merchantCode),
        order: {
          orderNumber: String(tokenData.orderNumber),
          showAmount: true,
          currency: this.izipayConfig.currency,
          amount: String(tokenData.amount),
          payMethod: "all",
          channel: "web",
          processType: "AT",
          merchantBuyerId: String(this.izipayConfig.merchantCode),
          dateTimeTransaction: String(Date.now()) + "000",
        },
        billing: billingData,
        render: {
          typeForm: "embedded",
          container: "izipay-form-container",
          showButtonProcessForm: true,
        },
      };

      console.log("⚙️ Configuración del SDK:", iziConfig);

      // Verificar que el SDK esté disponible
      if (typeof Izipay === "undefined") {
        throw new Error("SDK de Izipay no está cargado");
      }

      // Inicializar SDK según documentación oficial
      this.checkout = new Izipay({ config: iziConfig });
      console.log("✅ Checkout inicializado correctamente");
      return true;
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

      this.checkout.LoadForm({
        authorization: this.token,
        keyRSA: this.izipayConfig.publicKey,
        callbackResponse:
          callbackResponse || this.handlePaymentResponse.bind(this),
      });

      console.log("✅ Formulario de pago mostrado");
    } catch (error) {
      console.error("❌ Error mostrando formulario:", error);
      throw error;
    }
  }

  handlePaymentResponse(response) {
    console.log("💳 Respuesta del pago recibida:", response);

    // Verificar si el pago fue exitoso
    if (response && response.success) {
      console.log("✅ Pago exitoso");
      // Aquí puedes agregar lógica adicional para manejar el éxito
      this.onPaymentSuccess(response);
    } else {
      console.log("❌ Pago fallido o cancelado");
      this.onPaymentError(response);
    }
  }

  onPaymentSuccess(response) {
    // Mostrar mensaje de éxito
    alert("¡Pago realizado exitosamente!");

    // Aquí puedes agregar:
    // - Redirección a página de éxito
    // - Envío de confirmación
    // - Limpieza del carrito
    console.log("🎉 Procesando pago exitoso...", response);
  }

  onPaymentError(response) {
    // Mostrar mensaje de error
    alert("Error en el pago. Por favor, intenta nuevamente.");
    console.log("💥 Error en el pago:", response);
  }

  // Método para preparar datos de billing desde el formulario
  prepareBillingData(formData) {
    return {
      firstName: formData.get("first_name") || "Test",
      lastName: formData.get("last_name") || "User",
      email: formData.get("email") || "test@example.com",
      phoneNumber: formData.get("phone") || "987654321",
      street: formData.get("address1") || "Av. Test 123",
      city: formData.get("city") || "Lima",
      state: formData.get("province") || "Lima",
      country: "PE",
      postalCode: formData.get("zip") || "15001",
      documentType: "DNI",
      document: formData.get("document") || "12345678",
    };
  }

  // Método legacy para compatibilidad
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
}

// Exportar para uso global
window.IzipayHandler = IzipayHandler;
