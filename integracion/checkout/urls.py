from django.urls import path
from . import views

urlpatterns = [
    path('', views.checkout_page, name='checkout_page'),
    path('process/', views.process_checkout, name='process_checkout'),
]