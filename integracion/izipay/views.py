import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from .models import IzipayCredential
import uuid
from datetime import datetime

class GenerateTokenView(View):
    """
    Vista para generar token de sesión de Izipay
    Endpoint: POST /izipay/generate-token/
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            # Obtener datos del request
            data = json.loads(request.body)
            transaction_id = data.get('transactionId')
            order_number = data.get('orderNumber')
            amount = data.get('amount')
            
            # Validar datos requeridos
            if not all([transaction_id, order_number, amount]):
                return JsonResponse({
                    'success': False,
                    'error': 'Faltan datos requeridos: transactionId, orderNumber, amount'
                }, status=400)
            
            # Obtener credenciales de Izipay
            try:
                credentials = IzipayCredential.objects.first()
                if not credentials:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se encontraron credenciales de Izipay configuradas'
                    }, status=500)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error obteniendo credenciales: {str(e)}'
                }, status=500)
            
            # Preparar payload para Izipay según documentación oficial
            izipay_payload = {
                'transactionId': transaction_id,
                'requestSource': 'ECOMMERCE',
                'merchantCode': credentials.merchant_code,
                'orderNumber': order_number,
                'publicKey': credentials.api_key,  # La documentación lo llama publicKey
                'amount': str(amount)  # Debe ser string según la documentación
            }
            
            # Llamar a la API de Izipay para generar token
            izipay_response = self.call_izipay_token_api(izipay_payload)
            
            if izipay_response.get('success'):
                return JsonResponse({
                    'success': True,
                    'token': izipay_response['token'],
                    'transactionId': transaction_id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': izipay_response.get('error', 'Error desconocido de Izipay')
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido en el request'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=500)
    
    def call_izipay_token_api(self, payload):
        """
        Llama a la API de Izipay para generar el token de sesión
        Endpoint oficial: https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate
        """
        try:
            # URL de la API de Izipay (sandbox)
            url = 'https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate'
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Realizar petición a Izipay
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verificar respuesta según documentación
                if result.get('code') == '00' and result.get('message') == 'OK':
                    return {
                        'success': True,
                        'token': result['response']['token']
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Error de Izipay: {result.get('message', 'Error desconocido')}"
                    }
            else:
                return {
                    'success': False,
                    'error': f'Error HTTP {response.status_code}: {response.text}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout al conectar con Izipay'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Error de conexión con Izipay: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error inesperado: {str(e)}'
            }

# Función auxiliar para generar transaction ID único
def generate_transaction_id():
    """
    Genera un ID de transacción único
    Formato: TXN-timestamp-random
    """
    timestamp = int(datetime.now().timestamp() * 1000)
    random_part = str(uuid.uuid4())[:8]
    return f"TXN-{timestamp}-{random_part}"
