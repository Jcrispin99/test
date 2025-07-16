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

def check_specific_transaction(transaction_id):
    """Verificar una transacción específica en detalle"""
    try:
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
        print(f"🔍 Verificando transacción: {transaction_id}")
        print(f"   Payment Link ID: {transaction.payment_link_id}")
        print(f"   Estado actual en BD: {transaction.payment_link_state}")
        print(f"   Shopify Order ID: {transaction.shopify_order_id}")
        
        # Consultar estado en Izipay
        current_state = check_izipay_status_detailed(transaction.payment_link_id)
        return current_state
        
    except PaymentTransaction.DoesNotExist:
        print(f"❌ Transacción {transaction_id} no encontrada")
        return None

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
        
        print(f"   Token response: {token_data}")
        
        if token_response.status_code != 200 or token_data.get('code') != '00':
            print(f"❌ Error generando token: {token_data.get('message', 'Error desconocido')}")
            return None
        
        session_token = token_data.get('response', {}).get('token')
        print(f"✅ Token generado: {session_token[:20]}...")
        
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
        
        print(f"🔍 Consultando Payment Link: {payment_link_id}")
        search_response = requests.post(search_url, json=search_payload, headers=search_headers, timeout=30)
        search_data = search_response.json()
        
        print(f"📊 Respuesta completa de Izipay:")
        print(json.dumps(search_data, indent=2, ensure_ascii=False))
        
        if search_response.status_code == 200 and search_data.get('code') == '00':
            payment_link_info = search_data.get('response', {})
            return payment_link_info
        else:
            print(f"❌ Error consultando Izipay: {search_data.get('message', 'Error desconocido')}")
            return None
            
    except Exception as e:
        print(f"❌ Error consultando estado: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Verificar la transacción más reciente que pagaste
    print("🚀 Verificando estado detallado de la transacción más reciente...")
    print("=" * 80)
    
    # Cambia este ID por el de la transacción que acabas de pagar
    transaction_id = "100704"  # La más reciente según los logs
    
    result = check_specific_transaction(transaction_id)
    
    if result:
        print("\n✅ Consulta exitosa!")
        print(f"Estado actual en Izipay: {result.get('state')}")
        print(f"Información completa disponible arriba ⬆️")
    else:
        print("\n❌ No se pudo consultar el estado")
