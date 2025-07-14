from django.db import models

class ShopifyCredential(models.Model):
    store_name = models.CharField(max_length=255, help_text="Nombre de la tienda (sin .myshopify.com)")
    access_token = models.CharField(max_length=255, help_text="Token de acceso privado")
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    store_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL completa de la tienda")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.store_name}.myshopify.com"