from django.contrib import admin
from .models import Products, Category, Order
# Register your models here.

admin.site.register(Products)
admin.site.register(Order)
admin.site.register(Category)