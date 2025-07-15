from django.core.management.base import BaseCommand
from izipay.models import PaymentTransaction
from izipay.views import PaymentLinkSearchView
from django.utils import timezone

class Command(BaseCommand):
    help = 'Verificar estados de Payment Links pendientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--transaction-id',
            type=str,
            help='Verificar una transacción específica por ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Verificar todas las transacciones pendientes',
        )

    def handle(self, *args, **options):
        if options.get('transaction_id'):
            # Verificar transacción específica
            try:
                transaction = PaymentTransaction.objects.get(transaction_id=options['transaction_id'])
                self.verify_transaction(transaction)
            except PaymentTransaction.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ Transacción {options['transaction_id']} no encontrada")
                )
        elif options.get('all'):
            # Verificar todas las transacciones pendientes
            pending_transactions = PaymentTransaction.objects.filter(
                payment_link_state__in=['1', '4']  # GENERADO o TERMINADO_ERROR
            )
            
            self.stdout.write(f"🔍 Verificando {pending_transactions.count()} transacciones pendientes...")
            
            for transaction in pending_transactions:
                self.verify_transaction(transaction)
        else:
            # Verificar solo transacciones de las últimas 24 horas
            yesterday = timezone.now() - timezone.timedelta(days=1)
            recent_transactions = PaymentTransaction.objects.filter(
                created_at__gte=yesterday,
                payment_link_state__in=['1', '4']
            )
            
            self.stdout.write(f"🔍 Verificando {recent_transactions.count()} transacciones recientes...")
            
            for transaction in recent_transactions:
                self.verify_transaction(transaction)
        
        self.stdout.write(
            self.style.SUCCESS("✅ Verificación completada")
        )

    def verify_transaction(self, transaction):
        """
        Verificar el estado de una transacción específica
        """
        try:
            self.stdout.write(f"🔍 Verificando transacción {transaction.transaction_id}...")
            
            # Simular request para búsqueda
            class MockRequest:
                def __init__(self, data):
                    self.body = data
                    self.content_type = 'application/json'
            
            import json
            mock_request = MockRequest(json.dumps({
                'paymentLinkId': transaction.payment_link_id
            }).encode())
            
            search_view = PaymentLinkSearchView()
            result = search_view.post(mock_request)
            
            if result.status_code == 200:
                response_data = json.loads(result.content)
                if response_data.get('success'):
                    transaction_data = response_data.get('transaction', {})
                    state_display = transaction_data.get('payment_link_state_display', 'Desconocido')
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Transacción {transaction.transaction_id}: {state_display}"
                        )
                    )
                    
                    if transaction.shopify_order_id:
                        self.stdout.write(f"   📦 Orden Shopify: {transaction.shopify_order_id}")
                    
                    if transaction_data.get('is_successful'):
                        self.stdout.write(
                            self.style.SUCCESS("   💰 Estado: PAGADO")
                        )
                    elif transaction_data.get('is_failed'):
                        self.stdout.write(
                            self.style.WARNING("   ❌ Estado: FALLIDO")
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error verificando {transaction.transaction_id}: {response_data.get('error')}")
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error HTTP {result.status_code} verificando {transaction.transaction_id}")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {e}")
            )
