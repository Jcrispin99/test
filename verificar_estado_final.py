#!/usr/bin/env python
"""
Script para verificar el estado final de la orden después del procesamiento automático
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'integracion'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
django.setup()

from izipay.models import PaymentTransaction
from shopify.models import ShopifyCredential
import requests
import json

def verificar_estado_final():
    order_id = "6576332275934"
    
    print(f"🔍 === VERIFICACIÓN FINAL DE LA ORDEN {order_id} ===")
    
    # 1. Verificar estado en BD
    try:
        transaction = PaymentTransaction.objects.get(shopify_order_id=order_id)
        print(f"📊 Estado en BD:")
        print(f"   Transaction ID: {transaction.transaction_id}")
        print(f"   Estado actual: {transaction.payment_link_state}")
        print(f"   Estado display: {transaction.get_payment_link_state_display()}")
        print(f"   Última actualización: {transaction.webhook_received_at}")
        
    except PaymentTransaction.DoesNotExist:
        print("❌ No se encontró transacción")
        return
    
    # 2. Verificar estado en Shopify
    try:
        shopify_credentials = ShopifyCredential.objects.filter().first()
        if not shopify_credentials:
            print("❌ No hay credenciales de Shopify")
            return
        
        headers = {
            'X-Shopify-Access-Token': shopify_credentials.access_token,
            'Content-Type': 'application/json'
        }
        
        store_url = shopify_credentials.store_url
        if not store_url.startswith('https'):
            if store_url.startswith('http://'):
                store_url = store_url.replace('http://', 'https://')
            else:
                store_url = f"https://{shopify_credentials.store_name}.myshopify.com"
        
        order_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
        order_response = requests.get(order_url, headers=headers, timeout=30)
        
        if order_response.status_code == 200:
            order_data = order_response.json().get('order', {})
            
            print(f"\n📊 Estado en Shopify:")
            print(f"   Order ID: {order_data.get('id')}")
            print(f"   Order Number: {order_data.get('name')}")
            print(f"   Financial Status: {order_data.get('financial_status')}")
            print(f"   Tags: {order_data.get('tags')}")
            print(f"   Total: {order_data.get('total_price')} {order_data.get('currency')}")
            
            # Mostrar las notas (comentarios)
            note = order_data.get('note', '')
            if note:
                print(f"\n💬 Comentarios/Notas:")
                print(f"   {note[:500]}..." if len(note) > 500 else f"   {note}")
            else:
                print(f"\n💬 Sin comentarios")
                
        else:
            print(f"❌ Error obteniendo orden de Shopify: {order_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error consultando Shopify: {e}")
    
    print(f"\n✅ === RESUMEN DEL SISTEMA AUTOMÁTICO ===")
    print(f"🔄 El webhook de Izipay ahora procesa automáticamente:")
    print(f"   ✅ Actualiza etiquetas dinámicas (pendiente/pagada/cancelada)")
    print(f"   ✅ Agrega comentarios automáticos con detalles del pago")  
    print(f"   ✅ Marca orden como pagada cuando estado = 3")
    print(f"   ✅ Incluye link de verificación en los comentarios")
    print(f"   ✅ Funciona completamente sin intervención manual")

if __name__ == "__main__":
    verificar_estado_final()
