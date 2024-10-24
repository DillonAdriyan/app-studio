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
from django.core.paginator import Paginator
from weasyprint import HTML
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse, JsonResponse
import os
from django.conf import settings
from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from decimal import Decimal
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
import requests
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

class FacebookProfileView(APIView):
    def get(self, request, *args, **kwargs):
        access_token = settings.INSTAGRAM_ACCESS_TOKEN  # Your Facebook token with public_profile scope

        url = "https://graph.facebook.com/me"
        params = {
            'fields': 'id,name,picture',  # Requesting basic fields
            'access_token': access_token
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return Response(data)
        else:
            return Response({'error': 'Failed to retrieve data', 'details': response.json()}, status=response.status_code)
            
class InstagramDataView(APIView):
    permission_classes = [IsAuthenticated]  # Sesuaikan izin jika perlu
  
    def get(self, request, *args, **kwargs):
        access_token = settings.INSTAGRAM_ACCESS_TOKEN

        url = "https://graph.instagram.com/me"
        params = {
            'fields': 'id,username,followers_count,follows_count',
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        print(response.status_code)
        print(response.text)  # Menampilkan respons dari API Instagram
        if response.status_code == 200:
            data = response.json()
            return Response(data)
        else:
            return Response({'error': 'Failed to retrieve data'}, status=400)
            



def homepage(request):
    products = Product.objects.filter(is_active=True).annotate(
        average_rating=Avg('ratings__score')
    )
    categories = Category.objects.all()

    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    paginator = Paginator(products, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Cek apakah ini request AJAX untuk kategori
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Mengembalikan data produk sebagai JSON
        products_list = [
            {
                'id': product.id,
                'name': product.name,
                'image': product.image.url,
                'price': product.price
            }
            for product in page_obj
        ]
        return JsonResponse({'products': products_list})

    return render(request, 'homepage.html', {
        'products': products,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id
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






def generate_invoice(order):
    # Buat path untuk menyimpan invoice
    invoice_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
    
    # Cek apakah folder 'invoices' sudah ada, jika belum, buat folder tersebut
    if not os.path.exists(invoice_dir):
        os.makedirs(invoice_dir)

    # Buat nama file invoice berdasarkan nomor pesanan
    invoice_filename = f'invoice_{order.id}.pdf'
    invoice_filepath = os.path.join(invoice_dir, invoice_filename)

    # Ambil data pesanan yang diperlukan untuk invoice
    items = order.items.all()
    total_price = sum(item.get_total_price() for item in items)
    tax_rate = Decimal('0.10')
    disc_rate = Decimal('0.05')
    tax = total_price * tax_rate
    discount = disc_rate * total_price  # Contoh diskon 5%
    grand_total = total_price + tax - discount

    # Render template HTML ke string
    html_string = render_to_string('store/invoice_template.html', {
        'order': order,
        'items': items,
        'total_price': total_price,
        'tax': tax,
        'discount': discount,
        'grand_total': grand_total,
        'company': {
            'name': 'Sempurna, Inc.',
            'address': '270 5th Avenue, New Road, Jakarta City',
            'phone': '+62 123 4567'
        }
    })

    # Debug: Cek apakah HTML string sudah ter-render dengan benar
    # Tambahkan ini untuk memeriksa apakah ada kesalahan dalam rendering
    print(html_string)  # Ini akan mencetak HTML ke konsol, bisa dihapus setelah debugging

    # Konversi HTML menjadi PDF menggunakan WeasyPrint
    try:
        HTML(string=html_string).write_pdf(invoice_filepath)
    except Exception as e:
        print(f"Error generating PDF: {e}")  # Debugging error jika konversi gagal
        return None

    # Return path relative ke MEDIA_URL untuk diakses di template
    return os.path.join('invoices', invoice_filename)


    
 








@method_decorator(login_required, name='dispatch')
class CheckOut(View):
    def post(self, request):
        user = request.user

        # Prefetch items dan select product dalam satu query
        cart = Cart.objects.prefetch_related('items__product').filter(customer=user).first()

        if not cart or not cart.items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        # Periksa stok sekaligus tanpa looping
        out_of_stock_items = [
            cart_item for cart_item in cart.items.all()
            if cart_item.quantity > cart_item.product.stock
        ]
        if out_of_stock_items:
            messages.error(request, f"Not enough stock for {out_of_stock_items[0].product.name}.")
            return redirect('cart')

        try:
            # Gunakan transaksi agar jika terjadi kesalahan, semua perubahan di-rollback
            with transaction.atomic():
                # Buat pesanan
                order = Order.objects.create(customer=user)

                # Buat item pesanan dari item keranjang
                order_items = []
                for cart_item in cart.items.all():
                    order_items.append(OrderItem(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    ))

                    # Kurangi stok tanpa save per item
                    cart_item.product.stock = F('stock') - cart_item.quantity

                # Simpan semua OrderItem sekaligus
                OrderItem.objects.bulk_create(order_items)

                # Simpan produk yang stoknya telah diperbarui
                Product.objects.bulk_update(
                    [cart_item.product for cart_item in cart.items.all()], ['stock']
                )

                # Perbarui total harga untuk pesanan
                order.update_total_price()

                # Generate invoice
                invoice_filename = generate_invoice(order)

                # Tambahkan invoice ke dalam model Order
                order.invoice = invoice_filename
                order.save()

                # Kosongkan keranjang dalam satu query
                cart.items.all().delete()

            messages.success(request, "Your order has been placed successfully.")
        except Exception as e:
            print(e)
            messages.error(request, "There was an error processing your order.")
            return redirect('cart')

        return redirect('orders')






def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    invoice_filepath = os.path.join(settings.MEDIA_ROOT, order.invoice)

    # Pastikan file invoice ada
    if not os.path.exists(invoice_filepath):
        messages.error(request, "Invoice not found.")
        return redirect('orders')

    # Kembalikan file PDF sebagai respons
    return FileResponse(open(invoice_filepath, 'rb'), content_type='application/pdf')
    




    




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
    
    
def product_detail(request, product_id):
 product = get_object_or_404(Product, id=product_id)
 
 return render(request,
 'store/detail/product.html', context = {
  'product':product
 })