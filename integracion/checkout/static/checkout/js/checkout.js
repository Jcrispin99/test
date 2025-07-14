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

document.addEventListener("DOMContentLoaded", () => {
  renderCartItems();

  document
    .getElementById("checkout-form")
    .addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      const data = Object.fromEntries(formData.entries());

      // ✅ Forzamos la captura del correo electrónico manualmente
      data.email = document.querySelector('[name="email"]')?.value || "";
      data.items = payload.items || [];

      const submitBtn = this.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = "Procesando...";
      submitBtn.disabled = true;

      try {
        const response = await fetch("/api/checkout/process/", {
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
