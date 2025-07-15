#!/usr/bin/env python
"""
Script para verificar y actualizar la etiqueta de la orden 6576332275934
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'integracion'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
django.setup()

from izipay.models import PaymentTransaction, IzipayCredential
from shopify.models import ShopifyCredential
import requests
import json
from datetime import datetime

def buscar_transaccion(order_id):
    """Buscar transacción por orden ID"""
    try:
        # Buscar por shopify_order_id
        transaction = PaymentTransaction.objects.get(shopify_order_id=str(order_id))
        return transaction
    except PaymentTransaction.DoesNotExist:
        try:
            # Buscar por order_number
            transaction = PaymentTransaction.objects.get(order_number=str(order_id))
            return transaction
        except PaymentTransaction.DoesNotExist:
            print(f"❌ No se encontró transacción para la orden {order_id}")
            return None

def obtener_etiqueta_por_estado_izipay(estado_izipay):
    """Mapea el estado numérico de Izipay a una etiqueta descriptiva"""
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

def consultar_estado_actual_izipay(payment_link_id):
    """Consultar el estado actual en Izipay"""
    try:
        credential = IzipayCredential.objects.filter(is_active=True).first()
        if not credential:
            print("❌ No hay credenciales de Izipay activas")
            return None
        
        # Generar token temporal
        from datetime import datetime
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
            print(f"❌ Error generando token: {token_data.get('message', 'Error desconocido')}")
            return None
        
        session_token = token_data.get('response', {}).get('token')
        
        # Consultar estado del payment link
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
            return search_data.get('response', {})
        else:
            print(f"❌ Error consultando Payment Link: {search_data.get('message', 'Error desconocido')}")
            return None
            
    except Exception as e:
        print(f"❌ Error consultando Izipay: {e}")
        return None

def actualizar_etiqueta_shopify(order_id, nueva_etiqueta, transaction=None):
    """Actualizar etiqueta en Shopify y agregar comentario con info del pago"""
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
        
        # Obtener datos actuales de la orden
        order_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
        order_response = requests.get(order_url, headers=headers, timeout=30)
        
        if order_response.status_code != 200:
            print(f"❌ Error obteniendo orden: {order_response.status_code}")
            return False
        
        order_data = order_response.json().get('order', {})
        
        # Limpiar etiquetas de estado previas
        tags_actuales = order_data.get('tags', '')
        etiquetas_estado = ['pagada', 'no-pagada', 'pendiente', 'cancelada', 'izipay-paid', 'graphql-fallback']
        tags_limpiados = tags_actuales
        
        for etiqueta in etiquetas_estado:
            tags_limpiados = tags_limpiados.replace(f',{etiqueta}', '').replace(etiqueta, '')
        
        # Limpiar comas duplicadas o iniciales
        tags_limpiados = tags_limpiados.strip(',').replace(',,', ',')
        
        # Agregar nueva etiqueta de estado
        if tags_limpiados:
            nuevas_tags = f"{tags_limpiados},{nueva_etiqueta}"
        else:
            nuevas_tags = nueva_etiqueta
        
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
            print(f"✅ Etiqueta actualizada: '{nueva_etiqueta}' para orden {order_id}")
            print(f"🏷️  Tags antes: '{tags_actuales}'")
            print(f"🏷️  Tags después: '{nuevas_tags}'")
            
            # Agregar comentario con información del pago si está pagada
            if nueva_etiqueta == 'pagada' and transaction:
                agregar_comentario_pago(order_id, transaction, headers, store_url)
            
            return True
        else:
            print(f"❌ Error actualizando etiqueta: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error actualizando etiqueta Shopify: {e}")
        return False

def agregar_comentario_pago(order_id, transaction, headers, store_url):
    """Agregar comentario en la cronología de la orden con info del pago"""
    try:
        # Crear mensaje del comentario
        estado_display = transaction.get_payment_link_state_display()
        monto = transaction.amount
        moneda = transaction.currency
        fecha_creacion = transaction.created_at.strftime("%d/%m/%Y %H:%M")
        
        mensaje = f"""✅ PAGO CONFIRMADO VÍA IZIPAY
        
Cliente ya realizó el pago de {monto} {moneda}.

📊 Detalles del pago:
• Estado: {estado_display}
• Monto: {monto} {moneda}
• Fecha: {fecha_creacion}
• Transaction ID: {transaction.transaction_id}

🔗 Link de pago para verificación:
{transaction.payment_link_url}

ℹ️ El sistema Izipay confirma que este pago ha sido procesado exitosamente."""
        
        # Crear nota/comentario en la orden
        note_data = {
            "note": {
                "body": mensaje,
                "author": "Sistema Izipay",
                "created_at": datetime.now().isoformat()
            }
        }
        
        # URL para agregar nota a la orden
        notes_url = f"{store_url}/admin/api/2023-10/orders/{order_id}/events.json"
        
        # Crear evento de nota
        event_data = {
            "event": {
                "subject_id": order_id,
                "subject_type": "Order",
                "verb": "commented",
                "body": mensaje,
                "author": "Sistema Izipay"
            }
        }
        
        # Intentar agregar como nota primero
        try:
            from datetime import datetime
            
            # Usar el endpoint de notes si está disponible
            order_notes_url = f"{store_url}/admin/api/2023-10/orders/{order_id}.json"
            
            # Obtener la orden actual
            order_response = requests.get(order_notes_url, headers=headers, timeout=30)
            if order_response.status_code == 200:
                order_current = order_response.json().get('order', {})
                current_note = order_current.get('note', '')
                
                # Agregar nuestro mensaje a las notas existentes
                if current_note:
                    nueva_nota = f"{current_note}\n\n---\n\n{mensaje}"
                else:
                    nueva_nota = mensaje
                
                # Actualizar la orden con la nueva nota
                update_with_note = {
                    'order': {
                        'id': order_id,
                        'note': nueva_nota
                    }
                }
                
                note_response = requests.put(order_notes_url, json=update_with_note, headers=headers, timeout=30)
                
                if note_response.status_code == 200:
                    print(f"💬 Comentario agregado exitosamente a la orden {order_id}")
                    return True
                else:
                    print(f"⚠️ Error agregando comentario: {note_response.status_code}")
                    print(f"   Response: {note_response.text}")
                    return False
            
        except Exception as e:
            print(f"⚠️ Error agregando comentario: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error en agregar_comentario_pago: {e}")
        return False

def main():
    order_id = "6576332275934"
    
    print(f"🔍 === VERIFICANDO ORDEN {order_id} ===")
    
    # 1. Buscar transacción en BD
    transaction = buscar_transaccion(order_id)
    if not transaction:
        print("❌ No se puede continuar sin transacción")
        return
    
    print(f"✅ Transacción encontrada:")
    print(f"   Transaction ID: {transaction.transaction_id}")
    print(f"   Shopify Order ID: {transaction.shopify_order_id}")
    print(f"   Payment Link ID: {transaction.payment_link_id}")
    print(f"   Estado BD actual: {transaction.payment_link_state}")
    print(f"   Estado display: {transaction.get_payment_link_state_display()}")
    print(f"   Amount: {transaction.amount}")
    print(f"   Customer: {transaction.customer_email}")
    print(f"   Created: {transaction.created_at}")
    
    # 2. Consultar estado actual en Izipay
    print(f"\n🔍 Consultando estado actual en Izipay...")
    estado_izipay = consultar_estado_actual_izipay(transaction.payment_link_id)
    
    if estado_izipay:
        estado_actual = estado_izipay.get('state')
        print(f"📊 Estado actual en Izipay: {estado_actual}")
        print(f"📊 Info completa: {json.dumps(estado_izipay, indent=2)}")
        
        # Actualizar BD si es diferente
        if estado_actual != transaction.payment_link_state:
            print(f"🔄 Actualizando estado en BD: {transaction.payment_link_state} -> {estado_actual}")
            transaction.payment_link_state = estado_actual
            transaction.save()
        
        # 3. Determinar etiqueta correcta
        etiqueta_correcta = obtener_etiqueta_por_estado_izipay(estado_actual)
        
        # 4. Actualizar etiqueta en Shopify
        print(f"\n🏷️  Actualizando etiqueta en Shopify...")
        if actualizar_etiqueta_shopify(order_id, etiqueta_correcta, transaction):
            print(f"✅ Proceso completado exitosamente")
        else:
            print(f"❌ Error actualizando Shopify")
    else:
        # Usar estado de BD como fallback
        print(f"⚠️ No se pudo consultar Izipay, usando estado de BD")
        etiqueta_correcta = obtener_etiqueta_por_estado_izipay(transaction.payment_link_state)
        
        print(f"\n🏷️  Actualizando etiqueta en Shopify (fallback)...")
        if actualizar_etiqueta_shopify(order_id, etiqueta_correcta, transaction):
            print(f"✅ Proceso completado con fallback")
        else:
            print(f"❌ Error actualizando Shopify")

if __name__ == "__main__":
    main()
