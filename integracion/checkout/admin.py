from django.contrib import admin
from .models import CheckoutOrder

@admin.register(CheckoutOrder)
class CheckoutOrderAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo CheckoutOrder.
    """
    list_display = (
        'id',
        'shopify_order_id',
        'izipay_order_id',
        'status',
        'izipay_payment_url',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields =  ('shopify_order_id', 'izipay_order_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('status',)
        }),
        ('Información de Integración', {
            'fields': ('shopify_order_id', 'izipay_order_id', 'izipay_payment_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
