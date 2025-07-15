class DeliveryToggle {
    constructor() {
        this.shippingRadio = null;
        this.pickupRadio = null;
        this.shippingFields = null;
        this.pickupInfo = null;
        this.deliveryOptions = null;
        this.shippingCostElement = null;
        this.shippingMethodText = null;
        this.storeOptions = null;
        this.storeRadios = null;

        this.init();
    }

    init() {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", () =>
                this.initializeElements()
            );
        } else {
            this.initializeElements();
        }
    }

    initializeElements() {
        this.shippingRadio = document.getElementById("shipping");
        this.pickupRadio = document.getElementById("pickup");
        this.shippingFields = document.getElementById("shipping-fields");
        this.pickupInfo = document.getElementById("pickup-info");
        this.deliveryOptions = document.querySelectorAll(".delivery-option");
        this.shippingCostElement = document.getElementById("shipping-cost");
        this.shippingMethodText = document.getElementById("shipping-method-text");

        if (
            !this.shippingRadio ||
            !this.pickupRadio ||
            !this.shippingFields ||
            !this.pickupInfo
        ) {
            console.error(
                "❌ [DeliveryToggle] No se encontraron todos los elementos necesarios"
            );
            return;
        }

        this.setupEventListeners();
        this.setInitialState();
        this.setupStoreEventListeners();
    }

    setupEventListeners() {
        this.shippingRadio.addEventListener("change", () =>
            this.handleDeliveryChange()
        );
        this.pickupRadio.addEventListener("change", () =>
            this.handleDeliveryChange()
        );

        this.deliveryOptions.forEach((option) => {
            option.addEventListener("click", (e) => {
                if (e.target.type !== "radio") {
                    const radio = option.querySelector('input[type="radio"]');
                    if (radio) {
                        radio.checked = true;
                        this.handleDeliveryChange();
                    }
                }
            });
        });
    }

    setupStoreEventListeners() {
        const storeOptions = document.querySelectorAll(".store-option");
        const storeRadios = document.querySelectorAll('input[name="pickup_store"]');

        storeRadios.forEach((radio) => {
            radio.addEventListener("change", () => this.handleStoreChange());
        });

        storeOptions.forEach((option) => {
            option.addEventListener("click", (e) => {
                if (e.target.type === "radio") return;
                
                const radio = option.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                    this.handleStoreChange();
                }
            });
        });
    }

    handleDeliveryChange() {
        this.updateVisualState();
        this.toggleFields();
        this.updateRequiredFields();
        this.updateShippingCost();
    }

    updateVisualState() {
        this.deliveryOptions.forEach((option) => {
            option.classList.remove("selected");
        });

        if (this.shippingRadio.checked) {
            this.shippingRadio.closest(".delivery-option").classList.add("selected");
        } else if (this.pickupRadio.checked) {
            this.pickupRadio.closest(".delivery-option").classList.add("selected");
        }
    }

    toggleFields() {
        if (this.shippingRadio.checked) {
            this.shippingFields.style.display = "block";
            this.pickupInfo.style.display = "none";
        } else {
            this.shippingFields.style.display = "none";
            this.pickupInfo.style.display = "block";
            setTimeout(() => {
                this.setupStoreEventListeners();
                this.updateStoreVisualState();
            }, 50);
        }
    }

    updateRequiredFields() {
        const requiredFields =
            this.shippingFields.querySelectorAll("input, select");

        if (this.shippingRadio.checked) {
            const fieldsToRequire = this.shippingFields.querySelectorAll(
                'input[name="first_name"], input[name="last_name"], input[name="address1"], input[name="city"], input[name="zip"], select[name="province"]'
            );
            fieldsToRequire.forEach((field) => (field.required = true));
        } else {
            requiredFields.forEach((field) => (field.required = false));
        }
    }

    updateShippingCost() {
        if (!this.shippingCostElement || !this.shippingMethodText) return;

        if (this.shippingRadio.checked) {
            this.shippingMethodText.textContent = "Envío";
            this.shippingCostElement.textContent = "S/ 6.00";
        } else if (this.pickupRadio.checked) {
            this.shippingMethodText.textContent = "Retiro en tienda";
            this.shippingCostElement.textContent = "GRATIS";
        }

        this.notifyTotalUpdate();
    }

    notifyTotalUpdate() {
        const event = new CustomEvent('shippingCostChanged');
        document.dispatchEvent(event);
    }

    setInitialState() {
        this.handleDeliveryChange();
        setTimeout(() => {
            this.updateStoreVisualState();
        }, 100);
    }

    selectShipping() {
        if (this.shippingRadio) {
            this.shippingRadio.checked = true;
            this.handleDeliveryChange();
        }
    }

    selectPickup() {
        if (this.pickupRadio) {
            this.pickupRadio.checked = true;
            this.handleDeliveryChange();
        }
    }

    handleStoreChange() {
        this.updateStoreVisualState();
    }

    updateStoreVisualState() {
        const storeOptions = document.querySelectorAll(".store-option");
        
        storeOptions.forEach((option) => {
            option.classList.remove("selected");
        });

        const selectedStoreRadio = document.querySelector('input[name="pickup_store"]:checked');
        if (selectedStoreRadio) {
            const storeOption = selectedStoreRadio.closest(".store-option");
            if (storeOption) {
                storeOption.classList.add("selected");
            }
        } else {
            console.log("⚠️ [DeliveryToggle] No se encontró radio button seleccionado");
        }
    }
}

window.DeliveryToggle = DeliveryToggle;
