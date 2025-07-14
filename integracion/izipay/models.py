from django.db import models

class IzipayCredential(models.Model):
    nombre = models.CharField(max_length=100, default="Configuración Principal")

    # API Token de sesión
    merchant_code = models.CharField("Código del Comercio", max_length=20)
    api_key = models.CharField("Clave API (Botón de Pagos)", max_length=100)

    # Firma
    hash_key = models.CharField("Clave HASH", max_length=100)

    # Clave pública
    public_key = models.TextField("Clave pública Izipay")

    # URL externa para redirección o callback
    return_url = models.URLField("URL de redirección", max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Izipay [{self.merchant_code}]"
