class CheckoutController {
  constructor() {
    this.shopifyHandler = new ShopifyHandler();
    this.izipayHandler = new IzipayHandler();
    this.uiManager = new UIManager();
    this.isProcessing = false;
    this.init();
  }

  init() {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => {
        this.loadInitialData();
        this.setupEventListeners();
      });
    } else {
      this.loadInitialData();
      this.setupEventListeners();
    }
  }

  loadInitialData() {
    const items = this.shopifyHandler.getOrderItems();
    const customerInfo = this.shopifyHandler.getCustomerInfo();

    this.uiManager.renderCartItems(items);
    this.uiManager.prefillForm(customerInfo);
    this.shopifyHandler.autoFillForm();
  }

  setupEventListeners() {
    this.uiManager.form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await this.processOrder();
    });
  }

  async processOrder() {
    if (this.isProcessing) {
      console.log("⚠️ Orden ya en proceso, ignorando envío duplicado");
      return;
    }

    this.isProcessing = true;
    this.uiManager.setLoadingState(true);

    try {
      const formData = new FormData(this.uiManager.form);
      const orderData = Object.fromEntries(formData.entries());
      const shopifyOrder = this.shopifyHandler.prepareShopifyOrder(orderData);
      const shopifyResult = await this.createShopifyOrder(shopifyOrder);

      if (shopifyResult.success) {
        const totalAmount = this.shopifyHandler.calculateOrderTotal();
        const orderDataForIzipay = {
          total: totalAmount,
          orderNumber: `ORDER-${Date.now()}`,
          productDescription: `Orden de checkout - ${new Date().toLocaleDateString()}`,
        };

        const billingData = this.prepareBillingData(formData);
        const shippingData = this.prepareShippingData(formData);

        const paymentLinkResult = await this.izipayHandler.generatePaymentLink(
          orderDataForIzipay,
          billingData,
          shippingData
        );

        if (paymentLinkResult.success && paymentLinkResult.paymentLink) {
          this.uiManager.showMessage("Redirigiendo al procesador de pagos...", "success");
        } else {
          throw new Error("No se pudo generar el enlace de pago");
        }
      } else {
        this.uiManager.showMessage("Error: " + (shopifyResult.error || "Error desconocido"), true);
      }
    } catch (error) {
      console.error("❌ Error en el proceso:", error);
      this.uiManager.showMessage("Error de conexión. Intenta nuevamente.", true);
    } finally {
      this.uiManager.setLoadingState(false);
      this.isProcessing = false;
    }
  }

  handlePaymentCallback(paymentResponse, shopifyResult) {
    if (paymentResponse && paymentResponse.success) {
      this.uiManager.showMessage("¡Pago realizado exitosamente! Tu orden ha sido procesada.");
      setTimeout(() => {
        this.clearCheckout();
      }, 3000);
    } else {
      this.uiManager.showMessage("Error en el pago. Por favor, intenta nuevamente.", true);
    }
  }

  async createShopifyOrder(orderData) {
    try {
      const response = await fetch("/checkout/process/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
            .value,
        },
        body: JSON.stringify(orderData),
      });

      return await response.json();
    } catch (error) {
      console.error("Error creando orden en Shopify:", error);
      throw error;
    }
  }

  clearCheckout() {
    this.uiManager.clearCart();
    this.shopifyHandler.clearShopifyData();
  }

  prepareBillingData(formData) {
    return {
      firstName: formData.get('first_name') || '',
      lastName: formData.get('last_name') || '',
      email: formData.get('email') || '',
      phone: formData.get('phone') || '',
      address: formData.get('address') || '',
      district: formData.get('district') || '',
      city: formData.get('city') || '',
      region: formData.get('region') || '',
      zipCode: formData.get('zip_code') || ''
    };
  }

  prepareShippingData(formData) {
    const deliveryMethod = formData.get('delivery_method');
    
    if (deliveryMethod === 'shipping') {
      return {
        firstName: formData.get('shipping_first_name') || formData.get('first_name') || '',
        lastName: formData.get('shipping_last_name') || formData.get('last_name') || '',
        phone: formData.get('shipping_phone') || formData.get('phone') || '',
        address: formData.get('shipping_address') || '',
        district: formData.get('shipping_district') || '',
        city: formData.get('shipping_city') || '',
        region: formData.get('shipping_region') || '',
        zipCode: formData.get('shipping_zip_code') || ''
      };
    }
    
    return {};
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (!window.checkoutController) {
    window.checkoutController = new CheckoutController();
  } else {
    console.warn("⚠️ CheckoutController ya está inicializado");
  }
});
