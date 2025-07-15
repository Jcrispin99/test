// Controlador principal que coordina Shopify, Izipay y UI
class CheckoutController {
  constructor() {
    this.shopifyHandler = new ShopifyHandler();
    this.izipayHandler = new IzipayHandler();
    this.uiManager = new UIManager();

    this.init();
  }

  init() {
    document.addEventListener("DOMContentLoaded", () => {
      this.loadInitialData();
      this.setupEventListeners();
    });
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
      // 1. Obtener datos del formulario
      const formData = new FormData(this.uiManager.form);
      const orderData = Object.fromEntries(formData.entries());

      // 2. Preparar orden para Shopify
      const shopifyOrder = this.shopifyHandler.prepareShopifyOrder(orderData);

      // 3. Crear orden en Shopify
      const shopifyResult = await this.createShopifyOrder(shopifyOrder);

      if (shopifyResult.success) {
        // 4. Si Shopify fue exitoso, preparar pago con Izipay
        const totalAmount = this.shopifyHandler.calculateOrderTotal();
        const izipayPayment = this.izipayHandler.prepareIzipayPayment(
          shopifyOrder,
          totalAmount
        );

        // 5. Por ahora solo mostramos éxito, luego implementarás Izipay
        this.uiManager.showMessage(
          "¡Orden creada en Shopify! Preparando pago..."
        );

        // TODO: Aquí irá la integración con Izipay
        const paymentResult = await this.izipayHandler.processPayment(
          izipayPayment
        );

        this.clearCheckout();
      } else {
        this.uiManager.showMessage(
          "Error: " + (shopifyResult.error || "Error desconocido"),
          true
        );
      }
    } catch (error) {
      console.error("Error en el proceso:", error);
      this.uiManager.showMessage(
        "Error de conexión. Intenta nuevamente.",
        true
      );
    } finally {
      this.uiManager.setLoadingState(false);
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
}

// Inicializar la aplicación
const checkoutApp = new CheckoutController();
