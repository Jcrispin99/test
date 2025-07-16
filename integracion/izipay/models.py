from django.db import models
from django.db import transaction
from django.utils import timezone

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

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Izipay [{self.merchant_code}]"

class PaymentTransaction(models.Model):
    PAYMENT_STATES = [
        ('1', 'GENERADO'),
        ('3', 'TERMINADO_EXITO'),
        ('4', 'TERMINADO_ERROR'),
        ('5', 'EXPIRADO'),
        ('6', 'DESACTIVADO'),
    ]
    
    # IDs de identificación
    transaction_id = models.CharField(max_length=50, unique=True)  # ID de transacción Izipay
    shopify_order_id = models.CharField(max_length=50, blank=True, null=True)  # ID de orden Shopify
    order_number = models.CharField(max_length=100)  # Número de orden interno
    
    # Datos del Payment Link
    payment_link_id = models.CharField(max_length=100, blank=True, null=True)
    payment_link_url = models.URLField(blank=True, null=True)
    payment_link_state = models.CharField(max_length=2, choices=PAYMENT_STATES, default='1')
    
    # Datos financieros
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='PEN')
    
    # Datos del cliente
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=200)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    webhook_received_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'izipay_payment_transactions'
        
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.get_payment_link_state_display()}"
    
    @property
    def is_successful(self):
        return self.payment_link_state == '3'
    
    @property
    def is_failed(self):
        return self.payment_link_state in ['4', '5', '6']


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
