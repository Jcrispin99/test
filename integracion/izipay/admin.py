# izipay/admin.py
from django.contrib import admin
from .models import IzipayCredential, IzipayTransactionCounter, PaymentTransaction

@admin.register(IzipayCredential)
class IzipayCredentialAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'merchant_code', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('nombre', 'merchant_code')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre',)
        }),
        ('Credenciales API', {
            'fields': ('merchant_code', 'api_key', 'public_key')
        }),
        ('Configuración', {
            'fields': ('hash_key', 'return_url')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(IzipayTransactionCounter)
class IzipayTransactionCounterAdmin(admin.ModelAdmin):
    list_display = ('current_transaction_id', 'last_updated', 'created_at')
    readonly_fields = ('last_updated', 'created_at')
    
    fieldsets = (
        ('Contador', {
            'fields': ('current_transaction_id',),
            'description': 'El próximo transaction_id será: current_transaction_id + 1'
        }),
        ('Timestamps', {
            'fields': ('last_updated', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Solo permitir un registro
        return not IzipayTransactionCounter.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar el contador
        return False

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'shopify_order_id', 'order_number', 'payment_link_state_display', 'amount', 'currency', 'customer_email', 'created_at', 'is_successful')
    list_filter = ('payment_link_state', 'currency', 'created_at', 'webhook_received_at')
    search_fields = ('transaction_id', 'shopify_order_id', 'order_number', 'customer_email', 'customer_name')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at', 'webhook_received_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Identificación', {
            'fields': ('transaction_id', 'shopify_order_id', 'order_number')
        }),
        ('Payment Link', {
            'fields': ('payment_link_id', 'payment_link_url', 'payment_link_state')
        }),
        ('Información Financiera', {
            'fields': ('amount', 'currency')
        }),
        ('Cliente', {
            'fields': ('customer_email', 'customer_name')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at', 'webhook_received_at'),
            'classes': ('collapse',)
        }),
    )
    
    def payment_link_state_display(self, obj):
        return obj.get_payment_link_state_display()
    payment_link_state_display.short_description = 'Estado'
    
    def is_successful(self, obj):
        return obj.is_successful
    is_successful.boolean = True
    is_successful.short_description = 'Exitoso'
