#!/usr/bin/env python
"""
Script de diagnóstico para el problema del webhook automático
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

def diagnosticar_problema():
    print("🔍 === DIAGNÓSTICO DEL WEBHOOK AUTOMÁTICO ===")
    
    # 1. Verificar orden específica de la captura
    order_id_captura = '6576565717406'  # Orden #1247 de la captura
    
    print(f"\n1. 📊 Buscando transacciones para orden {order_id_captura}:")
    
    transactions = PaymentTransaction.objects.filter(shopify_order_id=order_id_captura)
    if transactions.exists():
        for t in transactions:
            print(f"   ✅ Transacción encontrada:")
            print(f"      Transaction ID: {t.transaction_id}")
            print(f"      Payment Link ID: {t.payment_link_id}")
            print(f"      Estado: {t.payment_link_state} ({t.get_payment_link_state_display()})")
            print(f"      Webhook recibido: {t.webhook_received_at}")
            print(f"      URL: {t.payment_link_url}")
            return t
    else:
        print(f"   ❌ No se encontraron transacciones para la orden {order_id_captura}")
    
    # 2. Buscar por order number también
    print(f"\n2. 📊 Buscando por order_number:")
    transactions_by_number = PaymentTransaction.objects.filter(order_number=order_id_captura)
    if transactions_by_number.exists():
        for t in transactions_by_number:
            print(f"   ✅ Transacción encontrada por order_number:")
            print(f"      Transaction ID: {t.transaction_id}")
            print(f"      Shopify Order ID: {t.shopify_order_id}")
            print(f"      Estado: {t.payment_link_state}")
            return t
    else:
        print(f"   ❌ No se encontraron transacciones por order_number")
    
    # 3. Mostrar todas las transacciones recientes
    print(f"\n3. 📊 Últimas 10 transacciones en BD:")
    all_recent = PaymentTransaction.objects.all().order_by('-created_at')[:10]
    for t in all_recent:
        print(f"   - Shopify: {t.shopify_order_id}, Order: {t.order_number}, Transaction: {t.transaction_id}, Estado: {t.payment_link_state}")
    
    return None

def verificar_configuracion():
    print(f"\n4. ⚙️ Verificando configuración:")
    
    # Verificar credenciales Izipay
    izipay_creds = IzipayCredential.objects.filter(is_active=True).first()
    if izipay_creds:
        print(f"   ✅ Credenciales Izipay: {izipay_creds.merchant_code}")
    else:
        print(f"   ❌ No hay credenciales Izipay activas")
    
    # Verificar credenciales Shopify
    shopify_creds = ShopifyCredential.objects.filter().first()
    if shopify_creds:
        print(f"   ✅ Credenciales Shopify: {shopify_creds.store_name}")
    else:
        print(f"   ❌ No hay credenciales Shopify")

def probar_webhook_manual():
    print(f"\n5. 🧪 Probando webhook manual:")
    
    # Buscar una transacción existente para probar
    transaction = PaymentTransaction.objects.first()
    if not transaction:
        print(f"   ❌ No hay transacciones para probar")
        return
    
    print(f"   📊 Usando transacción: {transaction.transaction_id}")
    
    # Simular webhook
    webhook_url = "http://localhost:8000/izipay/webhook/"
    webhook_data = {
        "transactionId": transaction.transaction_id,
        "state": "3",  # TERMINADO_EXITO
        "paymentLinkId": transaction.payment_link_id
    }
    
    try:
        response = requests.post(webhook_url, json=webhook_data, timeout=10)
        print(f"   📊 Respuesta webhook: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Webhook exitoso: {result.get('message')}")
            print(f"   🏷️ Etiqueta: {result.get('etiqueta_aplicada')}")
        else:
            print(f"   ❌ Error webhook: {response.text}")
    except Exception as e:
        print(f"   ❌ Error conectando webhook: {e}")

def main():
    transaction = diagnosticar_problema()
    verificar_configuracion()
    probar_webhook_manual()
    
    print(f"\n🎯 === POSIBLES SOLUCIONES ===")
    if not transaction:
        print(f"❌ PROBLEMA PRINCIPAL: No hay transacción vinculada a la orden #1247")
        print(f"")
        print(f"🔧 SOLUCIONES:")
        print(f"   1. Crear un nuevo payment link para esta orden")
        print(f"   2. Asegurarse de que el shopify_order_id se guarde correctamente")
        print(f"   3. Verificar que el proceso de creación vincule la orden")
    else:
        print(f"✅ Transacción encontrada")
        print(f"")
        print(f"🔧 VERIFICAR:")
        print(f"   1. Webhook URL configurada en Izipay")
        print(f"   2. Servidor accesible desde internet (ngrok)")
        print(f"   3. Estado actual del payment link en Izipay")

if __name__ == "__main__":
    main()
