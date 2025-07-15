#!/usr/bin/env python3
import requests
import json

def simulate_webhook():
    """
    Simular el webhook de Izipay cuando el pago es exitoso
    """
    webhook_url = "http://localhost:8000/izipay/webhook/"
    
    # Datos del webhook cuando el pago es exitoso
    webhook_data = {
        "transactionId": "100216",
        "state": "3",  # TERMINADO_EXITO
        "paymentLinkId": "a74a816f880648e8b8f1cf1556a9eb3c"
    }
    
    print("🔔 Simulando webhook de Izipay...")
    print(f"📤 URL: {webhook_url}")
    print(f"📄 Payload: {json.dumps(webhook_data, indent=2)}")
    
    try:
        response = requests.post(
            webhook_url,
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Webhook procesado exitosamente!")
                print(f"📝 Mensaje: {result.get('message')}")
                print(f"🆔 Transaction ID: {result.get('transaction_id')}")
            else:
                print(f"❌ Error en webhook: {result.get('error')}")
        else:
            try:
                error_data = response.json()
                print(f"❌ Error HTTP {response.status_code}: {json.dumps(error_data, indent=2)}")
            except:
                print(f"❌ Error HTTP {response.status_code}: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    simulate_webhook()
