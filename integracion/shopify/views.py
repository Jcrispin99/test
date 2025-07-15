from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
import json
import hmac
import hashlib
import base64
from .models import ShopifyCredential


@method_decorator(csrf_exempt, name='dispatch')
class ShopifyOrderPaidWebhookView(View):
    """
    Webhook para recibir notificaciones cuando una orden de Shopify sea pagada
    """
    
    def post(self, request):
        try:
            # Obtener datos del webhook
            data = json.loads(request.body)
            
            order_id = data.get('id')
            financial_status = data.get('financial_status')
            
            print(f"🛒 [Shopify Webhook] Orden {order_id} - Estado: {financial_status}")
            print(f"📧 Email: {data.get('email')}")
            print(f"💰 Total: {data.get('total_price')} {data.get('currency')}")
            
            # Aquí puedes agregar lógica adicional cuando una orden sea pagada
            # Por ejemplo, actualizar inventario, enviar emails, etc.
            
            if financial_status == 'paid':
                print(f"✅ Procesando orden pagada: {order_id}")
                # Lógica adicional para órdenes pagadas
                self.process_paid_order(data)
            
            return JsonResponse({
                'success': True,
                'message': f'Webhook procesado para orden {order_id}',
                'financial_status': financial_status
            })
            
        except Exception as e:
            print(f"❌ Error procesando webhook de Shopify: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def process_paid_order(self, order_data):
        """
        Procesar orden pagada desde Shopify
        """
        try:
            order_id = order_data.get('id')
            total_price = order_data.get('total_price')
            customer_email = order_data.get('email')
            
            print(f"📦 Procesando orden pagada {order_id}")
            print(f"   💰 Total: {total_price}")
            print(f"   📧 Cliente: {customer_email}")
            
            # Aquí puedes agregar tu lógica de negocio:
            # - Actualizar inventario
            # - Enviar confirmación por email
            # - Crear registros en otras tablas
            # - Integrar con sistemas de envío
            # etc.
            
            return True
            
        except Exception as e:
            print(f"❌ Error procesando orden pagada: {e}")
            return False


@method_decorator(csrf_exempt, name='dispatch')
class ShopifyGeneralWebhookView(View):
    """
    Webhook general para otros eventos de Shopify
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Obtener el topic del header si está disponible
            topic = request.META.get('HTTP_X_SHOPIFY_TOPIC', 'unknown')
            
            print(f"🛒 [Shopify Webhook] Topic: {topic}")
            print(f"📦 Datos recibidos: {list(data.keys()) if data else 'Sin datos'}")
            
            return JsonResponse({
                'success': True,
                'message': f'Webhook {topic} procesado',
                'topic': topic
            })
            
        except Exception as e:
            print(f"❌ Error en webhook general de Shopify: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
