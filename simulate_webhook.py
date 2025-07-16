#!/usr/bin/env python
import requests
import json

def simulate_webhook_success(transaction_id, payment_link_id):
    """Simular webhook de pago exitoso"""
    
    webhook_url = "http://127.0.0.1:8000/izipay/webhook/"
    
    # Datos que enviaría Izipay cuando el pago es exitoso
    webhook_data = {
        "transactionId": transaction_id,
        "paymentLinkId": payment_link_id,
        "state": "3",  # TERMINADO_EXITO
        "paymentLinkState": "3",
        "amount": "15.00",
        "currency": "PEN",
        "merchantCode": "4004345",
        "timestamp": "2025-07-15T12:25:00.000Z"
    }
    
    print(f"🔔 Simulando webhook para transacción: {transaction_id}")
    print(f"📡 URL: {webhook_url}")
    print(f"📦 Datos: {json.dumps(webhook_data, indent=2)}")
    
    try:
        response = requests.post(
            webhook_url, 
            json=webhook_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n📊 Respuesta del webhook:")
        print(f"   Status: {response.status_code}")
        print(f"   Respuesta: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook simulado exitosamente!")
            return True
        else:
            print("❌ Error en el webhook")
            return False
            
    except Exception as e:
        print(f"❌ Error enviando webhook: {e}")
        return False

def check_server_running():
    """Verificar si el servidor Django está corriendo"""
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        return True
    except:
        return False

if __name__ == "__main__":
    print("🚀 Simulador de Webhook de Izipay")
    print("=" * 50)
    
    # Verificar que el servidor esté corriendo
    if not check_server_running():
        print("❌ El servidor Django no está corriendo en http://127.0.0.1:8000/")
        print("💡 Ejecuta: cd integracion && python manage.py runserver")
        exit(1)
    
    print("✅ Servidor Django detectado")
    
    # Datos de la transacción más reciente
    transaction_id = "100704"
    payment_link_id = "2ed4291f7cc143209b68274367907b33"
    
    # Simular webhook de pago exitoso
    success = simulate_webhook_success(transaction_id, payment_link_id)
    
    if success:
        print("\n🎉 ¡Webhook simulado! Ahora verifica el estado del pedido en Shopify.")
    else:
        print("\n❌ Falló la simulación del webhook.")
