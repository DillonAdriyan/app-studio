# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import os
import hashlib
from django.utils.timezone import now

# def hashed_upload(instance, filename):
#     # Ambil ekstensi file asli
#     ext = filename.split('.')[-1]
    
#     # Buat hash berdasarkan timestamp dan nama file asli
#     hash_value = hashlib.md5(f"{filename}{now()}".encode('utf-8')).hexdigest()[:10]

#     # Tentukan nama file baru dengan hash
#     filename = f"{hash_value}.{ext}"

#     # Tentukan path folder tempat file akan disimpan
#     return os.path.join('products/', filename)
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO


def compress_image(image, max_size_kb=500):
    # Open the image file
    img = Image.open(image)
    
    # Initial size
    img_format = img.format
    
    # Start with a high and low range for quality
    low, high = 10, 90
    best_quality = high
    img_io = None

    # Use binary search to find the best quality
    while low <= high:
        mid_quality = (low + high) // 2

        # Create a BytesIO object to save the compressed image
        img_io = BytesIO()
        img.save(img_io, format=img_format, quality=mid_quality)
        img_io.seek(0)
        
        # Check the size of the image
        size_kb = img_io.getbuffer().nbytes / 1024

        if size_kb <= max_size_kb:
            best_quality = mid_quality
            high = mid_quality - 1  # Try a lower quality
        else:
            low = mid_quality + 1  # Increase quality to reduce size

    # Save the final image with the best found quality
    img_io = BytesIO()
    img.save(img_io, format=img_format, quality=best_quality)
    img_io.seek(0)
    
    # Return the compressed image
    return ContentFile(img_io.getvalue(), name=image.name)



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.user.username

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=60)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_active_products(cls):
        return cls.objects.filter(is_active=True)

    @classmethod
    def get_products_by_category(cls, category_id):
        return cls.objects.filter(category_id=category_id, is_active=True)
    def save(self, *args, **kwargs):
        if self.image:
            # Compress the image
            self.image = compress_image(self.image)
            # Generate a unique filename using hashlib
            unique_filename = hashlib.md5(self.image.read()).hexdigest()[:10] + os.path.splitext(self.image.name)[-1]
            self.image.name = unique_filename
            
        super().save(*args, **kwargs)

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled')
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    invoice = models.CharField(max_length=255, blank=True, null=True)  # Field baru untuk menyimpan invoice path

    def __str__(self):
        return f"Order {self.id} by {self.customer.username}"
    def update_total_price(self):
        self.total_price = sum(item.get_total_price() for item in self.items.all())
        self.save()
    
        
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Tambahkan ini

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"

    def get_total_price(self):
        return self.quantity * self.price  # Gunakan atribut price





class Cart(models.Model):
    customer = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.customer.username}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())
        
        
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart}"

    def get_total_price(self):
        return self.quantity * self.product.price



class Wishlist(models.Model):
    customer = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name='wishlists')

    def __str__(self):
        return f"Wishlist for {self.customer.username}"
        

class Rating(models.Model):
    product = models.ForeignKey(Product, related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating from 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # Ensure one rating per user per product

    def __str__(self):
        return f"{self.user.username} rated {self.product.name} with {self.score}"
        