#!/usr/bin/env python3
"""
Probar GraphQL orderMarkAsPaid con orden específica 6576332275934
"""

import requests
import json

def test_specific_order():
    """Probar con la orden específica de Shopify"""
    url = "http://localhost:8000/izipay/test-graphql/"
    
    payload = {
        "order_id": "6576332275934"  # Orden real de Shopify
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🎯 Probando GraphQL orderMarkAsPaid con orden específica...")
        print(f"🔗 URL: {url}")
        print(f"📦 Orden ID: {payload['order_id']}")
        print(f"🌐 Shopify Admin: https://admin.shopify.com/store/ahge8x-7b/orders/{payload['order_id']}")
        print()
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("📄 Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get('success'):
                print()
                print("✅ ¡ÉXITO! GraphQL orderMarkAsPaid ejecutado correctamente")
                print(f"📋 Orden: {result.get('order_name', 'N/A')}")
                print(f"💰 Estado financiero: {result.get('financial_status', 'N/A')}")
                print()
                print("🔍 Ve a Shopify Admin y verifica:")
                print(f"   https://admin.shopify.com/store/ahge8x-7b/orders/{payload['order_id']}")
                print("   La orden debería mostrar 'Paid' en el estado financiero")
                return True
            else:
                print()
                print("❌ La mutación falló:")
                print(f"   Error: {result.get('error', 'Desconocido')}")
                if 'user_errors' in result:
                    print(f"   User errors: {result['user_errors']}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_server_status():
    """Verificar que el servidor esté funcionando"""
    try:
        response = requests.get("http://localhost:8000/izipay/transactions/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor Django funcionando correctamente")
            return True
        else:
            print(f"❌ Servidor respondió con código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor Django: {e}")
        return False

if __name__ == "__main__":
    print("🚀 === PRUEBA ESPECÍFICA DE GRAPHQL ORDERMARKASPAID ===")
    print()
    
    # Verificar servidor
    if not check_server_status():
        print("🔧 Asegúrate de que el servidor Django esté ejecutándose:")
        print("   cd integracion && python manage.py runserver")
        exit(1)
    
    print()
    
    # Ejecutar prueba
    success = test_specific_order()
    
    print()
    if success:
        print("🎉 ¡Prueba completada exitosamente!")
        print("📱 Revisa Shopify Admin para confirmar el cambio de estado")
    else:
        print("🔍 Revisa los logs del servidor Django para más detalles")
        print("💡 El servidor debería mostrar información detallada sobre la ejecución de GraphQL")
