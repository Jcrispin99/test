# izipay/admin.py
from django.contrib import admin
from .models import IzipayCredential, IzipayTransactionCounter

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
