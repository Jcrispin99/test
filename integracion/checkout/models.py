from django.db import models

class OrdenCheckout(models.Model):
    ESTADO_CHOICES = [
        (1, 'Iniciado'),
        (2, 'Creado en Shopify'),
        (3, 'Link de pago generado'),
        (4, 'Pagado'),
        (5, 'Error'),
    ]

    idord_shp = models.CharField(max_length=255, null=True, blank=True)
    idord_izi = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    estado = models.IntegerField(choices=ESTADO_CHOICES, default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Orden #{self.id} - Estado: {self.get_estado_display()}"
