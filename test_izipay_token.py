import requests
import json
import os
import sys
import django

# Configurar Django
sys.path.append('/Users/wild/Documents/workspace/ikoodev/test/integracion')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
django.setup()

# Importar el modelo después de configurar Django
from izipay.models import IzipayCredential

# Importar el nuevo modelo
from izipay.models import IzipayCredential, IzipayTransactionCounter

def test_izipay_token():
    """
    Prueba para generar token de sesión de Izipay usando datos del modelo
    """
    
    try:
        # Obtener credenciales desde el modelo
        credential = IzipayCredential.objects.first()
        if not credential:
            print("❌ No se encontraron credenciales de Izipay en la base de datos")
            print("💡 Asegúrate de crear una instancia de IzipayCredential en el admin de Django")
            return
            
        print(f"📋 Usando credenciales: {credential.nombre}")
        print(f"🏪 Merchant Code: {credential.merchant_code}")
        
    except Exception as e:
        print(f"❌ Error al obtener credenciales: {str(e)}")
        return
    
    # URL de la API de Izipay (sandbox)
    url = "https://sandbox-api-pw.izipay.pe/gateway/api/v1/proxy-cors/https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate"
    
    # Datos usando el modelo
    payload = {
        "requestSource": "ECOMMERCE",
        "merchantCode": credential.merchant_code,
        "orderNumber": "R202211101518",  # Este debería ser dinámico en producción
        "publicKey": credential.public_key,
        "amount": "15.00"  # Este debería venir del carrito
    }
    
    headers = {
        "transactionId": IzipayTransactionCounter.get_next_transaction_id(),  # Auto-incrementa
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("\n🚀 Probando generación de token de Izipay...")
        print(f"📡 URL: `{url}`")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        print(f"📋 Headers: {json.dumps(headers, indent=2)}")
        print("\n" + "="*50)
        
        # Realizar la petición
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print("\n📝 Response Body:")
        
        # Intentar parsear como JSON
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
            
            # Verificar si es la respuesta esperada
            if response_json.get('code') == '00' and response_json.get('message') == 'OK':
                print("\n✅ ¡Token generado exitosamente!")
                token = response_json.get('response', {}).get('token')
                if token:
                    print(f"🔑 Token: {token[:50]}...")
                    
                    # Información adicional
                    user_org = response_json.get('response', {}).get('userOrg')
                    user_scoring = response_json.get('response', {}).get('userScoring')
                    if user_org:
                        print(f"🏢 User Org: {user_org}")
                    if user_scoring:
                        print(f"📊 User Scoring: {user_scoring}")
            else:
                print("\n❌ Error en la respuesta de Izipay")
                print(f"Código: {response_json.get('code')}")
                print(f"Mensaje: {response_json.get('message')}")
                
        except json.JSONDecodeError:
            print("❌ La respuesta no es JSON válido:")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout: La petición tardó demasiado")
    except requests.exceptions.ConnectionError:
        print("🌐 Error de conexión: No se pudo conectar con Izipay")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la petición: {str(e)}")
    except Exception as e:
        print(f"💥 Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_izipay_token()