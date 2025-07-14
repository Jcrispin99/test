// Manejo específico para integración con Izipay
class IzipayHandler {
  constructor() {
    this.izipayConfig = {
      // Aquí irán las configuraciones de Izipay cuando las implementes
      apiUrl: "/izipay/process/",
      currency: "PEN",
    };
  }

  // Preparar datos específicos para Izipay
  prepareIzipayPayment(orderData, totalAmount) {
    return {
      amount: totalAmount, // en centavos
      currency: this.izipayConfig.currency,
      customer: {
        email: orderData.email,
        first_name: orderData.shipping_address.first_name,
        last_name: orderData.shipping_address.last_name,
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

  // Método para cuando implementes el pago con Izipay
  async processPayment(paymentData) {
    try {
      const response = await fetch(this.izipayConfig.apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
            .value,
        },
        body: JSON.stringify(paymentData),
      });

      return await response.json();
    } catch (error) {
      console.error("Error procesando pago con Izipay:", error);
      throw error;
    }
  }

  // Generar configuración para Izipay según documentación oficial
  generateIzipayConfig(orderData, totalAmount) {
    const transactionId = this.generateTransactionId();
    
    return {
      config: {
        transactionId: transactionId,
        action: 'pay',
        merchantCode: this.config.merchantCode,
        order: {
          orderNumber: transactionId,
          currency: this.config.currency,
          amount: (totalAmount / 100).toFixed(2), // Convertir de centavos
          processType: 'AT',
          merchantBuyerId: this.config.merchantCode,
          dateTimeTransaction: Date.now() + '000',
        },
        billing: {
          firstName: orderData.shipping_address.first_name,
          lastName: orderData.shipping_address.last_name,
          email: orderData.email,
          phoneNumber: '', // Agregar campo teléfono al formulario
          street: orderData.shipping_address.address1,
          city: orderData.shipping_address.city,
          state: orderData.shipping_address.province,
          country: 'PE',
          postalCode: orderData.shipping_address.zip,
          documentType: 'DNI', // Agregar campo documento al formulario
          document: '', // Agregar campo documento al formulario
        },
        render: {
          typeForm: 'pop-up' // Modo popup según tu preferencia
        }
      }
    };
  }

  // Solicitar token de sesión al backend
  async requestSessionToken(iziConfig) {
    try {
      const response = await fetch(this.config.tokenEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
          transactionId: iziConfig.config.transactionId,
          orderNumber: iziConfig.config.order.orderNumber,
          amount: iziConfig.config.order.amount
        })
      });
      
      const result = await response.json();
      return result.token;
    } catch (error) {
      console.error('Error obteniendo token de Izipay:', error);
      throw error;
    }
  }

  // Procesar pago con Izipay
  async processPayment(orderData, totalAmount) {
    try {
      // 1. Generar configuración
      const iziConfig = this.generateIzipayConfig(orderData, totalAmount);
      
      // 2. Obtener token de sesión
      const sessionToken = await this.requestSessionToken(iziConfig);
      
      // 3. Inicializar Izipay
      const checkout = new Izipay({ config: iziConfig });
      
      // 4. Mostrar formulario popup
      return new Promise((resolve, reject) => {
        const callbackResponsePayment = (response) => {
          if (response.status === 'PAID') {
            resolve(response);
          } else {
            reject(new Error('Pago no completado'));
          }
        };
        
        checkout.LoadForm({
          authorization: sessionToken,
          keyRSA: 'TU_KEY_RSA', // Configurar en settings
          callbackResponse: callbackResponsePayment
        });
      });
      
    } catch (error) {
      console.error('Error procesando pago con Izipay:', error);
      throw error;
    }
  }

  generateTransactionId() {
    return 'TXN-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  }
}
