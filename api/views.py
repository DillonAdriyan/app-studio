from django.shortcuts import render
from rest_framework import generics
from rest_framework.generics import CreateAPIView
from rest_framework import status
from rest_framework.response import Response

from store.models import Product
from store.serializers import ProductSerializer


# Create your views here.
class ProductListAPIView(generics.ListCreateAPIView):
 queryset = Product.objects.all()
 serializer_class = ProductSerializer
 
 def get(self, request, *args, **kwargs):
        return super().get(request, *args,
        **kwargs)