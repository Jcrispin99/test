#!/usr/bin/env python3
"""
Script de prueba para las APIs de Izipay Payment Link
"""

import requests
import json

BASE_URL = "http://localhost:8000"  # Cambiar por tu URL

def test_create_payment_link():
    """Probar la creación de un Payment Link"""
    url = f"{BASE_URL}/izipay/payment-link/"
    
    payload = {
        "amount": 100.50,
        "orderNumber": "TEST-ORDER-001",
        "customerEmail": "test@example.com",
        "customerName": "Juan Pérez",
        "shopifyOrderId": "SHOPIFY-12345",
        "productDescription": "Producto de prueba",
        "billing": {
            "firstName": "Juan",
            "lastName": "Pérez",
            "phoneNumber": "987654321",
            "address": "Av. Test 123",
            "city": "Lima",
            "state": "Lima",
            "zipCode": "15001"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": "test-token"  # En producción usar el token real
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("=== Crear Payment Link ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_search_payment_link(payment_link_id):
    """Probar la búsqueda de un Payment Link"""
    url = f"{BASE_URL}/izipay/search/"
    
    payload = {
        "paymentLinkId": payment_link_id
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": "test-token"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("=== Buscar Payment Link ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_list_transactions():
    """Probar el listado de transacciones"""
    url = f"{BASE_URL}/izipay/transactions/"
    
    try:
        response = requests.get(url)
        print("=== Listar Transacciones ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_webhook_notification():
    """Simular una notificación de webhook con orden real de Shopify"""
    url = f"{BASE_URL}/izipay/webhook/"
    
    payload = {
        "transactionId": "100123",
        "state": "3",  # TERMINADO_EXITO
        "paymentLinkId": "test-payment-link-id"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("=== Webhook Notification (GraphQL orderMarkAsPaid) ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_create_transaction_with_shopify_order():
    """Crear una transacción de prueba vinculada a orden real de Shopify"""
    url = f"{BASE_URL}/izipay/payment-link/"
    
    payload = {
        "amount": 15.00,  # Monto corregido (15 soles, no 1500)
        "orderNumber": "TEST-GRAPHQL-001", 
        "customerEmail": "test@example.com",
        "customerName": "Test GraphQL",
        "shopifyOrderId": "5973851226407",  # Orden real de Shopify
        "productDescription": "Prueba GraphQL orderMarkAsPaid"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("=== Crear Transacción con Orden Shopify ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Iniciando pruebas del nuevo método GraphQL orderMarkAsPaid...")
    print()
    
    # 1. Crear transacción vinculada a orden real de Shopify
    print("📝 Paso 1: Creando transacción con orden real de Shopify")
    transaction_result = test_create_transaction_with_shopify_order()
    
    # 2. Listar transacciones para verificar
    print("📋 Paso 2: Verificando transacciones en base de datos")
    test_list_transactions()
    
    # 3. Simular webhook que activará GraphQL orderMarkAsPaid
    print("🔄 Paso 3: Simulando webhook de pago exitoso (activará GraphQL)")
    webhook_result = test_webhook_notification()
    
    # 4. Buscar Payment Link (si se creó uno)
    if transaction_result and transaction_result.get('paymentLinkId'):
        print("🔍 Paso 4: Buscando detalles del Payment Link")
        test_search_payment_link(transaction_result['paymentLinkId'])
    
    print()
    print("✅ Pruebas completadas - Revisa los logs del servidor Django para ver la ejecución de GraphQL")
    print("🔍 La mutación orderMarkAsPaid debería haber marcado la orden de Shopify como pagada")
    print("📋 Verifica en Shopify Admin si la orden 5973851226407 cambió su estado financiero")
