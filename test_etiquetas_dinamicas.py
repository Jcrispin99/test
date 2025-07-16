#!/usr/bin/env python3
"""
Prueba del nuevo sistema de etiquetas dinámicas basadas en estados de Izipay
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_estados_dinamicos():
    """Probar diferentes estados de Izipay y sus etiquetas correspondientes"""
    
    print("🧪 === PRUEBA DE ETIQUETAS DINÁMICAS ===")
    print()
    
    # Estados de prueba según Izipay
    estados_prueba = [
        ("1", "GENERADO", "pendiente"),
        ("2", "EN_PROCESO", "pendiente"), 
        ("3", "TERMINADO_EXITO", "pagada"),
        ("4", "TERMINADO_ERROR", "cancelada"),
        ("5", "EXPIRADO", "cancelada")
    ]
    
    transaction_id = "100123"  # Usar transacción existente
    
    for estado_codigo, estado_nombre, etiqueta_esperada in estados_prueba:
        print(f"🔄 Probando estado: {estado_codigo} ({estado_nombre})")
        print(f"🏷️  Etiqueta esperada: '{etiqueta_esperada}'")
        
        # Simular webhook
        payload = {
            "transactionId": transaction_id,
            "state": estado_codigo,
            "paymentLinkId": "PL123456"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/izipay/webhook/",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                etiqueta_aplicada = result.get('etiqueta_aplicada', 'N/A')
                
                print(f"✅ Webhook exitoso")
                print(f"📋 Etiqueta aplicada: '{etiqueta_aplicada}'")
                
                if etiqueta_aplicada == etiqueta_esperada:
                    print(f"✅ ¡Correcto! Etiqueta coincide")
                else:
                    print(f"❌ Error: esperaba '{etiqueta_esperada}', obtuvo '{etiqueta_aplicada}'")
            else:
                print(f"❌ Error en webhook: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
        
        print()
    
    print("📊 === RESUMEN DEL SISTEMA DE ETIQUETAS ===")
    print("🔹 Estado 1 (GENERADO) → etiqueta: 'pendiente'")
    print("🔹 Estado 2 (EN_PROCESO) → etiqueta: 'pendiente'") 
    print("🔹 Estado 3 (TERMINADO_EXITO) → etiqueta: 'pagada' + GraphQL")
    print("🔹 Estado 4 (TERMINADO_ERROR) → etiqueta: 'cancelada'")
    print("🔹 Estado 5 (EXPIRADO) → etiqueta: 'cancelada'")
    print()
    print("💡 Las etiquetas se actualizan automáticamente y reemplazan las anteriores")
    print("🎯 Solo una etiqueta de estado por orden en cualquier momento")

def verificar_transacciones():
    """Verificar las transacciones en la base de datos"""
    try:
        response = requests.get(f"{BASE_URL}/izipay/transactions/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            transactions = data.get('transactions', [])
            
            print(f"📋 Total de transacciones: {len(transactions)}")
            
            for trans in transactions[:3]:  # Mostrar solo las primeras 3
                print(f"   • ID: {trans['transaction_id']}")
                print(f"     Estado: {trans['payment_link_state']} ({trans['payment_link_state_display']})")
                print(f"     Shopify: {trans['shopify_order_id']}")
                print()
        else:
            print(f"❌ Error obteniendo transacciones: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Verificar transacciones disponibles
    print("🔍 Verificando transacciones existentes...")
    verificar_transacciones()
    
    print()
    
    # Probar sistema de etiquetas dinámicas
    test_estados_dinamicos()
    
    print()
    print("✅ Prueba completada")
    print("🔗 Ve a Shopify Admin para ver los cambios de etiquetas en tiempo real")
