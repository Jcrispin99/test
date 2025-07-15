from django.urls import path
from .views import IzipayPaymentLinkView, IzipayTestView, IzipayWebhookView, PaymentLinkSearchView, PaymentTransactionListView, TestGraphQLView

app_name = 'izipay'

urlpatterns = [
    path('payment-link/', IzipayPaymentLinkView.as_view(), name='izipay_payment_link'),
    path('webhook/', IzipayWebhookView.as_view(), name='izipay_webhook'),
    path('search/', PaymentLinkSearchView.as_view(), name='payment_link_search'),
    path('transactions/', PaymentTransactionListView.as_view(), name='payment_transactions'),
    path('process/', IzipayTestView.as_view(), name='izipay_test'),
    path('test-graphql/', TestGraphQLView.as_view(), name='test_graphql'),
]