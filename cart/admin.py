from django.contrib import admin
from .models import Products, Category, Order, Cart, Profile
# Register your models here.

admin.site.register(Products)
admin.site.register(Order)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(Profile)