from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .models import Product, Category, Order, OrderItem, Cart, CartItem, Wishlist, Rating
from django.db.models import Avg
from django.db.models import F
from django.contrib.auth.mixins import LoginRequiredMixin
def homepage(request):
    products = Product.objects.filter(is_active=True).annotate(
        average_rating=Avg('ratings__score')  # Calculate average rating
    )
    categories = Category.objects.all()
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    return render(request, 'homepage.html', {'products': products,
      'categories': categories,
    })



def store(request):
    products = Product.objects.filter(is_active=True).annotate(
        average_rating=Avg('ratings__score')  # Calculate average rating
    )
    categories = Category.objects.all()
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    return render(request, 'store/store.html', {
        'products': products,
        'categories': categories,
    })


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Account created successfully. Please log in.")
        return redirect('login')

    return render(request, 'auth/signup.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect('homepage')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'auth/login.html')

@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('homepage')



@method_decorator(login_required, name='dispatch')
class CheckOut(View):
    def post(self, request):
        user = request.user
        cart = Cart.objects.filter(customer=user).first()

        if not cart or not cart.items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        for cart_item in cart.items.all():
            if cart_item.quantity > cart_item.product.stock:
                messages.error(request, f"Not enough stock for {cart_item.product.name}.")
                return redirect('cart')

        # Create the order
        order = Order.objects.create(customer=user)

        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

            # Reduce stock
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save()

        # Update the total price for the order
        order.update_total_price()

        # Clear the cart
        cart.items.all().delete()

        messages.success(request, "Your order has been placed successfully.")
        return redirect('orders')






    




@method_decorator(login_required, name='dispatch')
class OrderView(View):
    def get(self, request):
        # Mengambil semua pesanan untuk pengguna yang sedang login
        orders = Order.objects.filter(customer=request.user).order_by('-created_at')
        return render(request, 'store/orders.html', {'orders': orders})




@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.stock < 1:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect('store')

    cart, created = Cart.objects.get_or_create(customer=request.user)
    cart_item, created = cart.items.get_or_create(product=product)
    
    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity = F('quantity') + 1
        else:
            messages.error(request, f"Cannot add more {product.name}. Only {product.stock} left in stock.")
            return redirect('cart')

    cart_item.save()
    messages.success(request, f"{product.name} has been added to your cart.")
    return redirect('store')



@login_required
def cart(request):
    # Mendapatkan keranjang untuk user yang sedang login
    cart = Cart.objects.filter(customer=request.user).first()
    
    if not cart:
        # Jika cart belum ada, kirimkan response bahwa keranjang kosong
        messages.info(request, "Your cart is empty.")
        return render(request, 'store/cart.html', {'cart': None})
    
    # Mengambil item yang ada di keranjang
    cart_items = cart.items.all()  # Gunakan related_name 'items' untuk mengambil CartItem
    
    return render(request, 'store/cart.html', {'cart': cart, 'cart_items': cart_items})




@login_required
def add_quantity(request, cart_id):
    cart_item = get_object_or_404(CartItem, id=cart_id, cart__customer=request.user)
    if cart_item.quantity < cart_item.product.stock:
        cart_item.quantity = F('quantity') + 1
        cart_item.save()
    else:
        messages.error(request, f"Cannot add more {cart_item.product.name}. Only {cart_item.product.stock} left in stock.")
    return redirect('cart')


@login_required
def remove_quantity(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__customer=request.user)

    if cart_item.quantity > 1:
        cart_item.quantity = F('quantity') - 1
        cart_item.save()
    else:
        cart_item.delete()

    messages.success(request, f"Quantity of {cart_item.product.name} decreased.")
    return redirect('cart')


@login_required
def wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(customer=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wishlist})
    
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(customer=request.user)

    if wishlist.products.filter(id=product.id).exists():
        messages.info(request, f"{product.name} is already in your wishlist.")
    else:
        wishlist.products.add(product)
        messages.success(request, f"{product.name} has been added to your wishlist.")

    return redirect('wishlist')
 
@login_required  # Ensure only logged-in users can rate products
def rate_product(request, product_id):
    if request.method == 'POST':
        score = request.POST.get('score')
        if score:
            product = get_object_or_404(Product, id=product_id)
            # Create or update the rating
            rating, created = Rating.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={'score': score}
            )
            return redirect('store')  # Redirect to the store after submitting the rating
    return redirect('store')