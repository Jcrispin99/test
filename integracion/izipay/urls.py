from django.urls import path
from .views import IzipayGenerateTokenView, IzipayTestView

app_name = 'izipay'

urlpatterns = [
    path('generate-token/', IzipayGenerateTokenView.as_view(), name='izipay_generate_token'),
    path('process/', IzipayTestView.as_view(), name='izipay_test'),
]