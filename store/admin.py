from django.contrib import admin
from .models import Product, Category, Order, Cart, Profile, CartItem
# Register your models here.

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Profile)