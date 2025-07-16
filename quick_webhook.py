import requests
import json

# Simular webhook de pago exitoso para la nueva orden
webhook_data = {
    'transactionId': '100896',
    'paymentLinkId': 'c55e5e150b114da3b414341d7f9a0910',
    'state': '3',
    'paymentLinkState': '3',
    'amount': '15.00',
    'currency': 'PEN',
    'merchantCode': '4004345'
}

print('🔔 Simulando webhook para orden 6576332275934...')
try:
    response = requests.post(
        'http://127.0.0.1:8000/izipay/webhook/',
        json=webhook_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    print(f'📊 Status: {response.status_code}')
    print(f'📦 Respuesta: {response.text}')
    
    if response.status_code == 200:
        print('✅ ¡Webhook enviado exitosamente!')
        print('💰 Orden 6576332275934 debería estar marcada como PAGADA')
    else:
        print('❌ Error en el webhook')
        
except Exception as e:
    print(f'❌ Error: {e}')
