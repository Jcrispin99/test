from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from shopify.models import ShopifyCredential
import json
import requests

# Nueva vista para servir el template
def checkout_page(request):
    """Renderiza la página de checkout"""
    return render(request, 'checkout/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def process_checkout(request):
    try:
        data = json.loads(request.body)
        
        # Obtener credenciales de Shopify
        shopify_creds = ShopifyCredential.objects.first()
        if not shopify_creds:
            return JsonResponse({'error': 'No hay credenciales de Shopify'}, status=400)
        
        # 1. Enviar a Shopify
        shopify_result = send_to_shopify(data, shopify_creds)
        
        # 2. Enviar a otro servicio
        other_result = send_to_other_service(data)
        
        return JsonResponse({
            'success': True,
            'shopify_response': shopify_result,
            'other_service_response': other_result,
            'message': 'Pedido procesado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def send_to_shopify(data, credentials):
    """Envía orden a Shopify"""
    headers = {
        'X-Shopify-Access-Token': credentials.access_token,
        'Content-Type': 'application/json'
    }
    
    url = f"https://{credentials.store_name}.myshopify.com/admin/api/2023-10/orders.json"
    
    # ✅ Mejorar el mapeo de line_items para Shopify
    line_items = []
    for item in data.get('items', []):
        line_items.append({
            'title': item.get('name', ''),
            'price': str(item.get('price', 0) / 100),  # Convertir centavos a soles
            'quantity': item.get('quantity', 1),
            'sku': item.get('sku', ''),
        })
    
    order_data = {
        'order': {
            'email': data.get('email'),
            'shipping_address': {
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'address1': data.get('address1'),
                'address2': data.get('address2', ''),
                'city': data.get('city'),
                'province': data.get('province'),
                'zip': data.get('zip'),
                'country': 'PE'  # ✅ Agregar país
            },
            'line_items': line_items,
            'financial_status': 'pending',
            'currency': 'PEN'  # ✅ Especificar moneda
        }
    }
    
    try:
        response = requests.post(url, json=order_data, headers=headers)
        response.raise_for_status()  # ✅ Lanzar excepción si hay error HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': f'Error de Shopify: {str(e)}'}

def send_to_other_service(data):
    """Envía a otro servicio (ej: Izipay)"""
    try:
        return {
            'status': 'success',
            'transaction_id': 'TXN123456',
            'message': 'Procesado en otro servicio'
        }
    except Exception as e:
        return {'error': str(e)}
