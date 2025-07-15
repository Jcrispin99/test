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

def check_new_transaction():
    """Verificar la nueva transacción específica"""
    transaction_id = "100896"
    payment_link_id = "c55e5e150b114da3b414341d7f9a0910"
    
    try:
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
        print(f"🔍 Verificando transacción: {transaction_id}")
        print(f"   Shopify Order: {transaction.shopify_order_id}")
        print(f"   Payment Link ID: {transaction.payment_link_id}")
        print(f"   Estado actual en BD: {transaction.payment_link_state}")
        
        # Consultar estado en Izipay
        current_state = check_izipay_status_detailed(payment_link_id)
        return transaction, current_state
        
    except PaymentTransaction.DoesNotExist:
        print(f"❌ Transacción {transaction_id} no encontrada")
        return None, None

def check_izipay_status_detailed(payment_link_id):
    """Consultar estado detallado en Izipay"""
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
        
        print("🔑 Generando token...")
        token_response = requests.post(token_url, json=token_payload, headers=token_headers, timeout=30)
        token_data = token_response.json()
        
        if token_response.status_code != 200 or token_data.get('code') != '00':
            print(f"❌ Error generando token: {token_data.get('message', 'Error desconocido')}")
            return None
        
        session_token = token_data.get('response', {}).get('token')
        print(f"✅ Token generado")
        
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
        
        print(f"🔍 Consultando Payment Link...")
        search_response = requests.post(search_url, json=search_payload, headers=search_headers, timeout=30)
        search_data = search_response.json()
        
        print(f"📊 Estado en Izipay:")
        if search_response.status_code == 200 and search_data.get('code') == '00':
            payment_link_info = search_data.get('response', {})
            state = payment_link_info.get('state')
            print(f"   Estado: {state}")
            if state == '1':
                print("   📝 GENERADO - Pago no completado")
            elif state == '3':
                print("   💰 TERMINADO_EXITO - ¡Pago completado!")
            return payment_link_info
        else:
            print(f"❌ Error consultando Izipay: {search_data.get('message', 'Error desconocido')}")
            return None
            
    except Exception as e:
        print(f"❌ Error consultando estado: {e}")
        import traceback
        traceback.print_exc()
        return None

def simulate_webhook_if_needed(transaction, izipay_data):
    """Simular webhook si el pago fue exitoso pero no se recibió"""
    if not izipay_data or not transaction:
        return False
        
    izipay_state = izipay_data.get('state')
    
    if izipay_state == '3' and transaction.payment_link_state != '3':
        print(f"\n🔔 ¡Pago exitoso detectado en Izipay pero no actualizado localmente!")
        print(f"   Estado local: {transaction.payment_link_state}")
        print(f"   Estado Izipay: {izipay_state}")
        print(f"   Simulando webhook...")
        
        # Simular webhook
        webhook_data = {
            "transactionId": transaction.transaction_id,
            "paymentLinkId": transaction.payment_link_id,
            "state": "3",
            "paymentLinkState": "3",
            "amount": "15.00",
            "currency": "PEN",
            "merchantCode": "4004345",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            webhook_url = "http://127.0.0.1:8000/izipay/webhook/"
            response = requests.post(
                webhook_url, 
                json=webhook_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Webhook simulado exitosamente!")
                print(f"📦 Orden Shopify {transaction.shopify_order_id} debería estar marcada como PAGADA")
                return True
            else:
                print(f"❌ Error en webhook: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error enviando webhook: {e}")
            return False
    else:
        print(f"ℹ️  No se necesita simular webhook (Estado: {izipay_state})")
        return False

if __name__ == "__main__":
    print("🚀 Verificando nueva transacción...")
    print(f"📅 {datetime.now()}")
    print("=" * 80)
    
    # Verificar la nueva transacción
    transaction, izipay_data = check_new_transaction()
    
    # Si el pago fue exitoso pero no se actualizó, simular webhook
    if transaction and izipay_data:
        webhook_sent = simulate_webhook_if_needed(transaction, izipay_data)
        
        if webhook_sent:
            print(f"\n🎉 ¡Proceso completado!")
            print(f"   ✅ Pago procesado exitosamente")
            print(f"   ✅ Estado actualizado en base de datos")
            print(f"   ✅ Orden Shopify {transaction.shopify_order_id} marcada como pagada")
    
    print("\n✅ Verificación completada!")
