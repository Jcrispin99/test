from izipay.models import PaymentTransaction

print(f"Total de transacciones: {PaymentTransaction.objects.count()}")

print("\nÚltimas 3 transacciones:")
for transaction in PaymentTransaction.objects.all().order_by('-created_at')[:3]:
    print(f"- ID: {transaction.transaction_id}")
    print(f"  Amount: {transaction.amount} {transaction.currency}")
    print(f"  Estado: {transaction.get_payment_link_state_display()}")
    print(f"  Email: {transaction.customer_email}")
    print(f"  Shopify Order: {transaction.shopify_order_id}")
    print(f"  Creado: {transaction.created_at}")
    print("---")
