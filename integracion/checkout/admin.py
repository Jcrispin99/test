from django.contrib import admin
from .models import OrdenCheckout

@admin.register(OrdenCheckout)
class OrdenCheckoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'idord_shp', 'idord_izi', 'estado', 'created_at', 'updated_at')
    list_filter = ('estado', 'created_at')
    search_fields = ('idord_shp', 'idord_izi')
    readonly_fields = ('created_at', 'updated_at')
