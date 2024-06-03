from django.urls import path
from .views import login, logout, homepage, signup, CheckOut, OrderView, store, add_to_cart, cart, add_quantity, remove_quantity
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', homepage, name='homepage'),
    path('store', store, name='store'),
    path('signup', signup, name='signup'),
    path('login', login, name='login'),
    path('logout', logout, name='logout'),
    path('check-out', CheckOut.as_view(), name='checkout'),
    path('orders', OrderView.as_view(), name='orders'),
    path('orders/<int:product_id>/', add_to_cart , name='addCart'),
    path('cart/', cart , name='cart'),
    path('cart/add_quantity/<int:cart_id>/', add_quantity , name='add_quantity'),
    path('cart/remove_quantity/<int:cart_id>/', remove_quantity , name='remove_quantity'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
