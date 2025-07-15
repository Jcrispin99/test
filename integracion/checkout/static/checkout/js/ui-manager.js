// Manejo de la interfaz de usuario
class UIManager {
  constructor() {
    console.log('🎨 [UIManager] Inicializando UIManager...');
    this.initializeElements();
  }

  initializeElements() {
    this.cartElement = document.getElementById("cart");
    this.subtotalElement = document.getElementById("subtotal");
    this.totalElement = document.getElementById("total");
    this.form = document.getElementById("checkout-form");
    this.submitButton = this.form?.querySelector('button[type="submit"]');
    this.originalButtonText =
      this.submitButton?.textContent || "Completar pedido";

    console.log('🎨 [UIManager] Elementos encontrados:');
    console.log('  - cartElement:', this.cartElement);
    console.log('  - subtotalElement:', this.subtotalElement);
    console.log('  - totalElement:', this.totalElement);
    console.log('  - form:', this.form);
    console.log('  - submitButton:', this.submitButton);
  }

  renderCartItems(items) {
    console.log('🎨 [UIManager] renderCartItems llamado con:', items);
    console.log('🎨 [UIManager] cartElement actual:', this.cartElement);
    
    if (!this.cartElement) {
      console.error('❌ [UIManager] cartElement no encontrado! Reintentando...');
      this.initializeElements();
      if (!this.cartElement) {
        console.error('❌ [UIManager] cartElement sigue sin encontrarse después del reinicio');
        return;
      }
    }
    
    if (!items || items.length === 0) {
      console.log('⚠️ [UIManager] No hay items para renderizar');
      return;
    }

    let subtotal = 0;
    this.cartElement.innerHTML = "";
    console.log('🎨 [UIManager] Cart limpiado, iniciando renderizado...');

    items.forEach((item, index) => {
      console.log(`🎨 [UIManager] Procesando item ${index + 1}:`, item);
      subtotal += item.line_price;
      const itemHTML = this.createItemHTML(item);
      console.log(`🎨 [UIManager] HTML generado para item ${index + 1}:`, itemHTML);
      this.cartElement.insertAdjacentHTML("beforeend", itemHTML);
    });

    console.log('🎨 [UIManager] Subtotal calculado:', subtotal);
    this.updateTotals(subtotal);
    console.log('✅ [UIManager] Renderizado completado');
  }

  createItemHTML(item) {
    return `
      <div class="product-item">
        <div class="product-image">
          <img src="${
            item.image || "https://via.placeholder.com/60x60"
          }" alt="${item.name}" />
          <div class="quantity-badge">${item.quantity}</div>
        </div>
        <div class="product-details">
          <div class="product-name">${item.name}</div>
          <div class="product-variant">${item.sku || ""}</div>
        </div>
        <div class="product-price">S/ ${(item.line_price / 100).toFixed(
          2
        )}</div>
      </div>`;
  }

  updateTotals(subtotal) {
    const formattedSubtotal = `S/ ${(subtotal / 100).toFixed(2)}`;
    const formattedTotal = `PEN S/ ${(subtotal / 100).toFixed(2)}`;

    if (this.subtotalElement) {
      this.subtotalElement.textContent = formattedSubtotal;
    }
    if (this.totalElement) {
      this.totalElement.textContent = formattedTotal;
    }
  }

  prefillForm(customerInfo) {
    if (customerInfo.email) {
      const emailInput = this.form.querySelector('input[name="email"]');
      if (emailInput) emailInput.value = customerInfo.email;
    }

    if (customerInfo.customer) {
      const firstNameInput = this.form.querySelector(
        'input[name="first_name"]'
      );
      const lastNameInput = this.form.querySelector('input[name="last_name"]');

      if (firstNameInput && customerInfo.customer.first_name) {
        firstNameInput.value = customerInfo.customer.first_name;
      }
      if (lastNameInput && customerInfo.customer.last_name) {
        lastNameInput.value = customerInfo.customer.last_name;
      }
    }
  }

  setLoadingState(isLoading) {
    if (!this.submitButton) return;

    if (isLoading) {
      this.submitButton.textContent = "Procesando...";
      this.submitButton.disabled = true;
    } else {
      this.submitButton.textContent = this.originalButtonText;
      this.submitButton.disabled = false;
    }
  }

  clearCart() {
    this.cartElement.innerHTML = "";
    this.updateTotals(0);
  }

  showMessage(message, isError = false) {
    // Por ahora usamos alert, pero puedes mejorarlo con notificaciones más elegantes
    alert(message);
  }
}
