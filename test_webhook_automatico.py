#!/usr/bin/env python
"""
Script para probar el webhook automático de Izipay
Simula diferentes estados de pago para verificar que:
1. Se actualice la etiqueta correcta
2. Se agregue el comentario automático 
3. Se marque como pagada si corresponde
"""

import requests
import json

def probar_webhook_automatico():
    webhook_url = "http://localhost:8000/izipay/webhook/"
    
    # Usar la transacción que ya existe para la orden 6576332275934
    transaction_id = "100896"
    
    print("🧪 === PROBANDO WEBHOOK AUTOMÁTICO ===")
    print(f"🔗 URL: {webhook_url}")
    print(f"🆔 Transaction ID: {transaction_id}")
    
    # Probar diferentes estados
    estados_a_probar = [
        {
            "estado": "1",
            "descripcion": "GENERADO (pendiente)",
            "esperado": "pendiente"
        },
        {
            "estado": "2", 
            "descripcion": "EN_PROCESO (pendiente)",
            "esperado": "pendiente"
        },
        {
            "estado": "3",
            "descripcion": "TERMINADO_EXITO (pagada)",
            "esperado": "pagada"
        },
        {
            "estado": "4",
            "descripcion": "TERMINADO_ERROR (cancelada)", 
            "esperado": "cancelada"
        },
        {
            "estado": "5",
            "descripcion": "EXPIRADO (cancelada)",
            "esperado": "cancelada"
        }
    ]
    
    for test_case in estados_a_probar:
        print(f"\n📝 === PROBANDO: {test_case['descripcion']} ===")
        
        # Datos del webhook
        webhook_data = {
            "transactionId": transaction_id,
            "state": test_case["estado"],
            "paymentLinkId": "12345"
        }
        
        try:
            response = requests.post(webhook_url, json=webhook_data, timeout=30)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Respuesta exitosa:")
                print(f"   Message: {result.get('message')}")
                print(f"   Etiqueta aplicada: {result.get('etiqueta_aplicada')}")
                print(f"   Shopify Order ID: {result.get('shopify_order_id')}")
                print(f"   Procesamiento automático: {result.get('procesamiento_automatico')}")
                
                # Verificar que la etiqueta sea la esperada
                if result.get('etiqueta_aplicada') == test_case['esperado']:
                    print(f"✅ Etiqueta correcta: {test_case['esperado']}")
                else:
                    print(f"❌ Etiqueta incorrecta. Esperado: {test_case['esperado']}, Recibido: {result.get('etiqueta_aplicada')}")
                    
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error en la petición: {e}")
        
        # Esperar un poco entre pruebas
        import time
        time.sleep(2)
    
    print(f"\n🎯 === RESUMEN ===")
    print(f"✅ El webhook debe procesar automáticamente:")
    print(f"   • Actualizar etiquetas dinámicas según estado Izipay")  
    print(f"   • Agregar comentarios automáticos con info del pago")
    print(f"   • Marcar como pagada cuando estado = 3 (TERMINADO_EXITO)")
    print(f"   • Todo sin intervención manual")

if __name__ == "__main__":
    probar_webhook_automatico()
