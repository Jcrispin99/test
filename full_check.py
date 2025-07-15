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

def check_all_transactions_detailed():
    """Verificar todas las transacciones en detalle"""
    transactions = PaymentTransaction.objects.all().order_by('-created_at')
    
    print("🔍 Verificando TODAS las transacciones en Izipay...")
    print("=" * 80)
    
    credential = IzipayCredential.objects.filter(is_active=True).first()
    if not credential:
        print("❌ No hay credenciales activas")
        return
    
    for transaction in transactions:
        if not transaction.payment_link_id:
            print(f"⏭️  Saltando {transaction.transaction_id} (sin payment_link_id)")
            continue
            
        print(f"\n📋 Transacción: {transaction.transaction_id}")
        print(f"   🛒 Shopify Order: {transaction.shopify_order_id}")
        print(f"   📊 Estado local: {transaction.payment_link_state}")
        
        # Consultar estado en Izipay
        izipay_state = get_izipay_state(transaction.payment_link_id, credential)
        
        if izipay_state:
            print(f"   🌐 Estado Izipay: {izipay_state}")
            
            if izipay_state != transaction.payment_link_state:
                print(f"   🔄 ACTUALIZANDO: {transaction.payment_link_state} → {izipay_state}")
                
                # Actualizar en la base de datos
                old_state = transaction.payment_link_state
                transaction.payment_link_state = izipay_state
                transaction.webhook_received_at = datetime.now()
                transaction.save()
                
                print(f"   ✅ ACTUALIZADO en BD!")
                
                # Si es exitoso, mostrar info de Shopify
                if izipay_state == '3':
                    print(f"   💰 PAGO EXITOSO! Orden Shopify: {transaction.shopify_order_id}")
                    print(f"   📦 Esta orden debería marcarse como PAGADA")
            else:
                print(f"   ✅ Estados sincronizados")
        else:
            print(f"   ❌ No se pudo consultar Izipay")

def get_izipay_state(payment_link_id, credential):
    """Obtener estado de un payment link en Izipay"""
    try:
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
            return None
            
    except Exception as e:
        return None

if __name__ == "__main__":
    print("🚀 Verificación completa de estados de pago")
    print(f"📅 {datetime.now()}")
    
    check_all_transactions_detailed()
    
    print("\n✅ Verificación completada!")
    print("💡 Si alguna transacción cambió a estado '3', ¡el pago fue exitoso!")
