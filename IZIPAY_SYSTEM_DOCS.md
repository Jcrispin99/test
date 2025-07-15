# Sistema de Transacciones Izipay - Shopify

## Resumen

Este sistema implementa una **tabla pivote** que relaciona las transacciones de **Izipay** con las órdenes de **Shopify**, permitiendo el seguimiento automático del estado de los pagos y la actualización de órdenes.

## Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django API    │    │   Izipay API    │
│ (izipay-handler)│◄──►│                 │◄──►│                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ PaymentTransaction│
                       │ (Tabla Pivote)   │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Shopify API    │
                       │ (actualización) │
                       └─────────────────┘
```

## Modelo PaymentTransaction (Tabla Pivote)

### Campos Principales:
- `transaction_id`: ID único de Izipay
- `shopify_order_id`: ID de la orden en Shopify
- `payment_link_id`: ID del Payment Link de Izipay
- `payment_link_state`: Estado del pago (1-6)
- `amount`, `currency`: Información financiera
- `customer_email`, `customer_name`: Datos del cliente

### Estados de Payment Link:
- `1`: GENERADO
- `3`: TERMINADO_EXITO (✅ Pagado)
- `4`: TERMINADO_ERROR
- `5`: EXPIRADO
- `6`: DESACTIVADO

## APIs Implementadas

### 1. Crear Payment Link
**POST** `/izipay/payment-link/`

```json
{
  "amount": 100.50,
  "orderNumber": "ORDER-123",
  "customerEmail": "cliente@email.com",
  "customerName": "Juan Pérez",
  "shopifyOrderId": "SHOPIFY-456",
  "billing": { "firstName": "Juan", ... },
  "shipping": { "firstName": "Juan", ... }
}
```

**Respuesta:**
```json
{
  "success": true,
  "paymentLink": "https://paymentlink.izipay.pe/pay/xyz",
  "paymentLinkId": "abc123",
  "transactionId": "100456"
}
```

### 2. Webhook de Notificaciones
**POST** `/izipay/webhook/`

```json
{
  "transactionId": "100456",
  "state": "3",
  "paymentLinkId": "abc123"
}
```

**Funcionalidad:**
- Actualiza el estado de la transacción
- Si `state = "3"` (TERMINADO_EXITO), actualiza orden Shopify a "pagada"

### 3. Consultar Payment Link
**POST** `/izipay/search/`

```json
{
  "paymentLinkId": "abc123"
}
```

**Respuesta:**
```json
{
  "success": true,
  "transaction": {
    "transaction_id": "100456",
    "shopify_order_id": "SHOPIFY-456",
    "payment_link_state": "3",
    "payment_link_state_display": "TERMINADO_EXITO",
    "is_successful": true
  },
  "izipay_data": { ... }
}
```

### 4. Listar Transacciones (Tabla Pivote)
**GET** `/izipay/transactions/`

**Filtros opcionales:**
- `?state=3`: Filtrar por estado
- `?shopify_order_id=SHOPIFY-456`: Filtrar por orden

## Comando de Gestión

```bash
# Verificar transacciones pendientes (últimas 24h)
python manage.py check_payment_states

# Verificar todas las transacciones pendientes
python manage.py check_payment_states --all

# Verificar transacción específica
python manage.py check_payment_states --transaction-id 100456
```

## Flujo de Trabajo

### 1. Crear Orden y Payment Link
```javascript
// Frontend (izipay-handler.js)
const orderData = {
  total: 150.00,
  orderNumber: "ORDER-789",
  shopifyOrderId: "SHOPIFY-999"
};

const result = await izipayHandler.createPaymentLink(orderData, billingData, shippingData);
// → Redirige al usuario al Payment Link
```

### 2. Usuario Realiza el Pago
- Usuario completa el pago en Izipay
- Izipay cambia el estado del Payment Link a "3" (TERMINADO_EXITO)

### 3. Notificación Automática (Webhook)
```python
# Django recibe webhook de Izipay
{
  "transactionId": "100789",
  "state": "3"  # TERMINADO_EXITO
}

# Sistema actualiza automáticamente:
transaction.payment_link_state = "3"
transaction.save()

# Si hay shopify_order_id, actualiza la orden:
update_shopify_order(transaction.shopify_order_id, 'paid')
```

### 4. Consulta de Estado
```python
# Consultar manualmente o por comando
transaction = PaymentTransaction.objects.get(transaction_id="100789")
print(f"Estado: {transaction.get_payment_link_state_display()}")
print(f"¿Pagado?: {transaction.is_successful}")
```

## Configuración de Webhook

En el panel de Izipay, configurar:
- **URL Webhook**: `https://tu-dominio.com/izipay/webhook/`
- **Eventos**: Cambios de estado de Payment Link

## Panel de Administración

Accesible en `/admin/izipay/paymenttransaction/`:
- Vista de todas las transacciones
- Filtros por estado, fecha, email
- Búsqueda por transaction_id, order_number, shopify_order_id
- Estados visuales (exitoso/fallido)

## Casos de Uso

### Ver todas las órdenes pagadas:
```python
paid_orders = PaymentTransaction.objects.filter(payment_link_state='3')
for order in paid_orders:
    print(f"Orden {order.shopify_order_id}: {order.amount} {order.currency}")
```

### Encontrar transacción por orden de Shopify:
```python
shopify_order = PaymentTransaction.objects.get(shopify_order_id="SHOPIFY-456")
print(f"Estado Izipay: {shopify_order.get_payment_link_state_display()}")
```

### Verificar órdenes pendientes:
```bash
python manage.py check_payment_states --all
```

## Beneficios del Sistema

✅ **Trazabilidad completa**: Relación directa Izipay ↔ Shopify  
✅ **Actualización automática**: Webhook actualiza estados en tiempo real  
✅ **Consulta flexible**: APIs para verificar estados manualmente  
✅ **Monitoreo**: Comando de gestión para verificaciones periódicas  
✅ **Admin panel**: Interfaz visual para gestión  
✅ **Robustez**: Manejo de errores y fallbacks  

## Próximos Pasos

1. **Integración Shopify**: Implementar actualización real de órdenes
2. **Notificaciones**: Email/SMS cuando el pago sea exitoso
3. **Dashboard**: Panel de control visual para transacciones
4. **Reportes**: Exportación de datos para análisis
5. **Testing**: Pruebas automatizadas del flujo completo
