class UIManager {
  constructor() {
    this.currentSubtotal = 0;
    this.initializeElements();
    this.initializeDeliveryToggle();
    this.setupEventListeners();
  }

  initializeElements() {
    this.cartElement = document.getElementById("cart");
    this.subtotalElement = document.getElementById("subtotal");
    this.totalElement = document.getElementById("total");
    this.form = document.getElementById("checkout-form");
    this.submitButton = this.form?.querySelector('button[type="submit"]');
    this.originalButtonText =
    this.submitButton?.textContent || "Completar pedido";
  }

  initializeDeliveryToggle() {
    this.deliveryToggle = new DeliveryToggle();
  }

  renderCartItems(items) {
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

    items.forEach((item, index) => {
      subtotal += item.line_price;
      const itemHTML = this.createItemHTML(item);
      this.cartElement.insertAdjacentHTML("beforeend", itemHTML);
    });

    this.currentSubtotal = subtotal;
    this.updateTotals(subtotal);
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
    
    let shippingCost = 0;
    const shippingCostElement = document.getElementById("shipping-cost");
    if (shippingCostElement && shippingCostElement.textContent.includes("S/")) {
      const costText = shippingCostElement.textContent.replace("S/", "").trim();
      shippingCost = parseFloat(costText) * 100;
    }
    
    const total = subtotal + shippingCost;
    const formattedTotal = `PEN S/ ${(total / 100).toFixed(2)}`;

    if (this.subtotalElement) {
      this.subtotalElement.textContent = formattedSubtotal;
    }
    if (this.totalElement) {
      this.totalElement.textContent = formattedTotal;
    }
  }

  prefillForm(customerInfo) {
    if (customerInfo.email) {
      const emailInput = this.form.querySelector('#email') || this.form.querySelector('input[name="email"]');
      if (emailInput) {
        emailInput.value = customerInfo.email;
      }
    }

    if (customerInfo.customer) {
      this.fillAddressFields(customerInfo.customer);
    }
  }

  fillAddressFields(customer) {
    const firstNameInput = document.querySelector('#first_name') || document.querySelector('input[name="first_name"]');
    const lastNameInput = document.querySelector('#last_name') || document.querySelector('input[name="last_name"]');
    const dniInput = document.querySelector('#dni') || document.querySelector('input[name="dni"]');
    const address1Input = document.querySelector('#address1') || document.querySelector('input[name="address1"]');
    const address2Input = document.querySelector('#address2') || document.querySelector('input[name="address2"]');
    const cityInput = document.querySelector('#city') || document.querySelector('input[name="city"]');
    const zipInput = document.querySelector('#zip') || document.querySelector('input[name="zip"]');
    const phoneInput = document.querySelector('#phone') || document.querySelector('input[name="phone"]');
    const provinceSelect = document.querySelector('#province') || document.querySelector('select[name="province"]');

    if (firstNameInput && customer.first_name) {
      firstNameInput.value = customer.first_name;
    }
    
    if (lastNameInput && customer.last_name) {
      lastNameInput.value = customer.last_name;
    }

    if (dniInput && customer.dni) {
      dniInput.value = customer.dni;
    }

    if (customer.address) {
      if (address1Input && customer.address.address1) {
        address1Input.value = customer.address.address1;
      }
      
      if (address2Input && customer.address.address2) {
        address2Input.value = customer.address.address2;
      }
      
      if (cityInput && customer.address.city) {
        cityInput.value = customer.address.city;
      }
      
      if (zipInput && customer.address.zip) {
        zipInput.value = customer.address.zip;
      }

      if (provinceSelect && customer.address.province) {
        const provinceName = customer.address.province.toLowerCase();
        const options = provinceSelect.querySelectorAll('option');
        
        options.forEach(option => {
          if (option.value.toLowerCase() === provinceName || 
              option.textContent.toLowerCase().includes(provinceName)) {
            option.selected = true;
          }
        });
      }
    }

    if (phoneInput && customer.phone) {
      phoneInput.value = customer.phone;
    }

    setTimeout(() => {
      if (window.peruRegions && window.peruRegions.triggerAutoSelect) {
        window.peruRegions.triggerAutoSelect();
      }
    }, 100);
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
    alert(message);
  }

  setupEventListeners() {
    document.addEventListener('shippingCostChanged', () => {
      this.updateTotals(this.currentSubtotal);
    });
  }
}
