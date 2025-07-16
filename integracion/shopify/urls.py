from django.urls import path
from .views import ShopifyOrderPaidWebhookView, ShopifyGeneralWebhookView

urlpatterns = [
    path('webhook/order-paid/', ShopifyOrderPaidWebhookView.as_view(), name='shopify_order_paid_webhook'),
    path('webhook/general/', ShopifyGeneralWebhookView.as_view(), name='shopify_general_webhook'),
]
