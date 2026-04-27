from django.urls import path
from .views import GenerateCodeView, RedeemCodeView

urlpatterns = [
    path('family-codes/generate/', GenerateCodeView.as_view(), name='generate-code'),
    path('family-codes/redeem/', RedeemCodeView.as_view(), name='redeem-code'),
]
