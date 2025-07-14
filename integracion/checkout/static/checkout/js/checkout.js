const payload = JSON.parse(
  decodeURIComponent(
    new URLSearchParams(window.location.search).get("data") || "{}"
  )
);

function renderCartItems() {
  const cartDiv = document.getElementById("cart");
  let subtotal = 0;
  if (!payload || !payload.items) return;

  payload.items.forEach((item) => {
    subtotal += item.line_price;
    const itemHTML = `
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
    cartDiv.insertAdjacentHTML("beforeend", itemHTML);
  });

  document.getElementById("subtotal").textContent = `S/ ${(
    subtotal / 100
  ).toFixed(2)}`;
  document.getElementById("total").textContent = `PEN S/ ${(
    subtotal / 100
  ).toFixed(2)}`;
}

function prefillFormData() {
  // Prellenar email si viene en los datos de la URL
  if (payload && payload.email) {
    const emailInput = document.querySelector('input[name="email"]');
    if (emailInput) {
      emailInput.value = payload.email;
    }
  }

  // También puedes prellenar otros campos si vienen en la URL
  if (payload && payload.customer) {
    const firstNameInput = document.querySelector('input[name="first_name"]');
    const lastNameInput = document.querySelector('input[name="last_name"]');

    if (firstNameInput && payload.customer.first_name) {
      firstNameInput.value = payload.customer.first_name;
    }
    if (lastNameInput && payload.customer.last_name) {
      lastNameInput.value = payload.customer.last_name;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  renderCartItems();
  prefillFormData();

  document
    .getElementById("checkout-form")
    .addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      const data = Object.fromEntries(formData.entries());

      data.email = document.querySelector('[name="email"]')?.value || "";
      data.items = payload.items || [];

      const submitBtn = this.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = "Procesando...";
      submitBtn.disabled = true;

      try {
        const response = await fetch("/checkout/process/", {
          // ✅ URL corregida
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
              .value,
          },
          body: JSON.stringify(data),
        });

        const result = await response.json();
        if (result.success) {
          alert("¡Pedido procesado exitosamente!");
          // ✅ Limpiar carrito después del éxito
          clearCart();
          // ✅ Opcional: redirigir a página de confirmación
          // window.location.href = '/checkout/success/';
        } else {
          alert("Error: " + (result.error || "Error desconocido"));
        }
      } catch (error) {
        console.error("Error:", error);
        alert("Error de conexión. Intenta nuevamente.");
      } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    });
});

// ✅ Nueva función para limpiar carrito
function clearCart() {
  // Limpiar el carrito visual
  const cartDiv = document.getElementById("cart");
  cartDiv.innerHTML = "";

  // Resetear totales
  document.getElementById("subtotal").textContent = "S/ 0.00";
  document.getElementById("total").textContent = "PEN S/ 0.00";

  // Limpiar datos del payload
  payload.items = [];

  // Opcional: actualizar URL para remover parámetros del carrito
  const url = new URL(window.location);
  url.searchParams.delete("data");
  window.history.replaceState({}, document.title, url.pathname);
}
