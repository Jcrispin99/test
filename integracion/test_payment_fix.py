#!/usr/bin/env python3
import requests
import json

def test_payment_link():
    """
    Prueba simple para verificar el formato del amount
    """
    url = "http://localhost:8000/izipay/payment-link/"
    
    # Datos de prueba
    test_data = {
        "amount": 150.50,  # Número decimal
        "orderNumber": "TEST-ORDER-123",
        "customerEmail": "test@example.com",
        "customerName": "Juan Pérez",
        "shopifyOrderId": "SHOPIFY-TEST-456",
        "productDescription": "Producto de prueba",
        "billing": {
            "firstName": "Juan",
            "lastName": "Pérez",
            "email": "test@example.com",
            "phoneNumber": "987654321",
            "address": "Av. Test 123",
            "city": "Lima",
            "state": "Lima",
            "zipCode": "15074"
        },
        "shipping": {
            "firstName": "Juan",
            "lastName": "Pérez",
            "email": "test@example.com",
            "phoneNumber": "987654321",
            "address": "Av. Test 123",
            "city": "Lima",
            "state": "Lima",
            "zipCode": "15074"
        }
    }
    
    print("🔍 Probando Payment Link con amount:", test_data["amount"])
    print("📤 Enviando datos a:", url)
    
    try:
        response = requests.post(
            url,
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "X-CSRFToken": "test-token"  # En producción obtendrías esto del DOM
            },
            timeout=30
        )
        
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Payment Link creado exitosamente!")
                print(f"🔗 Payment Link: {data.get('paymentLink', 'N/A')}")
                print(f"🆔 Transaction ID: {data.get('transactionId', 'N/A')}")
            else:
                print(f"❌ Error en la respuesta: {data.get('error', 'Error desconocido')}")
        else:
            print(f"❌ Error HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Detalles del error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Respuesta: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_payment_link()
