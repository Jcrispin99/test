#!/usr/bin/env python3
"""
Script para probar directamente la mutación GraphQL orderMarkAsPaid
"""

import requests
import json

def test_graphql_order_mark_as_paid():
    """Probar la mutación GraphQL"""
    url = "http://localhost:8000/izipay/test-graphql/"
    
    payload = {
        "order_id": "5973851226407"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🧪 Probando GraphQL orderMarkAsPaid...")
        print(f"🔗 URL: {url}")
        print(f"📦 Payload: {payload}")
        print()
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        return response.json()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = test_graphql_order_mark_as_paid()
    
    if result and result.get('success'):
        print()
        print("✅ ¡GraphQL orderMarkAsPaid ejecutado exitosamente!")
        print(f"📋 Orden: {result.get('order_name')}")
        print(f"💰 Estado financiero: {result.get('financial_status')}")
        print()
        print("🔍 Ve a Shopify Admin y verifica que la orden esté marcada como pagada")
    else:
        print()
        print("❌ Hubo un problema con la mutación GraphQL")
        print("🔍 Revisa los logs para más detalles")
