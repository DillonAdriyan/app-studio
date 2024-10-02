from django.urls import path
from .views import ProductListAPIView
urlpatterns = [
   path("product/", ProductListAPIView.as_view(), name="product")
 
 ]
 
