#!/usr/bin/env python3
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
django.setup()

from izipay.models import PaymentTransaction

try:
    # Buscar la transacción del pago real
    transaction = PaymentTransaction.objects.get(transaction_id='100216')
    print(f"🔍 Transacción real encontrada: {transaction.transaction_id}")
    print(f"📧 Email: {transaction.customer_email}")
    print(f"💰 Monto: {transaction.amount} {transaction.currency}")
    print(f"🆔 Payment Link ID: {transaction.payment_link_id}")
    print(f"📊 Estado actual: {transaction.get_payment_link_state_display()}")
    print(f"🛒 Shopify Order ID: {transaction.shopify_order_id}")
    print()
    
    # Actualizar manualmente el Shopify Order ID
    print("🔧 Actualizando Shopify Order ID manualmente...")
    transaction.shopify_order_id = "6576265265374"  # Del log anterior
    transaction.save()
    print(f"✅ Shopify Order ID actualizado: {transaction.shopify_order_id}")
    
except PaymentTransaction.DoesNotExist:
    print("❌ Transacción no encontrada")
except Exception as e:
    print(f"❌ Error: {e}")
