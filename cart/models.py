from django.db import models
from django.contrib.auth.models import User
import datetime 

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.user.username

class Category(models.Model): 
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    @staticmethod
    def get_all_categories(): 
        return Category.objects.all() 

    def __str__(self): 
        return self.name

class Products(models.Model): 
    name = models.CharField(max_length=60) 
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1) 
    description = models.TextField(blank=True, null=True)
    stock = models.IntegerField(blank=True, null=True, default=1)
    image = models.ImageField(upload_to='uploads/products/')

    @staticmethod
    def get_products_by_id(ids):
        return Products.objects.filter(id__in=ids)

    @staticmethod
    def get_all_products():
        return Products.objects.all()

    @staticmethod
    def get_all_products_by_categoryid(category_id):
        if category_id:
            return Products.objects.filter(category=category_id)
        else:
            return Products.get_all_products()
    
    def __str__(self):
        return self.name

class Order(models.Model): 
    product = models.ForeignKey(Products, on_delete=models.CASCADE) 
    customer = models.ForeignKey(User, on_delete=models.CASCADE) 
    quantity = models.IntegerField(default=1) 
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    address = models.CharField(max_length=255, default='', blank=True) 
    phone = models.CharField(max_length=15, default='', blank=True) 
    date = models.DateField(default=datetime.datetime.today) 
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered')], default='Pending') 
    
    def placeOrder(self):
        self.save()

    def total_orders(self):
        return self.quantity * self.price
     
    @staticmethod
    def get_orders_by_user(user_id):
        return Order.objects.filter(customer=user_id).order_by('-date')
    
    def __str__(self):
        return f"Order {self.id} by {self.customer.username}"

class Cart(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def add_quantity(self):
        self.quantity += 1
        self.save()

    def remove_quantity(self):
        if self.quantity > 1:
            self.quantity -= 1
            self.save()
        else:
            self.delete()
             
    @classmethod
    def total_items(cls, customer):
        return cls.objects.filter(customer=customer).aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0
    @classmethod
    def total_product(cls, customer):
     return cls.objects.filter(customer=customer).values('product').distinct().count()
    
    @classmethod
    def total_price(cls, customer):
        cart_items = cls.objects.filter(customer=customer)
        return sum(item.product.price * item.quantity for item in cart_items)
        
        
    def get_total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
