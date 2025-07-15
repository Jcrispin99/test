from django.urls import path
from .views import IzipayPaymentLinkView, IzipayTestView

app_name = 'izipay'

urlpatterns = [
    path('payment-link/', IzipayPaymentLinkView.as_view(), name='izipay_payment_link'),
    path('process/', IzipayTestView.as_view(), name='izipay_test'),
]