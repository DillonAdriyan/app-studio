from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.http import HttpResponse

from .models import Category, Products, Order, Cart
from .forms import UserRegisterForm


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('homepage')
        else:
            error_message = 'Invalid email or password'
            return render(request, 'auth/login.html', {'error': error_message})
    return render(request, 'auth/login.html')

def logout(request):
    auth_logout(request)
    return redirect('login')

@login_required
def homepage(request):
    return render(request, 'store/store.html')

class Index(View):
    def post(self, request):
        product_id = request.POST.get('product')
        remove = request.POST.get('remove')
        customer = request.user

        cart_item, created = Cart.objects.get_or_create(customer=customer, product_id=product_id)
        if remove:
            cart_item.remove_quantity()
        else:
            cart_item.add_quantity()

        return redirect('homepage')

    def get(self, request):
        return HttpResponseRedirect(f'/store{request.get_full_path()[1:]}')

def store(request):
    if not request.session.get('cart'):
        request.session['cart'] = {}
    
    categoryID = request.GET.get('category')
    products = Products.get_all_products_by_categoryid(categoryID) if categoryID else Products.get_all_products()
    
    data = {
        'products': products,
        'categories': Category.get_all_categories()
    }
  
    return render(request, 'store/store.html', data)

class CheckOut(View):
    @method_decorator(login_required)
    def post(self, request):
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        customer = request.user
        cart = request.session.get('cart')
        products = Products.get_products_by_id(list(cart.keys()))

        for product in products:
            order = Order(
                customer=customer,
                product=product,
                price=product.price,
                address=address,
                phone=phone,
                quantity=cart.get(str(product.id))
            )
            order.save()
            product.stock -= cart.get(str(product.id))
            product.save()
        
        request.session['cart'] = {}

        return redirect('cart')
        
        
        
        
def cart(request):
 user = request.user
 cart = Cart.objects.filter(customer=user)
 total_items = Cart.total_items(user)
 total_product = Cart.total_product(user)
 total_price = Cart.total_price(user)
 context = { 'carts' : cart,
 'user': user,
 'total_items': total_items,
 'total_product': total_product,
 'total_price': total_price
 }
 return render(request, 'store/cart.html', context)
 
def add_to_cart(request, product_id):
    product = get_object_or_404(Products, pk=product_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        customer = request.user
        cart_item, created = Cart.objects.get_or_create(customer=customer, product=product)
        if not created:
            # Jika item sudah ada di keranjang, tambahkan kuantitas baru ke kuantitas yang ada
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        return redirect('cart')
    
    context = {'products': product}
    return render(request, 'store/add_cart.html', context)



def add_quantity(request, cart_id):
    cart_item = Cart.objects.get(pk=cart_id)
    cart_item.add_quantity()
    return redirect('cart')

def remove_quantity(request, cart_id):
    cart_item = Cart.objects.get(pk=cart_id)
    cart_item.remove_quantity()
    return redirect('cart')


class OrderView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        orders = Order.get_orders_by_user(user.id)
        context = {'orders': orders}
        return render(request, 'store/orders.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from .forms import UserRegisterForm
from django.contrib.auth.models import User

def signup(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        error_message = None

        # Retrieve form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password1')

        value = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'email': email
        }

        # Custom validation logic
        if not first_name:
            error_message = "Please enter your first name!"
        elif len(first_name) < 3:
            error_message = 'First name must be 3 characters long or more.'
        elif not last_name:
            error_message = 'Please enter your last name.'
        elif len(last_name) < 3:
            error_message = 'Last name must be 3 characters long or more.'
        elif not phone:
            error_message = 'Enter your phone number.'
        elif len(phone) < 10:
            error_message = 'Phone number must be 10 characters long.'
        elif not password:
            error_message = 'Please enter a password.'
        elif len(password) < 5:
            error_message = 'Password must be 5 characters long.'
        elif not email:
            error_message = 'Please enter your email.'
        elif len(email) < 5:
            error_message = 'Email must be 5 characters long.'
        elif User.objects.filter(email=email).exists():
            error_message = 'Email address already registered.'

        # If no custom errors, validate the form
        if not error_message:
            if form.is_valid():
                user = form.save()
                user = authenticate(request, username=email, password=password)
                if user is not None:
                    auth_login(request, user)
                    return redirect('homepage')
                else:
                    error_message = 'Authentication failed'
            else:
                # Form validation errors
                for field, errors in form.errors.items():
                    error_message = f"{field}: {', '.join(errors)}"
                    break

        return render(request, 'auth/signup.html', {'form': form, 'error': error_message, 'values': value})

    else:
        form = UserRegisterForm()
        value = {
            'first_name': '',
            'last_name': '',
            'phone': '',
            'email': ''
        }

    return render(request, 'auth/signup.html', {'form': form, 'values': value})
