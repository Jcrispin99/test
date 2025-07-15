#!/usr/bin/env python3
import requests
import json

def check_payment_status():
    """
    Verificar manualmente el estado de un Payment Link específico
    """
    
    # Obtener información de la transacción desde la base de datos
    import os
    import django
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
    django.setup()
    
    from izipay.models import PaymentTransaction
    
    try:
        # Buscar la transacción más reciente
        transaction = PaymentTransaction.objects.latest('created_at')
        print(f"🔍 Transacción encontrada: {transaction.transaction_id}")
        print(f"📧 Email: {transaction.customer_email}")
        print(f"💰 Monto: {transaction.amount} {transaction.currency}")
        print(f"🆔 Payment Link ID: {transaction.payment_link_id}")
        print(f"🔗 Payment Link URL: {transaction.payment_link_url}")
        print(f"📊 Estado actual: {transaction.get_payment_link_state_display()}")
        print(f"🛒 Shopify Order ID: {transaction.shopify_order_id}")
        print()
        
        if transaction.payment_link_id:
            # Probar la API de búsqueda
            search_url = "http://localhost:8000/izipay/search/"
            search_data = {
                "paymentLinkId": transaction.payment_link_id
            }
            
            print(f"🔍 Consultando estado del Payment Link...")
            print(f"📤 URL: {search_url}")
            print(f"📄 Payload: {json.dumps(search_data, indent=2)}")
            
            try:
                response = requests.post(
                    search_url,
                    json=search_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                print(f"📥 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        transaction_data = result.get('transaction', {})
                        izipay_data = result.get('izipay_data', {})
                        
                        print("✅ Consulta exitosa!")
                        print(f"📊 Estado: {transaction_data.get('payment_link_state_display')}")
                        print(f"💰 ¿Pagado?: {'SÍ' if transaction_data.get('is_successful') else 'NO'}")
                        print(f"❌ ¿Fallido?: {'SÍ' if transaction_data.get('is_failed') else 'NO'}")
                        
                        if izipay_data.get('state'):
                            print(f"🔢 Estado Izipay: {izipay_data.get('state')}")
                        
                        # Si el pago fue exitoso y hay Shopify Order ID
                        if transaction_data.get('is_successful') and transaction.shopify_order_id:
                            print(f"🚀 ¡El pago fue exitoso! Debería actualizar Shopify Order: {transaction.shopify_order_id}")
                        
                    else:
                        print(f"❌ Error en la consulta: {result.get('error')}")
                else:
                    try:
                        error_data = response.json()
                        print(f"❌ Error HTTP {response.status_code}: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"❌ Error HTTP {response.status_code}: {response.text}")
                        
            except requests.exceptions.RequestException as e:
                print(f"❌ Error de conexión: {e}")
        else:
            print("⚠️ No hay Payment Link ID para consultar")
            
    except PaymentTransaction.DoesNotExist:
        print("❌ No se encontraron transacciones en la base de datos")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_payment_status()
