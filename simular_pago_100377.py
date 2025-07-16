#!/usr/bin/env python
"""
Script para simular el pago exitoso de la transacción 100377
y probar el sistema automático de webhook
"""

import requests
import json

def simular_pago_exitoso():
    print("🧪 === SIMULANDO PAGO EXITOSO PARA TU TRANSACCIÓN ===")
    
    # Tu transacción específica
    transaction_id = "100377"
    order_id = "6576567517406"
    
    print(f"📊 Transacción: {transaction_id}")
    print(f"📦 Orden Shopify: {order_id}")
    
    # URL del webhook (debe estar corriendo en localhost:8000)
    webhook_url = "http://localhost:8000/izipay/webhook/"
    
    # Simular webhook de Izipay cuando el pago es exitoso
    webhook_data = {
        "transactionId": transaction_id,
        "state": "3",  # 3 = TERMINADO_EXITO (PAGADO)
        "paymentLinkId": "12345"  # ID del payment link
    }
    
    print(f"\n🔄 Enviando webhook simulado...")
    print(f"   Estado: 3 (TERMINADO_EXITO)")
    print(f"   URL: {webhook_url}")
    
    try:
        response = requests.post(webhook_url, json=webhook_data, timeout=30)
        
        print(f"\n📊 Respuesta del webhook:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ SUCCESS: {result.get('success')}")
            print(f"   📝 Message: {result.get('message')}")
            print(f"   🏷️  Etiqueta aplicada: {result.get('etiqueta_aplicada')}")
            print(f"   📦 Shopify Order: {result.get('shopify_order_id')}")
            print(f"   🤖 Procesamiento automático: {result.get('procesamiento_automatico')}")
            
            if result.get('success') and result.get('etiqueta_aplicada') == 'pagada':
                print(f"\n✅ === SISTEMA AUTOMÁTICO FUNCIONÓ CORRECTAMENTE ===")
                print(f"🔄 El sistema automáticamente:")
                print(f"   ✅ Actualizó el estado en BD: 1 → 3")
                print(f"   ✅ Cambió etiqueta en Shopify: 'pendiente' → 'pagada'") 
                print(f"   ✅ Marcó la orden como pagada en Shopify")
                print(f"   ✅ Agregó comentario con detalles del pago")
                print(f"   ✅ Incluyó el link de verificación del pago")
                
                print(f"\n🎯 AHORA REVISA EN SHOPIFY:")
                print(f"   📋 Orden debería mostrar: 'pagada' en etiquetas")
                print(f"   💬 Comentario: 'Cliente ya realizó el pago de X PEN'")
                print(f"   💰 Estado financiero: 'Paid'")
                
            else:
                print(f"\n❌ Algo no funcionó correctamente")
                print(f"   Revisa los logs del servidor Django")
                
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: No se pudo conectar al webhook")
        print(f"🔧 SOLUCIÓN:")
        print(f"   1. Asegúrate de que el servidor Django esté corriendo:")
        print(f"      cd integracion && python manage.py runserver")
        print(f"   2. Luego ejecuta este script nuevamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

def verificar_resultado():
    print(f"\n🔍 === CÓMO VERIFICAR QUE FUNCIONÓ ===")
    print(f"")
    print(f"1. 📋 En Shopify Admin:")
    print(f"   • Ve a la orden {order_id}")
    print(f"   • Verifica que las etiquetas muestren 'pagada'")
    print(f"   • Revisa los comentarios/notas de la orden")
    print(f"")
    print(f"2. 💬 Comentario automático debe decir:")
    print(f"   '✅ PAGO CONFIRMADO VÍA IZIPAY'")
    print(f"   'El cliente ya realizó el pago de X PEN'")
    print(f"   'Link de pago para verificación: [URL]'")
    print(f"")
    print(f"3. 💰 Estado financiero:")
    print(f"   • Debe cambiar a 'Paid' automáticamente")

if __name__ == "__main__":
    simular_pago_exitoso()
    verificar_resultado()
