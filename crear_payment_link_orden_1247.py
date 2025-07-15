#!/usr/bin/env python
"""
Script para crear un payment link específico para la orden #1247 (6576565717406)
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'integracion'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
django.setup()

from izipay.models import PaymentTransaction, IzipayCredential
from shopify.models import ShopifyCredential
import requests
import json
from datetime import datetime, timedelta
import re

def crear_payment_link_para_orden():
    order_id = "6576565717406"  # Orden #1247 de la captura
    
    print(f"🔗 === CREANDO PAYMENT LINK PARA ORDEN {order_id} ===")
    
    # 1. Obtener información de la orden desde Shopify
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
        
        # Obtener datos de la orden
        order_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
        order_response = requests.get(order_url, headers=headers, timeout=30)
        
        if order_response.status_code == 200:
            order_data = order_response.json().get('order', {})
            
            print(f"✅ Orden encontrada en Shopify:")
            print(f"   Order Number: {order_data.get('name')}")
            print(f"   Total: {order_data.get('total_price')} {order_data.get('currency')}")
            print(f"   Customer Email: {order_data.get('email')}")
            print(f"   Financial Status: {order_data.get('financial_status')}")
            
            # Extraer datos para el payment link
            amount = float(order_data.get('total_price', 15.0))
            customer_email = order_data.get('email', 'marvinhectorcamposdeza@gmail.com')
            order_number = order_data.get('name', f'ORDER-{order_id}')
            customer_name = order_data.get('customer', {}).get('first_name', 'Cliente') + ' ' + order_data.get('customer', {}).get('last_name', '')
            
            # 2. Crear payment link
            payment_link_data = {
                'amount': amount,
                'orderNumber': order_number,
                'customerEmail': customer_email,
                'customerName': customer_name.strip(),
                'shopifyOrderId': order_id,  # ¡IMPORTANTE: Vincular con Shopify!
                'productDescription': f'Pago orden Shopify {order_number}'
            }
            
            print(f"\n🔄 Creando payment link con datos:")
            print(f"   Amount: {amount}")
            print(f"   Email: {customer_email}")
            print(f"   Order Number: {order_number}")
            print(f"   Shopify Order ID: {order_id}")
            
            # Llamar a la API local para crear el payment link
            payment_link_url = "http://localhost:8000/izipay/payment-link/"
            
            response = requests.post(payment_link_url, json=payment_link_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"\n✅ Payment Link creado exitosamente:")
                    print(f"   Payment Link URL: {result.get('paymentLink')}")
                    print(f"   Payment Link ID: {result.get('paymentLinkId')}")
                    print(f"   Transaction ID: {result.get('transactionId')}")
                    
                    # Verificar que se creó la transacción vinculada
                    transaction = PaymentTransaction.objects.filter(shopify_order_id=order_id).first()
                    if transaction:
                        print(f"\n✅ Transacción vinculada correctamente:")
                        print(f"   Transaction ID: {transaction.transaction_id}")
                        print(f"   Estado: {transaction.payment_link_state}")
                        
                        print(f"\n🎯 AHORA EL SISTEMA AUTOMÁTICO FUNCIONARÁ:")
                        print(f"   1. Cliente paga en: {result.get('paymentLink')}")
                        print(f"   2. Izipay envía webhook automáticamente")
                        print(f"   3. Sistema actualiza etiqueta y comentario")
                        print(f"   4. Orden se marca como pagada")
                        
                        return result.get('paymentLink')
                    else:
                        print(f"❌ Error: No se vinculó la transacción con Shopify")
                else:
                    print(f"❌ Error creando payment link: {result.get('error')}")
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"   Response: {response.text}")
                
        else:
            print(f"❌ Error obteniendo orden de Shopify: {order_response.status_code}")
            print(f"   Response: {order_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    crear_payment_link_para_orden()
    
    print(f"\n💡 === INSTRUCCIONES ===")
    print(f"1. ✅ Usa el payment link generado para realizar el pago")
    print(f"2. ✅ El webhook procesará automáticamente:")
    print(f"   • Actualizar etiqueta: pendiente → pagada")
    print(f"   • Agregar comentario con detalles del pago")
    print(f"   • Marcar orden como pagada en Shopify")
    print(f"3. ✅ Todo será automático, sin scripts manuales")

if __name__ == "__main__":
    main()
