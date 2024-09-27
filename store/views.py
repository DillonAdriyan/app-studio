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
from weasyprint import HTML
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
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

    # Konversi HTML menjadi PDF menggunakan WeasyPrint
    HTML(string=html_string).write_pdf(invoice_filepath)

    # Return path relative ke MEDIA_URL untuk diakses di template
    return os.path.join('invoices', invoice_filename)
    
 


def generate_invoice2(order):
    # Buat path untuk menyimpan invoice
    invoice_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
    
    # Cek apakah folder 'invoices' sudah ada, jika belum, buat folder tersebut
    if not os.path.exists(invoice_dir):
        os.makedirs(invoice_dir)
    
    # Buat nama file invoice berdasarkan nomor pesanan
    invoice_filename = f'invoice_{order.id}.pdf'
    invoice_filepath = os.path.join(invoice_dir, invoice_filename)

    # Buat PDF
    pdf = SimpleDocTemplate(invoice_filepath, pagesize=A4)
    width, height = A4
    elements = []
    
    # Stylesheet untuk paragraph
    styles = getSampleStyleSheet()
    centered = styles["Title"]
    centered.alignment = TA_CENTER
    normal_left = styles["Normal"]
    normal_left.alignment = TA_LEFT
    bold_style = styles["Heading2"]
    bold_style.alignment = TA_LEFT

    # Header Perusahaan
    elements.append(Paragraph("SEMPURNA, INC.", bold_style))
    elements.append(Paragraph("Design Studio", normal_left))
    elements.append(Paragraph("Sempurna Inc, 10 January 2018", normal_left))
    elements.append(Spacer(1, 12))
    
    # Detail Invoice dan Customer
    elements.append(Paragraph(f"Invoice Number: {order.id}", normal_left))
    elements.append(Paragraph(f"Date: {order.created_at.strftime('%Y-%m-%d')}", normal_left))
    elements.append(Spacer(1, 12))

    # Tabel Pesanan
    data = [["NO", "ITEM DESCRIPTION", "PRICE", "QTY", "TOTAL"]]

    total_price = Decimal(0)  # Menggunakan Decimal
    for idx, item in enumerate(order.items.all(), start=1):
        total_item_price = item.get_total_price()
        data.append([str(idx), item.product.name, f"${item.price:.2f}", str(item.quantity), f"${total_item_price:.2f}"])
        total_price += total_item_price

    # Menggunakan Decimal untuk perhitungan pajak dan total
    tax_rate = Decimal('0.15')  # Pajak 15%
    tax_amount = total_price * tax_rate
    grand_total = total_price + tax_amount

    # Tambahkan total ke dalam tabel
    data.append(["", "", "", "Sub Total:", f"${total_price:.2f}"])
    data.append(["", "", "", "Tax (15%):", f"${tax_amount:.2f}"])
    data.append(["", "", "", "Grand Total:", f"${grand_total:.2f}"])

    # Gaya untuk tabel
    table = Table(data, colWidths=[0.5 * inch, 2 * inch, 1.5 * inch, 1 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.red),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)

    # Spacer untuk memberi jarak sebelum menambahkan detail akhir
    elements.append(Spacer(1, 24))

    # Footer: Terms & Conditions dan Payment Method
    elements.append(Paragraph("Payment Method:", bold_style))
    elements.append(Paragraph("Bank Account: 123456789", normal_left))
    elements.append(Paragraph("Bank Code: 001", normal_left))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Terms & Conditions:", bold_style))
    elements.append(Paragraph("Lorem ipsum dolor sit amet, consectetur adipiscing elit.", normal_left))

    # Tanda tangan
    elements.append(Spacer(1, 48))
    elements.append(Paragraph("____________________", normal_left))
    elements.append(Paragraph("Steven Joe", normal_left))
    elements.append(Paragraph("Accounting Manager", normal_left))

    # Simpan PDF
    pdf.build(elements)

    # Return path relative ke MEDIA_URL untuk diakses di template
    return os.path.join('invoices', invoice_filename)







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

        # Buat pesanan
        order = Order.objects.create(customer=user)

        # Buat item pesanan dari item keranjang
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

            # Kurangi stok
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save()

        # Perbarui total harga untuk pesanan
        order.update_total_price()

        # Generate invoice
        invoice_filename = generate_invoice(order)

        # Tambahkan invoice ke dalam model Order (opsional, jika mau disimpan di DB)
        order.invoice = invoice_filename
        order.save()

        # Kosongkan keranjang
        cart.items.all().delete()

        messages.success(request, "Your order has been placed successfully.")
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