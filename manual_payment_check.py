#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('integracion')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
django.setup()

from izipay.models import PaymentTransaction, IzipayCredential
import requests
import json

def check_payment_transactions():
    """Verificar todas las transacciones de pago y sus estados"""
    print("🔍 Verificando transacciones de pago...")
    print("=" * 60)
    
    transactions = PaymentTransaction.objects.all().order_by('-created_at')
    
    if not transactions:
        print("❌ No se encontraron transacciones")
        return
    
    for transaction in transactions:
        print(f"\n📋 Transacción ID: {transaction.transaction_id}")
        print(f"   🛒 Shopify Order ID: {transaction.shopify_order_id}")
        print(f"   🔗 Payment Link ID: {transaction.payment_link_id}")
        print(f"   📊 Estado: {transaction.payment_link_state} ({transaction.get_payment_link_state_display()})")
        print(f"   ✅ Es exitosa: {transaction.is_successful}")
        print(f"   ❌ Falló: {transaction.is_failed}")
        print(f"   📅 Creada: {transaction.created_at}")
        print(f"   🔔 Webhook recibido: {transaction.webhook_received_at}")
        
        # Verificar estado actual en Izipay
        if transaction.payment_link_id:
            current_state = check_izipay_status(transaction.payment_link_id)
            if current_state:
                print(f"   🌐 Estado actual en Izipay: {current_state}")
                if current_state != transaction.payment_link_state:
                    print(f"   ⚠️  DESINCRONIZADO! Local: {transaction.payment_link_state}, Izipay: {current_state}")

def check_izipay_status(payment_link_id):
    """Consultar el estado actual de un payment link en Izipay"""
    try:
        credential = IzipayCredential.objects.filter(is_active=True).first()
        if not credential:
            print("❌ No hay credenciales activas")
            return None
        
        transaction_id = f"100{str(datetime.now().microsecond)[:3]}"
        
        # 1. Generar token
        token_payload = {
            "requestSource": "ECOMMERCE", 
            "merchantCode": credential.merchant_code,
            "orderNumber": credential.merchant_code,
            "publicKey": credential.public_key,
            "amount": "0.00"
        }
        
        token_headers = {
            "transactionId": transaction_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        token_url = "https://sandbox-api-pw.izipay.pe/gateway/api/v1/proxy-cors/https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate"
        
        token_response = requests.post(token_url, json=token_payload, headers=token_headers, timeout=30)
        token_data = token_response.json()
        
        if token_response.status_code != 200 or token_data.get('code') != '00':
            print(f"❌ Error generando token: {token_data.get('message', 'Error desconocido')}")
            return None
        
        session_token = token_data.get('response', {}).get('token')
        
        # 2. Consultar Payment Link
        search_payload = {
            "paymentLinkId": payment_link_id,
            "merchantCode": credential.merchant_code,
            "languageUsed": "ESP"
        }
        
        search_headers = {
            "Authorization": f"Bearer {session_token}",
            "transactionId": transaction_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        search_url = "https://sandbox-api-pw.izipay.pe/gateway/api/v1/proxy-cors/https://sandbox-api-pw.izipay.pe/paymentlink/api/v1/process/search"
        
        search_response = requests.post(search_url, json=search_payload, headers=search_headers, timeout=30)
        search_data = search_response.json()
        
        if search_response.status_code == 200 and search_data.get('code') == '00':
            payment_link_info = search_data.get('response', {})
            return payment_link_info.get('state')
        else:
            print(f"❌ Error consultando Izipay: {search_data.get('message', 'Error desconocido')}")
            return None
            
    except Exception as e:
        print(f"❌ Error consultando estado: {e}")
        return None

def update_transaction_states():
    """Actualizar estados de transacciones consultando Izipay"""
    print("\n🔄 Actualizando estados desde Izipay...")
    print("=" * 60)
    
    transactions = PaymentTransaction.objects.filter(payment_link_id__isnull=False)
    
    for transaction in transactions:
        print(f"\n🔍 Verificando transacción {transaction.transaction_id}...")
        current_state = check_izipay_status(transaction.payment_link_id)
        
        if current_state and current_state != transaction.payment_link_state:
            old_state = transaction.payment_link_state
            transaction.payment_link_state = current_state
            transaction.save()
            
            print(f"✅ Estado actualizado: {old_state} → {current_state}")
            
            # Si el pago fue exitoso, simular actualización de Shopify
            if current_state == '3' and transaction.shopify_order_id:
                print(f"💰 Pago exitoso detectado! Orden Shopify: {transaction.shopify_order_id}")
                print("📦 (Aquí se actualizaría el estado en Shopify)")
        else:
            print(f"ℹ️  Sin cambios (estado actual: {current_state})")

def check_webhook_configuration():
    """Verificar la configuración del webhook"""
    print("\n🔗 Verificando configuración de webhook...")
    print("=" * 60)
    
    # Verificar que las URLs estén configuradas
    webhook_url = "http://tu-dominio.com/api/izipay/webhook/"  # Cambiar por tu URL real
    print(f"📡 URL del webhook: {webhook_url}")
    print("⚠️  Asegúrate de que esta URL esté configurada en Izipay")
    print("⚠️  Y que sea accesible desde internet (no localhost)")

if __name__ == "__main__":
    print("🚀 Iniciando verificación de transacciones...")
    print(f"📅 Fecha: {datetime.now()}")
    
    # 1. Verificar transacciones actuales
    check_payment_transactions()
    
    # 2. Actualizar estados desde Izipay
    update_transaction_states()
    
    # 3. Verificar configuración de webhook
    check_webhook_configuration()
    
    print("\n✅ Verificación completada!")
