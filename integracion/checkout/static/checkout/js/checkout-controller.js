// Controlador principal que coordina Shopify, Izipay y UI
class CheckoutController {
  constructor() {
    this.shopifyHandler = new ShopifyHandler();
    this.izipayHandler = new IzipayHandler();
    this.uiManager = new UIManager();

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
    // Cargar datos de Shopify y renderizar
    const items = this.shopifyHandler.getOrderItems();
    const customerInfo = this.shopifyHandler.getCustomerInfo();

    this.uiManager.renderCartItems(items);
    this.uiManager.prefillForm(customerInfo);
  }

  setupEventListeners() {
    this.uiManager.form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await this.processOrder();
    });
  }

  async processOrder() {
    this.uiManager.setLoadingState(true);

    try {
      console.log("🚀 Iniciando proceso de orden...");

      // 1. Obtener datos del formulario
      const formData = new FormData(this.uiManager.form);
      const orderData = Object.fromEntries(formData.entries());

      // 2. Preparar orden para Shopify
      const shopifyOrder = this.shopifyHandler.prepareShopifyOrder(orderData);

      // 3. Crear orden en Shopify
      const shopifyResult = await this.createShopifyOrder(shopifyOrder);

      if (shopifyResult.success) {
        console.log("✅ Orden creada en Shopify exitosamente");

        // 4. Preparar datos para Izipay
        const totalAmount = this.shopifyHandler.calculateOrderTotal();
        const orderDataForIzipay = {
          total: totalAmount, // Ya viene como string con formato decimal
          orderNumber: `ORDER-${Date.now()}`,
        };

        const billingData = this.izipayHandler.prepareBillingData(formData);

        console.log("💳 Iniciando proceso de pago con Izipay...");

        // 5. Inicializar y mostrar formulario de Izipay
        const initialized = await this.izipayHandler.initializeCheckout(
          orderDataForIzipay,
          billingData
        );

        if (initialized) {
          // Mostrar formulario de pago
          this.izipayHandler.showPaymentForm((paymentResponse) => {
            this.handlePaymentCallback(paymentResponse, shopifyResult);
          });

          this.uiManager.showMessage(
            "Orden creada exitosamente. Completa tu pago..."
          );
        } else {
          throw new Error("No se pudo inicializar el formulario de pago");
        }
      } else {
        this.uiManager.showMessage(
          "Error: " + (shopifyResult.error || "Error desconocido"),
          true
        );
      }
    } catch (error) {
      console.error("❌ Error en el proceso:", error);
      this.uiManager.showMessage(
        "Error de conexión. Intenta nuevamente.",
        true
      );
    } finally {
      this.uiManager.setLoadingState(false);
    }
  }

  handlePaymentCallback(paymentResponse, shopifyResult) {
    console.log("🔄 Procesando callback de pago...", paymentResponse);

    if (paymentResponse && paymentResponse.success) {
      console.log("🎉 Pago completado exitosamente");

      // Mostrar mensaje de éxito
      this.uiManager.showMessage(
        "¡Pago realizado exitosamente! Tu orden ha sido procesada."
      );

      // Limpiar el checkout
      setTimeout(() => {
        this.clearCheckout();
      }, 3000);
    } else {
      console.log("❌ Error en el pago");
      this.uiManager.showMessage(
        "Error en el pago. Por favor, intenta nuevamente.",
        true
      );
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

    // Opcional: recargar la página o redireccionar
    // window.location.reload();
  }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Inicializando CheckoutController...");
  const checkoutApp = new CheckoutController();
});
