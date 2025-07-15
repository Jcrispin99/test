from django.urls import path
from .views import IzipayTestView

app_name = 'izipay'

urlpatterns = [
    path('process/', IzipayTestView.as_view(), name='test_process'),
]