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
    
    # Debug: mostrar la estructura de datos recibida
    print(f"\n=== DEBUG SHOPIFY ORDER ===")
    print(f"Data received: {json.dumps(data, indent=2, ensure_ascii=False)}")
    print("===========================\n")
    
    def get_region_name_from_code(code):
        region_map = {
            '01': 'Amazonas', '02': 'Áncash', '03': 'Apurímac', '04': 'Arequipa',
            '05': 'Ayacucho', '06': 'Cajamarca', '07': 'Callao', '08': 'Cusco',
            '09': 'Huancavelica', '10': 'Huánuco', '11': 'Ica', '12': 'Junín',
            '13': 'La Libertad', '14': 'Lambayeque', '15': 'Lima', '16': 'Loreto',
            '17': 'Madre de Dios', '18': 'Moquegua', '19': 'Pasco', '20': 'Piura',
            '21': 'Puno', '22': 'San Martín', '23': 'Tacna', '24': 'Tumbes', '25': 'Ucayali'
        }
        
        if not code:
            return 'Lima'
        
        if any(c.isalpha() for c in str(code)):
            return str(code)
        
        normalized_code = str(code).zfill(2)
        return region_map.get(normalized_code, str(code))
    
    line_items = []
    for item in data.get('items', []):
        price_in_cents = item.get('line_price', 0)
        price_decimal = price_in_cents / 100
        
        line_items.append({
            'title': item.get('name', ''),
            'price': str(price_decimal),
            'quantity': item.get('quantity', 1),
            'sku': item.get('sku', ''),
        })
    
    shipping_addr = data.get('shipping_address', {})
    
    province_code = shipping_addr.get('province', '')
    province_name = get_region_name_from_code(province_code)
    
    print(f"\n=== PROVINCIA CONVERSION ===")
    print(f"Original: {province_code} -> Converted: {province_name}")
    print("============================\n")
    
    order_data = {
        'order': {
            'email': data.get('email'),
            'shipping_address': {
                'first_name': shipping_addr.get('first_name'),
                'last_name': shipping_addr.get('last_name'),
                'address1': shipping_addr.get('address1'),
                'address2': shipping_addr.get('address2', ''),
                'city': shipping_addr.get('city'),
                'province': province_name,
                'zip': shipping_addr.get('zip'),
                'country': 'PE'
            },
            'line_items': line_items,
            'financial_status': 'pending',
            'currency': 'PEN'
        }
    }
    
    print(f"\n=== DEBUG SHOPIFY PAYLOAD ===")
    print(f"Order data to send: {json.dumps(order_data, indent=2, ensure_ascii=False)}")
    print("=============================\n")
    
    try:
        response = requests.post(url, json=order_data, headers=headers)
        print(f"\n=== SHOPIFY RESPONSE ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print("=======================\n")
        
        response.raise_for_status()
        return {'success': True, 'data': response.json()}
    except requests.exceptions.RequestException as e:
        print(f"❌ Shopify Error: {str(e)}")
        return {'success': False, 'error': f'Error de Shopify: {str(e)}'}

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
