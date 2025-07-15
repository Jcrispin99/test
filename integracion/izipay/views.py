from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
import json


class IzipayTestView(View):
    """
    Vista de prueba para Izipay - Solo recibe y muestra datos
    Endpoint: POST /izipay/process/
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            # Obtener datos del checkout
            data = json.loads(request.body)
            
            # Log de los datos recibidos para debugging
            print("\n=== DATOS RECIBIDOS EN IZIPAY ===")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=================================")
            
            # Validar que lleguen datos
            if not data:
                return JsonResponse({
                    'success': False,
                    'error': 'No se recibieron datos'
                }, status=400)
            
            # Simular respuesta exitosa para que el flujo continúe
            return JsonResponse({
                'success': True,
                'message': 'Datos recibidos en Izipay (modo testing)',
                'data_summary': {
                    'amount': data.get('amount'),
                    'customer_email': data.get('customer', {}).get('email'),
                    'order_reference': data.get('order_reference'),
                    'items_count': len(data.get('items', []))
                },
                'note': 'Esta es solo una respuesta de prueba para verificar el flujo'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos JSON inválidos'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error: {str(e)}'
            }, status=500)