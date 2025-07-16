from django.db import models

class CheckoutOrder(models.Model):
    """
    Modelo para almacenar la información de la orden de checkout
    que integra Shopify e Izipay.
    """

    shopify_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID de la orden generada en Shopify."
    )
    izipay_order_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID de la orden generada en Izipay."
    )
    status = models.IntegerField(
        default=0,
        choices=[(i, str(i)) for i in range(6)],  # Opciones de 0 a 5
        help_text="Estado actual de la orden."
    )
    izipay_payment_url = models.URLField(
        max_length=512,
        null=True,
        blank=True,
        help_text="URL de pago generada por Izipay."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Orden #{self.id} - Shopify ID: {self.shopify_order_id or 'N/A'}"

    class Meta:
        verbose_name = "Orden de Checkout"
        verbose_name_plural = "Órdenes de Checkout"
        ordering = ['-created_at']
