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
            
            # Determinar etiqueta basada en el estado de Izipay
            estado_etiqueta = self.obtener_etiqueta_por_estado_izipay(payment_link_state)
            
            # Si hay orden de Shopify asociada, procesar automáticamente
            if transaction.shopify_order_id:
                print(f"🔄 Procesando actualización automática para orden {transaction.shopify_order_id}")
                print(f"📊 Estado: {payment_link_state} -> Etiqueta: {estado_etiqueta}")
                
                # Si el pago fue exitoso, marcar como pagado
                if payment_link_state == '3':  # TERMINADO_EXITO
                    print(f"✅ Pago exitoso - Marcando orden como pagada")
                    self.update_shopify_order(transaction.shopify_order_id, 'paid')
                else:
                    # Para otros estados, solo actualizar la etiqueta
                    print(f"📝 Actualizando etiqueta sin marcar como pagada")
                    self.actualizar_solo_etiqueta_shopify(transaction.shopify_order_id, estado_etiqueta)
                
                # Agregar comentario automático sobre el estado del pago
                print(f"💬 Agregando comentario automático")
                self.agregar_comentario_pago_automatico(transaction.shopify_order_id, transaction, estado_etiqueta)
            else:
                print(f"ℹ️ Transacción sin orden de Shopify asociada")
            
            return JsonResponse({
                'success': True,
                'message': f'Estado actualizado de {old_state} a {payment_link_state}',
                'transaction_id': transaction_id,
                'etiqueta_aplicada': estado_etiqueta,
                'shopify_order_id': transaction.shopify_order_id,
                'procesamiento_automatico': bool(transaction.shopify_order_id)
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
                
                # Marcar orden como pagada usando GraphQL (más eficiente que REST)
                def marcar_orden_como_pagada_graphql(order_id):
                    """Usa GraphQL orderMarkAsPaid para marcar orden como pagada"""
                    
                    # Convertir order_id numérico a Global ID de Shopify
                    global_order_id = f"gid://shopify/Order/{order_id}"
                    
                    # Mutation GraphQL para marcar como pagada
                    mutation = """
                    mutation($orderId: ID!) {
                        orderMarkAsPaid(input: { id: $orderId }) {
                            order {
                                id
                                displayFinancialStatus
                                financialStatus
                                name
                            }
                            userErrors {
                                field
                                message
                            }
                        }
                    }
                    """
                    
                    variables = {
                        "orderId": global_order_id
                    }
                    
                    payload = {
                        "query": mutation,
                        "variables": variables
                    }
                    
                    # URL GraphQL endpoint
                    graphql_url = f"{store_url}/admin/api/2023-10/graphql.json"
                    
                    print(f"🔄 Marcando orden {order_id} como pagada via GraphQL")
                    print(f"🔗 URL GraphQL: {graphql_url}")
                    print(f"🆔 Global ID: {global_order_id}")
                    
                    response = requests.post(graphql_url, json=payload, headers=headers, timeout=30)
                    print(f"📊 Respuesta GraphQL: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Verificar si hay errores en la respuesta
                        if 'errors' in result:
                            print(f"❌ Errores GraphQL: {result['errors']}")
                            return False
                        
                        # Verificar datos de la mutación
                        order_data = result.get('data', {}).get('orderMarkAsPaid', {})
                        user_errors = order_data.get('userErrors', [])
                        
                        if user_errors:
                            print(f"❌ Errores de usuario: {user_errors}")
                            return False
                        
                        # Éxito
                        order_info = order_data.get('order', {})
                        financial_status = order_info.get('displayFinancialStatus', 'unknown')
                        order_name = order_info.get('name', order_id)
                        
                        print(f"✅ Orden {order_name} marcada como pagada exitosamente")
                        print(f"💰 Estado financiero: {financial_status}")
                        return True
                        
                    else:
                        try:
                            error_data = response.json()
                        except:
                            error_data = response.text
                        print(f"❌ Error HTTP en GraphQL: {response.status_code}")
                        print(f"   Detalle: {error_data}")
                        return False
                
                # Ejecutar actualización usando GraphQL (método recomendado)
                print(f"🚀 Marcando orden {order_id} como pagada usando GraphQL orderMarkAsPaid")
                
                exito_graphql = marcar_orden_como_pagada_graphql(order_id)
                
                if exito_graphql:
                    # Actualizar etiqueta a "pagada" después del éxito
                    self.actualizar_etiqueta_estado_pago(order_id, "pagada", headers, store_url, order_data)
                    print(f"✅ Orden actualizada exitosamente via GraphQL")
                    return True
                else:
                    # Si GraphQL falla, actualizar etiqueta a "no-pagada" 
                    self.actualizar_etiqueta_estado_pago(order_id, "no-pagada", headers, store_url, order_data)
                    print(f"⚠️ GraphQL falló, orden marcada como no-pagada")
                    return False
            else:
                print(f"ℹ️  Estado {status} no requiere transacción")
                return True
                
        except Exception as e:
            print(f"❌ Error actualizando orden Shopify: {e}")
            import traceback
            traceback.print_exc()
            return False

    def actualizar_etiqueta_estado_pago(self, order_id, estado_pago, headers, store_url, order_data):
        """
        Actualiza la etiqueta de estado de pago de manera dinámica
        Estados posibles: 'pagada', 'no-pagada', 'pendiente', 'cancelada'
        """
        try:
            # Obtener tags actuales y limpiar etiquetas de estado previas
            tags_actuales = order_data.get('tags', '')
            
            # Remover etiquetas de estado previas
            etiquetas_estado = ['pagada', 'no-pagada', 'pendiente', 'cancelada', 'izipay-paid', 'graphql-fallback']
            tags_limpiados = tags_actuales
            
            for etiqueta in etiquetas_estado:
                tags_limpiados = tags_limpiados.replace(f',{etiqueta}', '').replace(etiqueta, '')
            
            # Limpiar comas duplicadas o iniciales
            tags_limpiados = tags_limpiados.strip(',').replace(',,', ',')
            
            # Agregar nueva etiqueta de estado
            if tags_limpiados:
                nuevas_tags = f"{tags_limpiados},{estado_pago}"
            else:
                nuevas_tags = estado_pago
            
            # Actualizar orden con nueva etiqueta
            order_update = {
                'order': {
                    'id': order_id,
                    'tags': nuevas_tags
                }
            }
            
            order_update_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
            response = requests.put(order_update_url, json=order_update, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"🏷️  Etiqueta actualizada: '{estado_pago}' para orden {order_id}")
                return True
            else:
                print(f"⚠️ Error actualizando etiqueta: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error en actualizar_etiqueta_estado_pago: {e}")
            return False

    def obtener_etiqueta_por_estado_izipay(self, estado_izipay):
        """
        Mapea el estado numérico de Izipay a una etiqueta descriptiva
        Estados Izipay:
        - 1: GENERADO -> 'pendiente'
        - 2: EN_PROCESO -> 'pendiente' 
        - 3: TERMINADO_EXITO -> 'pagada'
        - 4: TERMINADO_ERROR -> 'cancelada'
        - 5: EXPIRADO -> 'cancelada'
        """
        estados_mapa = {
            '1': 'pendiente',    # GENERADO
            '2': 'pendiente',    # EN_PROCESO
            '3': 'pagada',       # TERMINADO_EXITO
            '4': 'cancelada',    # TERMINADO_ERROR
            '5': 'cancelada'     # EXPIRADO
        }
        
        estado_str = str(estado_izipay)
        etiqueta = estados_mapa.get(estado_str, 'pendiente')
        
        print(f"🏷️  Estado Izipay {estado_str} -> Etiqueta: '{etiqueta}'")
        return etiqueta
    
    def actualizar_solo_etiqueta_shopify(self, order_id, nueva_etiqueta):
        """
        Actualiza solo la etiqueta de una orden en Shopify sin marcar como pagada
        """
        try:
            print(f"🏷️  Actualizando solo etiqueta para orden {order_id}: '{nueva_etiqueta}'")
            
            # Obtener credenciales de Shopify
            shopify_credentials = ShopifyCredential.objects.filter().first()
            if not shopify_credentials:
                print("❌ No hay credenciales de Shopify configuradas")
                return False
            
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
            
            # Obtener datos actuales de la orden
            order_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
            order_response = requests.get(order_url, headers=headers, timeout=30)
            
            if order_response.status_code != 200:
                print(f"❌ Error obteniendo orden: {order_response.status_code}")
                return False
            
            order_data = order_response.json().get('order', {})
            
            # Actualizar etiqueta usando la función helper
            return self.actualizar_etiqueta_estado_pago(order_id, nueva_etiqueta, headers, store_url, order_data)
            
        except Exception as e:
            print(f"❌ Error en actualizar_solo_etiqueta_shopify: {e}")
            return False

    def agregar_comentario_pago_automatico(self, order_id, transaction, estado_etiqueta):
        """
        Agregar comentario automático con información del pago cuando cambia el estado
        """
        try:
            # Obtener credenciales de Shopify
            shopify_credentials = ShopifyCredential.objects.filter().first()
            if not shopify_credentials:
                print("❌ No hay credenciales de Shopify configuradas")
                return False
            
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
            
            # Crear mensaje según el estado
            estado_display = transaction.get_payment_link_state_display()
            monto = transaction.amount
            moneda = transaction.currency
            fecha_creacion = transaction.created_at.strftime("%d/%m/%Y %H:%M")
            fecha_webhook = transaction.webhook_received_at.strftime("%d/%m/%Y %H:%M") if transaction.webhook_received_at else "N/A"
            
            if estado_etiqueta == 'pagada':
                mensaje = f"""✅ PAGO CONFIRMADO VÍA IZIPAY
                
El cliente ya realizó el pago de {monto} {moneda}.

📊 Detalles del pago:
• Estado: {estado_display} 
• Monto: {monto} {moneda}
• Fecha creación: {fecha_creacion}
• Última actualización: {fecha_webhook}
• Transaction ID: {transaction.transaction_id}

🔗 Link de pago para verificación:
{transaction.payment_link_url}

ℹ️ El sistema Izipay confirma que este pago ha sido procesado exitosamente."""
                
            elif estado_etiqueta == 'pendiente':
                mensaje = f"""⏳ PAGO PENDIENTE VÍA IZIPAY
                
El pago de {monto} {moneda} está en proceso.

📊 Detalles:
• Estado: {estado_display}
• Monto: {monto} {moneda}  
• Transaction ID: {transaction.transaction_id}
• Última actualización: {fecha_webhook}

🔗 Link de pago:
{transaction.payment_link_url}

ℹ️ El cliente puede completar el pago usando el link proporcionado."""
                
            elif estado_etiqueta == 'cancelada':
                mensaje = f"""❌ PAGO CANCELADO/EXPIRADO VÍA IZIPAY
                
El pago de {monto} {moneda} no fue completado.

📊 Detalles:
• Estado: {estado_display}
• Monto: {monto} {moneda}
• Transaction ID: {transaction.transaction_id}
• Última actualización: {fecha_webhook}

ℹ️ Será necesario generar un nuevo link de pago si el cliente desea continuar."""
            else:
                mensaje = f"""📋 ACTUALIZACIÓN DE PAGO VÍA IZIPAY
                
Estado del pago actualizado.

📊 Detalles:
• Estado: {estado_display}
• Monto: {monto} {moneda}
• Transaction ID: {transaction.transaction_id} 
• Última actualización: {fecha_webhook}

🔗 Link de pago:
{transaction.payment_link_url}"""
            
            # Obtener la orden actual para agregar la nota
            order_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
            order_response = requests.get(order_url, headers=headers, timeout=30)
            
            if order_response.status_code == 200:
                order_current = order_response.json().get('order', {})
                current_note = order_current.get('note', '')
                
                # Agregar nuestro mensaje a las notas existentes
                if current_note and not "VÍA IZIPAY" in current_note:
                    nueva_nota = f"{current_note}\n\n---\n\n{mensaje}"
                elif "VÍA IZIPAY" in current_note:
                    # Reemplazar nota anterior de Izipay
                    lines = current_note.split('\n')
                    filtered_lines = []
                    skip_izipay_section = False
                    
                    for line in lines:
                        if "VÍA IZIPAY" in line:
                            skip_izipay_section = True
                            continue
                        elif line.strip() == "---" and skip_izipay_section:
                            skip_izipay_section = False
                            continue
                        elif not skip_izipay_section:
                            filtered_lines.append(line)
                    
                    base_note = '\n'.join(filtered_lines).strip()
                    if base_note:
                        nueva_nota = f"{base_note}\n\n---\n\n{mensaje}"
                    else:
                        nueva_nota = mensaje
                else:
                    nueva_nota = mensaje
                
                # Actualizar la orden con la nueva nota
                update_with_note = {
                    'order': {
                        'id': order_id,
                        'note': nueva_nota
                    }
                }
                
                note_response = requests.put(order_url, json=update_with_note, headers=headers, timeout=30)
                
                if note_response.status_code == 200:
                    print(f"💬 Comentario automático agregado a la orden {order_id} - Estado: {estado_etiqueta}")
                    return True
                else:
                    print(f"⚠️ Error agregando comentario automático: {note_response.status_code}")
                    return False
            else:
                print(f"❌ Error obteniendo orden para comentario: {order_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error en agregar_comentario_pago_automatico: {e}")
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
                
                if payment_link_info.get('state') != transaction.payment_link_state:
                    old_state = transaction.payment_link_state
                    transaction.payment_link_state = payment_link_info.get('state')
                    transaction.save()
                    
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
            
            shopify_credentials = ShopifyCredential.objects.filter().first()
            if not shopify_credentials:
                print("❌ No hay credenciales de Shopify configuradas")
                return False
            
            headers = {
                'X-Shopify-Access-Token': shopify_credentials.access_token,
                'Content-Type': 'application/json'
            }
            
            store_url = shopify_credentials.store_url
            if not store_url.startswith('https'):
                if store_url.startswith('http://'):
                    store_url = store_url.replace('http://', 'https://')
                else:
                    store_url = f"https://{shopify_credentials.store_name}.myshopify.com"
            
            if status == 'paid':
                order_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
                order_response = requests.get(order_url, headers=headers, timeout=30)
                
                if order_response.status_code != 200:
                    print(f"❌ Error obteniendo orden: {order_response.status_code}")
                    return False
                
                order_data = order_response.json().get('order', {})
                order_data.get('total_price', '0.00')
                
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

@method_decorator(csrf_exempt, name='dispatch')
class TestGraphQLView(View):
    """
    Vista de prueba para testear la mutación GraphQL orderMarkAsPaid
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id', '5973851226407')
            
            print(f"🧪 === INICIANDO PRUEBA GRAPHQL ===")
            print(f"📦 Orden ID: {order_id}")
            
            shopify_credentials = ShopifyCredential.objects.filter().first()
            if not shopify_credentials:
                return JsonResponse({'success': False, 'error': 'No hay credenciales de Shopify'}, status=500)
            
            headers = {
                'X-Shopify-Access-Token': shopify_credentials.access_token,
                'Content-Type': 'application/json'
            }
            
            store_url = shopify_credentials.store_url
            if not store_url.startswith('https'):
                if store_url.startswith('http://'):
                    store_url = store_url.replace('http://', 'https://')
                else:
                    store_url = f"https://{shopify_credentials.store_name}.myshopify.com"
            
            global_order_id = f"gid://shopify/Order/{order_id}"
            
            mutation = """
            mutation($orderId: ID!) {
                orderMarkAsPaid(input: { id: $orderId }) {
                    order {
                        id
                        displayFinancialStatus
                        financialStatus
                        name
                    }
                    userErrors {
                        field
                        message
                    }
                }
            }
            """
            
            variables = {
                "orderId": global_order_id
            }
            
            payload = {
                "query": mutation,
                "variables": variables
            }
            
            graphql_url = f"{store_url}/admin/api/2023-10/graphql.json"
            
            print(f"🔗 URL GraphQL: {graphql_url}")
            print(f"🆔 Global ID: {global_order_id}")
            print(f"📦 Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(graphql_url, json=payload, headers=headers, timeout=30)
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                
                if 'errors' in result:
                    print(f"❌ Errores GraphQL: {result['errors']}")
                    return JsonResponse({
                        'success': False,
                        'errors': result['errors'],
                        'graphql_response': result
                    })
                
                order_data = result.get('data', {}).get('orderMarkAsPaid', {})
                user_errors = order_data.get('userErrors', [])
                
                if user_errors:
                    print(f"❌ User Errors: {user_errors}")
                    return JsonResponse({
                        'success': False,
                        'user_errors': user_errors,
                        'graphql_response': result
                    })
                
                order_info = order_data.get('order', {})
                financial_status = order_info.get('displayFinancialStatus')
                order_name = order_info.get('name')
                
                print(f"✅ ÉXITO: Orden {order_name} - Estado: {financial_status}")
                
                return JsonResponse({
                    'success': True,
                    'order_name': order_name,
                    'financial_status': financial_status,
                    'graphql_response': result,
                    'message': f'Orden {order_name} marcada como pagada exitosamente'
                })
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error HTTP: {response.status_code}',
                    'response_text': response.text
                }, status=500)
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=500)