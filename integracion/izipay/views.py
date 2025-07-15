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
from .models import IzipayCredential, IzipayTransactionCounter, PaymentTransaction
from shopify.models import ShopifyCredential


class IzipayPaymentLinkView(View):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            required_fields = ['amount', 'orderNumber', 'customerEmail']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'success': False, 'error': f'Campo requerido: {field}'}, status=400)
            
            credential = IzipayCredential.objects.filter(is_active=True).first()
            if not credential:
                return JsonResponse({'success': False, 'error': 'No hay credenciales activas'}, status=500)
            
            # Formatear amount correctamente para Izipay (decimal con exactamente 2 decimales)
            amount_decimal = float(data['amount'])
            amount_str = "{:.2f}".format(amount_decimal)
            transaction_id = f"100{str(datetime.now().microsecond)[:3]}"
            
            print(f"🔍 [Backend] Datos recibidos:")
            print(f"   Amount original: {data['amount']} (tipo: {type(data['amount'])})")
            print(f"   Amount formateado: {amount_str}")
            print(f"   Transaction ID: {transaction_id}")
            
            now = datetime.now()
            expiration_time = now + timedelta(hours=24)
            expiration_minutes = expiration_time.minute
            if expiration_minutes not in [0, 30]:
                expiration_minutes = 0 if expiration_minutes < 15 else 30
                expiration_time = expiration_time.replace(minute=expiration_minutes, second=0, microsecond=0)
            expiration_str = expiration_time.strftime("%Y-%m-%d %H:%M:00.000")
            
            clean_reference = f"REF{transaction_id.zfill(7)}"
            
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
                    "firstName": data.get('billing', {}).get('firstName', data.get('customerName', 'Cliente').split()[0] if data.get('customerName') else 'Cliente'),
                    "lastName": data.get('billing', {}).get('lastName', ' '.join(data.get('customerName', 'Apellido').split()[1:]) if len(data.get('customerName', '').split()) > 1 else 'Apellido'),
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
                    "firstName": data.get('shipping', {}).get('firstName') or data.get('billing', {}).get('firstName') or data.get('customerName', 'Cliente').split()[0] if data.get('customerName') else 'Cliente',
                    "lastName": data.get('shipping', {}).get('lastName') or data.get('billing', {}).get('lastName') or ' '.join(data.get('customerName', 'Apellido').split()[1:]) if len(data.get('customerName', '').split()) > 1 else 'Apellido',
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
                        
                        payment_link_url = payment_link_data.get('urL_PaymentLink')
                        payment_link_id = payment_link_data.get('paymentLinkId')
                        
                        # Guardar transacción en la base de datos
                        transaction = PaymentTransaction.objects.create(
                            transaction_id=transaction_id,
                            shopify_order_id=data.get('shopifyOrderId'),  # Si viene de Shopify
                            order_number=data['orderNumber'],
                            payment_link_id=payment_link_id,
                            payment_link_url=payment_link_url,
                            payment_link_state='1',  # GENERADO
                            amount=float(data['amount']),
                            currency='PEN',
                            customer_email=data['customerEmail'],
                            customer_name=data.get('customerName', 'Cliente')
                        )
                        
                        return JsonResponse({
                            'success': True,
                            'paymentLink': payment_link_url,
                            'paymentLinkId': payment_link_id,
                            'transactionId': transaction_id,
                            'message': 'Payment Link generado exitosamente'
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

@method_decorator(csrf_exempt, name='dispatch')
class IzipayWebhookView(View):
    """
    Webhook para recibir notificaciones de cambio de estado de Izipay
    """
    
    def post(self, request):
        try:
            # Izipay puede enviar datos como form-data o JSON
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
            
            # Extraer datos del webhook
            transaction_id = data.get('transactionId') or data.get('transaction_id')
            payment_link_state = data.get('state') or data.get('paymentLinkState')
            payment_link_id = data.get('paymentLinkId') or data.get('payment_link_id')
            
            if not transaction_id:
                return JsonResponse({'success': False, 'error': 'Transaction ID requerido'}, status=400)
            
            # Buscar la transacción
            try:
                transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            except PaymentTransaction.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Transacción no encontrada'}, status=404)
            
            # Actualizar estado
            old_state = transaction.payment_link_state
            transaction.payment_link_state = payment_link_state
            transaction.webhook_received_at = datetime.now()
            
            if payment_link_id:
                transaction.payment_link_id = payment_link_id
                
            transaction.save()
            
            # Si el pago fue exitoso, actualizar orden de Shopify
            if payment_link_state == '3' and transaction.shopify_order_id:  # TERMINADO_EXITO
                self.update_shopify_order(transaction.shopify_order_id, 'paid')
            
            return JsonResponse({
                'success': True,
                'message': f'Estado actualizado de {old_state} a {payment_link_state}',
                'transaction_id': transaction_id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def update_shopify_order(self, order_id, status):
        """
        Actualizar el estado de la orden en Shopify creando una transacción de pago
        """
        try:
            print(f"📦 Actualizando orden Shopify {order_id} a estado: {status}")
            
            # Obtener credenciales de Shopify
            shopify_credentials = ShopifyCredential.objects.filter().first()
            if not shopify_credentials:
                print("❌ No hay credenciales de Shopify configuradas")
                return False
            
            print(f"🏪 Usando tienda: {shopify_credentials.store_name}")
            
            # Configurar headers para Shopify API
            headers = {
                'X-Shopify-Access-Token': shopify_credentials.access_token,
                'Content-Type': 'application/json'
            }
            
            # Construir URL de la API de Shopify
            store_url = shopify_credentials.store_url
            if not store_url.startswith('https'):
                # Forzar HTTPS y corregir formato si es necesario
                if store_url.startswith('http://'):
                    store_url = store_url.replace('http://', 'https://')
                else:
                    store_url = f"https://{shopify_credentials.store_name}.myshopify.com"
            
            if status == 'paid':
                # Primero obtener los detalles de la orden
                order_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
                order_response = requests.get(order_url, headers=headers, timeout=30)
                
                if order_response.status_code != 200:
                    print(f"❌ Error obteniendo orden: {order_response.status_code}")
                    return False
                
                order_data = order_response.json().get('order', {})
                total_price = order_data.get('total_price', '0.00')
                
                print(f"💰 Total de la orden: {total_price}")
                
                # Marcar la orden como pagada usando el endpoint de fulfillment
                # Primero verificar si la orden ya está pagada
                current_financial_status = order_data.get('financial_status', '')
                
                if current_financial_status == 'paid':
                    print(f"ℹ️  La orden {order_id} ya está marcada como pagada")
                    return True
                
                # Crear transacción de pago en Shopify usando el enfoque correcto
                def crear_transaccion_en_shopify(order_id, monto, moneda="PEN", gateway="Izipay"):
                    # URL para crear transacción de pago
                    url = f"{store_url}/admin/api/2023-10/orders/{order_id}/transactions.json"
                    
                    payload = {
                        "transaction": {
                            "kind": "sale",  # Transacción directa de venta
                            "status": "success",
                            "amount": str(monto),
                            "currency": moneda,
                            "gateway": gateway
                        }
                    }
                    
                    print(f"💳 Creando transacción de pago para orden {order_id}")
                    print(f"🔗 URL transacción: {url}")
                    print(f"📦 Payload: {payload}")
                    
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    print(f"📊 Shopify API Response: {response.status_code}")
                    
                    if response.status_code == 201:
                        transaction_data = response.json()
                        transaction_id = transaction_data.get('transaction', {}).get('id')
                        financial_status = transaction_data.get('transaction', {}).get('status')
                        print(f"✅ Transacción creada exitosamente: ID {transaction_id}")
                        print(f"💰 Estado financiero: {financial_status}")
                        return True
                    else:
                        error_data = response.text
                        try:
                            error_json = response.json()
                            error_data = error_json
                        except:
                            pass
                        print(f"❌ Error creando transacción: {response.status_code}")
                        print(f"   Respuesta: {error_data}")
                        return False
                
                # Ejecutar la creación de transacción
                exito = crear_transaccion_en_shopify(order_id, total_price)
                
                if exito:
                    print(f"✅ Orden Shopify actualizada exitosamente")
                    return True
                else:
                    # Como fallback, marcar con tag
                    print(f"⚠️  Usando fallback: marcar orden con tag")
                    fallback_update = {
                        'order': {
                            'id': order_id,
                            'tags': order_data.get('tags', '') + ',izipay-paid'
                        }
                    }
                    
                    order_update_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
                    fallback_response = requests.put(order_update_url, json=fallback_update, headers=headers, timeout=30)
                    
                    if fallback_response.status_code == 200:
                        print(f"✅ Orden marcada con tag de pago Izipay como fallback")
                        return True
                    else:
                        print(f"❌ Error en fallback: {fallback_response.status_code}")
                        return False
            else:
                print(f"ℹ️  Estado {status} no requiere transacción")
                return True
                
        except Exception as e:
            print(f"❌ Error actualizando orden Shopify: {e}")
            import traceback
            traceback.print_exc()
            return False


class PaymentLinkSearchView(View):
    """
    Vista para buscar y consultar el estado de un Payment Link
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            payment_link_id = data.get('paymentLinkId')
            if not payment_link_id:
                return JsonResponse({'success': False, 'error': 'paymentLinkId requerido'}, status=400)
            
            try:
                transaction = PaymentTransaction.objects.get(payment_link_id=payment_link_id)
            except PaymentTransaction.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Payment Link no encontrado'}, status=404)
            
            credential = IzipayCredential.objects.filter(is_active=True).first()
            if not credential:
                return JsonResponse({'success': False, 'error': 'No hay credenciales activas'}, status=500)
            
            transaction_id = f"100{str(datetime.now().microsecond)[:3]}"
            
            # 1. Generar token
            token_payload = {
                "requestSource": "ECOMMERCE", 
                "merchantCode": credential.merchant_code,
                "orderNumber": credential.merchant_code,
                "publicKey": credential.public_key,
                "amount": "0.00"
            }
            
            token_headers = {
                "transactionId": transaction_id,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            token_url = "https://sandbox-api-pw.izipay.pe/gateway/api/v1/proxy-cors/https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate"
            
            token_response = requests.post(token_url, json=token_payload, headers=token_headers, timeout=30)
            token_data = token_response.json()
            
            if token_response.status_code != 200 or token_data.get('code') != '00':
                return JsonResponse({
                    'success': False,
                    'error': f"Error generando token: {token_data.get('message', 'Error desconocido')}"
                }, status=400)
            
            session_token = token_data.get('response', {}).get('token')
            
            # 2. Consultar Payment Link
            search_payload = {
                "paymentLinkId": payment_link_id,
                "merchantCode": credential.merchant_code,
                "languageUsed": "ESP"
            }
            
            search_headers = {
                "Authorization": f"Bearer {session_token}",
                "transactionId": transaction_id,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            search_url = "https://sandbox-api-pw.izipay.pe/gateway/api/v1/proxy-cors/https://sandbox-api-pw.izipay.pe/paymentlink/api/v1/process/search"
            
            search_response = requests.post(search_url, json=search_payload, headers=search_headers, timeout=30)
            search_data = search_response.json()
            
            if search_response.status_code == 200 and search_data.get('code') == '00':
                payment_link_info = search_data.get('response', {})
                
                # Actualizar estado si es diferente
                if payment_link_info.get('state') != transaction.payment_link_state:
                    old_state = transaction.payment_link_state
                    transaction.payment_link_state = payment_link_info.get('state')
                    transaction.save()
                    
                    # Si el pago fue exitoso, actualizar orden de Shopify
                    if payment_link_info.get('state') == '3' and transaction.shopify_order_id:
                        self.update_shopify_order(transaction.shopify_order_id, 'paid')
                
                return JsonResponse({
                    'success': True,
                    'transaction': {
                        'transaction_id': transaction.transaction_id,
                        'shopify_order_id': transaction.shopify_order_id,
                        'order_number': transaction.order_number,
                        'payment_link_id': transaction.payment_link_id,
                        'payment_link_url': transaction.payment_link_url,
                        'payment_link_state': transaction.payment_link_state,
                        'payment_link_state_display': transaction.get_payment_link_state_display(),
                        'amount': str(transaction.amount),
                        'currency': transaction.currency,
                        'customer_email': transaction.customer_email,
                        'customer_name': transaction.customer_name,
                        'created_at': transaction.created_at.isoformat(),
                        'is_successful': transaction.is_successful,
                        'is_failed': transaction.is_failed
                    },
                    'izipay_data': payment_link_info
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f"Error consultando Payment Link: {search_data.get('message', 'Error desconocido')}"
                }, status=400)
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def update_shopify_order(self, order_id, status):
        """
        Actualizar el estado de la orden en Shopify creando una transacción de pago
        """
        try:
            print(f"📦 Actualizando orden Shopify {order_id} a estado: {status}")
            
            # Obtener credenciales de Shopify
            shopify_credentials = ShopifyCredential.objects.filter().first()
            if not shopify_credentials:
                print("❌ No hay credenciales de Shopify configuradas")
                return False
            
            # Configurar headers para Shopify API
            headers = {
                'X-Shopify-Access-Token': shopify_credentials.access_token,
                'Content-Type': 'application/json'
            }
            
            # Construir URL de la API de Shopify
            store_url = shopify_credentials.store_url
            if not store_url.startswith('https'):
                if store_url.startswith('http://'):
                    store_url = store_url.replace('http://', 'https://')
                else:
                    store_url = f"https://{shopify_credentials.store_name}.myshopify.com"
            
            if status == 'paid':
                # Obtener detalles de la orden
                order_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
                order_response = requests.get(order_url, headers=headers, timeout=30)
                
                if order_response.status_code != 200:
                    print(f"❌ Error obteniendo orden: {order_response.status_code}")
                    return False
                
                order_data = order_response.json().get('order', {})
                total_price = order_data.get('total_price', '0.00')
                
                # Marcar la orden como pagada usando tags
                order_update_data = {
                    'order': {
                        'id': order_id,
                        'tags': order_data.get('tags', '') + ',izipay-paid'
                    }
                }
                
                order_update_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
                response = requests.put(order_update_url, json=order_update_data, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    print(f"✅ Orden Shopify {order_id} marcada con tag Izipay")
                    return True
                else:
                    print(f"❌ Error actualizando orden Shopify: {response.status_code} - {response.text}")
                    return False
            else:
                return True
                
        except Exception as e:
            print(f"❌ Error actualizando orden Shopify: {e}")
            return False


class PaymentTransactionListView(View):
    """
    Vista para listar y consultar transacciones (tabla pivote)
    """
    
    def get(self, request):
        transactions = PaymentTransaction.objects.all().order_by('-created_at')
        
        # Filtros opcionales
        state = request.GET.get('state')
        if state:
            transactions = transactions.filter(payment_link_state=state)
        
        shopify_order_id = request.GET.get('shopify_order_id')
        if shopify_order_id:
            transactions = transactions.filter(shopify_order_id=shopify_order_id)
        
        # Convertir a lista de diccionarios
        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                'transaction_id': transaction.transaction_id,
                'shopify_order_id': transaction.shopify_order_id,
                'order_number': transaction.order_number,
                'payment_link_id': transaction.payment_link_id,
                'payment_link_url': transaction.payment_link_url,
                'payment_link_state': transaction.payment_link_state,
                'payment_link_state_display': transaction.get_payment_link_state_display(),
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'customer_email': transaction.customer_email,
                'customer_name': transaction.customer_name,
                'created_at': transaction.created_at.isoformat(),
                'updated_at': transaction.updated_at.isoformat(),
                'webhook_received_at': transaction.webhook_received_at.isoformat() if transaction.webhook_received_at else None,
                'is_successful': transaction.is_successful,
                'is_failed': transaction.is_failed
            })
        
        return JsonResponse({
            'success': True,
            'transactions': transactions_data,
            'total': len(transactions_data)
        })