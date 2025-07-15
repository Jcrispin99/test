from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
import json
import requests
from .models import IzipayCredential, IzipayTransactionCounter


class IzipayGenerateTokenView(View):
    """
    Vista para generar token de sesión de Izipay desde el backend
    Endpoint: POST /izipay/generate-token/
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            # Obtener datos del request
            data = json.loads(request.body)
            
            # Validar datos requeridos
            required_fields = ['amount', 'orderNumber']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Campo requerido: {field}'
                    }, status=400)
            
            # Obtener credenciales de Izipay
            try:
                credential = IzipayCredential.objects.first()
                if not credential:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se encontraron credenciales de Izipay configuradas'
                    }, status=500)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error al obtener credenciales: {str(e)}'
                }, status=500)
            
            # Generar transaction ID único
            transaction_id = IzipayTransactionCounter.get_next_transaction_id()
            
            # Preparar payload para Izipay
            payload = {
                "requestSource": "ECOMMERCE",
                "merchantCode": credential.merchant_code,
                "orderNumber": data['orderNumber'],
                "publicKey": credential.public_key,
                "amount": "{:.2f}".format(int(data['amount']) / 100)
            }
            
            print(f"\n=== DEBUG IZIPAY TOKEN ===")
            print(f"Amount received from frontend: {data['amount']} (type: {type(data['amount'])})")
            print(f"Payload to send to Izipay: {payload}")
            print("==========================\n")
            
            headers = {
                "transactionId": transaction_id,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # URL de la API de Izipay (sandbox)
            url = "https://sandbox-api-pw.izipay.pe/gateway/api/v1/proxy-cors/https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate"
            
            # Realizar petición a Izipay
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                response_data = response.json()
                
                print(f"\n=== IZIPAY RESPONSE ===")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response_data}")
                print("=======================\n")
                
                # Verificar respuesta de Izipay
                if response.status_code == 200 and response_data.get('code') == '00':
                    return JsonResponse({
                        'success': True,
                        'token': response_data.get('response', {}).get('token'),
                        'userOrg': response_data.get('response', {}).get('userOrg'),
                        'userScoring': response_data.get('response', {}).get('userScoring'),
                        'transactionId': transaction_id,
                        'orderNumber': data['orderNumber'],
                        'amount': data['amount']
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f"Error de Izipay: {response_data.get('message', 'Error desconocido')}",
                        'izipay_code': response_data.get('code'),
                        'izipay_response': response_data
                    }, status=400)
                    
            except requests.exceptions.Timeout:
                return JsonResponse({
                    'success': False,
                    'error': 'Timeout: La petición a Izipay tardó demasiado'
                }, status=408)
            except requests.exceptions.ConnectionError:
                return JsonResponse({
                    'success': False,
                    'error': 'Error de conexión: No se pudo conectar con Izipay'
                }, status=503)
            except requests.exceptions.RequestException as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error en la petición a Izipay: {str(e)}'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos JSON inválidos'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=500)


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