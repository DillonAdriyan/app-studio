from django.shortcuts import render, redirect, HttpResponseRedirect 
from .models import Category, Products, Order, Cart
from django.views import View 
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

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




  
# Create your views here. 
class Index(View):
    def post(self, request):
        product_id = request.POST.get('product')
        remove = request.POST.get('remove')
        customer_id = request.session.get('customer')
        customer = Customer.objects.get(id=customer_id)

        cart_item, created = Cart.objects.get_or_create(customer=customer, product_id=product_id)
        if remove:
            cart_item.remove_quantity()
        else:
            cart_item.add_quantity()

        return redirect('homepage')

    def get(self, request):
        return HttpResponseRedirect(f'/store{request.get_full_path()[1:]}')

  
  
def store(request): 
    cart = request.session.get('cart') 
    if not cart: 
        request.session['cart'] = {} 
    products = None
    categories = Category.get_all_categories() 
    categoryID = request.GET.get('category') 
    if categoryID: 
        products = Products.get_all_products_by_categoryid(categoryID) 
    else: 
        products = Products.objects.all() 
  
    data = {} 
    data['products'] = products
    data['categories'] = categories 
  
    print('you are : ', request.session.get('email')) 
    return render(request, 'store/store.html', data) 
    
    
 # check out Viewfrom django.shortcuts import render, redirect
from django.utils.decorators import method_decorator

class CheckOut(View):
    @method_decorator(login_required)
    def post(self, request):
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        customer = request.user
        cart = request.session.get('cart')
        products = Products.get_products_by_id(list(cart.keys()))
        print(address, phone, customer, cart, products)

        for product in products:
            order = Order(customer=customer,
                          product=product,
                          price=product.price,
                          address=address,
                          phone=phone,
                          quantity=cart.get(str(product.id)))
            order.save()
            # Reduce stock
            product.stock -= cart.get(str(product.id))
            product.save()
        request.session['cart'] = {}

        return redirect('cart')


        
        
class OrderView(View):
    def get(self, request): 
        user = request.user
        orders = Order.get_orders_by_user(user.id)
        context = {'orders': orders}
        print(orders)
        return render(request, 'store/orders.html', context) 
        
        

from django.contrib.auth import authenticate, login as auth_login

def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')

        value = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'email': email
        }
        error_message = None

        if not first_name:
            error_message = "Please Enter your First Name !!"
        elif len(first_name) < 3:
            error_message = 'First Name must be 3 char long or more'
        elif not last_name:
            error_message = 'Please Enter your Last Name'
        elif len(last_name) < 3:
            error_message = 'Last Name must be 3 char long or more'
        elif not phone:
            error_message = 'Enter your Phone Number'
        elif len(phone) < 10:
            error_message = 'Phone Number must be 10 char Long'
        elif len(password) < 5:
            error_message = 'Password must be 5 char long'
        elif len(email) < 5:
            error_message = 'Email must be 5 char long'
        elif User.objects.filter(username=email).exists():
            error_message = 'Email Address Already Registered..'

        if not error_message:
            user = User(first_name=first_name,
                        last_name=last_name,
                        username=email,
                        email=email,
                        password=make_password(password))
            user.save()
            user = authenticate(request, username=email, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('homepage')
        else:
            return render(request, 'auth/signup.html', {'error': error_message, 'values': value})

    return render(request, 'auth/signup.html')


