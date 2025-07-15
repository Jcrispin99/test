import requests
import json
import time
from datetime import datetime

def test_izipay_complete_flow():
    """
    Prueba completa del flujo de Izipay:
    1. Generar token desde Django
    2. Simular configuración del SDK
    3. Mostrar datos que se enviarían al SDK
    """
    
    print("🚀 === PRUEBA COMPLETA DE IZIPAY ===")
    print()
    
    # Paso 1: Generar token
    print("📋 Paso 1: Generando token desde Django...")
    
    token_url = "http://localhost:8000/izipay/generate-token/"
    order_number = f"TEST-FLOW-{int(time.time())}"
    
    token_payload = {
        "amount": "150.00",
        "orderNumber": order_number
    }
    
    try:
        response = requests.post(token_url, json=token_payload, headers={
            "Content-Type": "application/json"
        })
        
        if response.status_code == 200:
            token_data = response.json()
            if token_data.get('success'):
                print("✅ Token generado exitosamente")
                print(f"   Token: {token_data['token'][:50]}...")
                print(f"   Transaction ID: {token_data['transactionId']}")
                print(f"   Order Number: {token_data['orderNumber']}")
                print()
                
                # Paso 2: Configurar datos para el SDK
                print("⚙️  Paso 2: Configurando datos para el SDK...")
                
                # Datos del modelo (simulados)
                merchant_config = {
                    "merchantCode": "4004396",
                    "publicKey": "VErethUtraQuxas57wuMuquprADrAHAb"
                }
                
                # Configuración completa para Izipay SDK
                izipay_config = {
                    "config": {
                        "transactionId": token_data['transactionId'],
                        "action": "pay",
                        "merchantCode": merchant_config["merchantCode"],
                        "order": {
                            "orderNumber": token_data['orderNumber'],
                            "currency": "PEN",
                            "amount": token_data['amount'],
                            "processType": "AT",
                            "merchantBuyerId": merchant_config["merchantCode"],
                            "dateTimeTransaction": str(int(time.time() * 1000)) + "000",
                        },
                        "billing": {
                            "firstName": "Juan",
                            "lastName": "Pérez",
                            "email": "test@example.com",
                            "phoneNumber": "987654321",
                            "street": "Av. Test 123",
                            "city": "Lima",
                            "state": "Lima",
                            "country": "PE",
                            "postalCode": "15001",
                            "documentType": "DNI",
                            "document": "12345678",
                        }
                    }
                }
                
                # Datos para LoadForm
                load_form_config = {
                    "authorization": token_data['token'],
                    "keyRSA": merchant_config["publicKey"],
                    "callbackResponse": "callbackResponsePayment"  # Función callback
                }
                
                print("✅ Configuración del SDK preparada")
                print()
                
                # Paso 3: Mostrar configuración completa
                print("📄 Paso 3: Configuración completa para el SDK:")
                print()
                print("🔧 Configuración de inicialización:")
                print(json.dumps(izipay_config, indent=2, ensure_ascii=False))
                print()
                print("🔑 Configuración de LoadForm:")
                print(json.dumps(load_form_config, indent=2, ensure_ascii=False))
                print()
                
                # Paso 4: Generar código JavaScript equivalente
                print("💻 Paso 4: Código JavaScript equivalente:")
                print()
                print("```javascript")
                print("// 1. Configuración del SDK")
                print(f"const iziConfig = {json.dumps(izipay_config, indent=2)};")
                print()
                print("// 2. Inicializar SDK")
                print("try {")
                print("  const checkout = new Izipay({ config: iziConfig });")
                print("  console.log('✅ SDK inicializado');")
                print("} catch ({Errors, message, date}) {")
                print("  console.log({Errors, message, date});")
                print("}")
                print()
                print("// 3. Mostrar formulario")
                print("const callbackResponsePayment = (response) => console.log(response);")
                print()
                print("try {")
                print("  checkout && checkout.LoadForm({")
                print(f"    authorization: '{token_data['token'][:50]}...',")
                print(f"    keyRSA: '{merchant_config['publicKey']}',")
                print("    callbackResponse: callbackResponsePayment,")
                print("  });")
                print("} catch ({Errors, message, date}) {")
                print("  console.log({Errors, message, date});")
                print("}")
                print("```")
                print()
                
                print("🎉 ¡Flujo completo simulado exitosamente!")
                print()
                print("📝 Próximos pasos:")
                print("   1. Copiar el código JavaScript generado")
                print("   2. Pegarlo en la consola del navegador con el SDK cargado")
                print("   3. O integrarlo en tu archivo HTML/JS")
                
            else:
                print("❌ Error en la respuesta del token:")
                print(json.dumps(token_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error HTTP {response.status_code}:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar con el servidor Django")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    except Exception as e:
        print(f"💥 Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_izipay_complete_flow()