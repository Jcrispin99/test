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
    """Simular una notificación de webhook"""
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
        print("=== Webhook Notification ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Iniciando pruebas de las APIs de Izipay...")
    print()
    
    # 1. Crear Payment Link
    payment_result = test_create_payment_link()
    
    # 2. Listar transacciones
    test_list_transactions()
    
    # 3. Simular webhook
    test_webhook_notification()
    
    # 4. Buscar Payment Link (si se creó uno)
    if payment_result and payment_result.get('paymentLinkId'):
        test_search_payment_link(payment_result['paymentLinkId'])
    
    print("✅ Pruebas completadas")
