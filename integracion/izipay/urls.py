from django.urls import path
from .views import GenerateTokenView

app_name = 'izipay'

urlpatterns = [
    path('generate-token/', GenerateTokenView.as_view(), name='generate_token'),
]