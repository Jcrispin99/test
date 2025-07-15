from django.db import models
from django.db import transaction

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


class IzipayTransactionCounter(models.Model):
    """
    Modelo para manejar el contador de transactionId único
    """
    current_transaction_id = models.PositiveIntegerField(
        "ID de Transacción Actual", 
        default=100010,
        help_text="Último ID de transacción generado. Se incrementa automáticamente."
    )
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Contador de Transacciones Izipay"
        verbose_name_plural = "Contadores de Transacciones Izipay"
    
    def __str__(self):
        return f"Transaction Counter: {self.current_transaction_id}"
    
    @classmethod
    def get_next_transaction_id(cls):
        """
        Obtiene el siguiente transaction_id y lo incrementa automáticamente
        Usa transacción atómica para evitar duplicados
        """
        with transaction.atomic():
            counter, created = cls.objects.get_or_create(
                id=1,  # Solo mantenemos un registro
                defaults={'current_transaction_id': 100009}
            )
            
            # Obtener el ID actual
            current_id = counter.current_transaction_id
            
            # Incrementar para la próxima vez
            counter.current_transaction_id += 1
            counter.save()
            
            return str(current_id)
    
    def save(self, *args, **kwargs):
        # Asegurar que solo existe un registro
        if not self.pk and IzipayTransactionCounter.objects.exists():
            raise ValueError("Solo puede existir un contador de transacciones")
        return super().save(*args, **kwargs)
