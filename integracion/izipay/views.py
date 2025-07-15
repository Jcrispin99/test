from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
import json
import re
import requests
import hmac
import traceback
from datetime import datetime, timedelta
from .models import IzipayCredential, IzipayTransactionCounter


class IzipayPaymentLinkView(View):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            required_fields = ['amount', 'orderNumber', 'customerEmail', 'customerName']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Campo requerido: {field}'
                    }, status=400)
            
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
            
            transaction_id = IzipayTransactionCounter.get_next_transaction_id()
            
            expiration_date = datetime.now() + timedelta(hours=24)
            if expiration_date.minute < 30:
                expiration_date = expiration_date.replace(minute=30, second=0, microsecond=0)
            else:
                expiration_date = expiration_date.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            expiration_str = expiration_date.strftime("%Y-%m-%d %H:%M:%S.000")
            
            amount_decimal = float(data['amount'])
            amount_str = "{:.2f}".format(amount_decimal)
            
            clean_reference = f"REF{str(transaction_id).zfill(7)}"
            
            def clean_phone_number(phone):
                if not phone:
                    return '987654321'
                
                cleaned = re.sub(r'[\s\-\(\)\+]', '', str(phone))
                
                if cleaned.startswith('51'):
                    cleaned = cleaned[2:]
                elif cleaned.startswith('0051'):
                    cleaned = cleaned[4:]
                
                if not cleaned.isdigit():
                    return '987654321'
                
                if len(cleaned) == 9 and cleaned.startswith('9'):
                    return cleaned
                elif len(cleaned) == 8:
                    return '0' + cleaned
                elif len(cleaned) > 9:
                    return cleaned[-9:]
                else:
                    return '987654321'
            
            payload = {
                "merchantCode": credential.merchant_code,
                "productDescription": data.get('productDescription', "Orden de compra online"),
                "amount": amount_str,
                "currency": "PEN",
                "expirationDate": expiration_str,
                "wayOfUse": "INDIVIDUAL",
                "email_Notification": data['customerEmail'],
                "payMethod": "CARD",
                "referenceCode": clean_reference,
                "languageUsed": "ESP",
                "urL_Terms_and_Conditions": "https://www.izipay.pe/pdf/terminos-y-condiciones-formulario-pago",
                "billing": {
                    "firstName": data.get('billing', {}).get('firstName', data['customerName'].split()[0] if data['customerName'] else 'Cliente'),
                    "lastName": data.get('billing', {}).get('lastName', ' '.join(data['customerName'].split()[1:]) if len(data['customerName'].split()) > 1 else 'Apellido'),
                    "email": data['customerEmail'],
                    "phoneNumber": clean_phone_number(data.get('billing', {}).get('phoneNumber') or data.get('billing', {}).get('phone')),
                    "street": data.get('billing', {}).get('address') or 'Dirección no especificada',
                    "postalCode": data.get('billing', {}).get('zipCode') or '15074',
                    "city": data.get('billing', {}).get('city') or 'Lima',
                    "state": data.get('billing', {}).get('region') or data.get('billing', {}).get('state') or 'Lima',
                    "country": "PE",
                    "documentType": "DNI",
                    "document": "12345678"
                },
                "shipping": {
                    "firstName": data.get('shipping', {}).get('firstName') or data.get('billing', {}).get('firstName') or data['customerName'].split()[0] if data['customerName'] else 'Cliente',
                    "lastName": data.get('shipping', {}).get('lastName') or data.get('billing', {}).get('lastName') or ' '.join(data['customerName'].split()[1:]) if len(data['customerName'].split()) > 1 else 'Apellido',
                    "email": data['customerEmail'],
                    "phoneNumber": clean_phone_number(data.get('shipping', {}).get('phoneNumber') or data.get('shipping', {}).get('phone') or data.get('billing', {}).get('phoneNumber') or data.get('billing', {}).get('phone')),
                    "street": data.get('shipping', {}).get('address') or data.get('billing', {}).get('address') or 'Dirección no especificada',
                    "postalCode": data.get('shipping', {}).get('zipCode') or data.get('billing', {}).get('zipCode') or '15074',
                    "city": data.get('shipping', {}).get('city') or data.get('billing', {}).get('city') or 'Lima',
                    "state": data.get('shipping', {}).get('region') or data.get('shipping', {}).get('state') or data.get('billing', {}).get('region') or data.get('billing', {}).get('state') or 'Lima',
                    "country": "PE",
                    "documentType": "DNI",
                    "document": "87654321"
                },
                "customFields": [
                    {
                        "name": "field1",
                        "value": data['orderNumber']
                    }
                ]
            }
            
            clean_order_number = credential.merchant_code
            
            token_payload = {
                "requestSource": "ECOMMERCE", 
                "merchantCode": credential.merchant_code,
                "orderNumber": clean_order_number,
                "publicKey": credential.public_key,
                "amount": "0.00"
            }
            
            token_headers = {
                "transactionId": transaction_id,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            token_url = "https://sandbox-api-pw.izipay.pe/gateway/api/v1/proxy-cors/https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate"
            
            try:
                token_response = requests.post(token_url, json=token_payload, headers=token_headers, timeout=30)
                token_data = token_response.json()
                
                if token_response.status_code != 200 or token_data.get('code') != '00':
                    return JsonResponse({
                        'success': False,
                        'error': f"Error generando token: {token_data.get('message', 'Error desconocido')}",
                        'token_response': token_data
                    }, status=400)
                
                session_token = token_data.get('response', {}).get('token')
                if not session_token:
                    return JsonResponse({
                        'success': False,
                        'error': "No se pudo obtener el token de sesión",
                        'token_response': token_data
                    }, status=400)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error generando token de sesión: {str(e)}'
                }, status=500)
            
            payment_link_headers = {
                "transactionId": transaction_id,
                "Authorization": session_token,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            url = "https://sandbox-api-pw.izipay.pe/paymentlink/api/v1/process/generate"
            
            try:
                response = requests.post(url, json=payload, headers=payment_link_headers, timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if response_data.get('code') == '0' and 'response' in response_data:
                        payment_link_data = response_data['response']
                        return JsonResponse({
                            'success': True,
                            'paymentLink': payment_link_data.get('urL_PaymentLink'),
                            'paymentLinkId': payment_link_data.get('paymentLinkId'),
                            'transactionId': transaction_id,
                            'orderNumber': data['orderNumber'],
                            'amount': data['amount'],
                            'expirationDate': expiration_str,
                            'merchantCode': payment_link_data.get('merchantCode'),
                            'state': payment_link_data.get('state')
                        })
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': f"Error de Izipay: {response_data.get('message', 'Error desconocido')}",
                            'izipay_code': response_data.get('code'),
                            'izipay_response': response_data
                        }, status=400)
                else:
                    try:
                        error_data = response.json()
                    except:
                        error_data = {'message': response.text}
                        
                    return JsonResponse({
                        'success': False,
                        'error': f"Error de Izipay: {error_data.get('message', 'Error desconocido')}",
                        'status_code': response.status_code,
                        'izipay_response': error_data
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
                
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': 'Datos JSON inválidos'
            }, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=500)

class IzipayTestView(View):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            if not data:
                return JsonResponse({
                    'success': False,
                    'error': 'No se recibieron datos'
                }, status=400)
            
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