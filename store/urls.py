from django.urls import path
from .views import login, logout, homepage, signup, CheckOut, OrderView, store, add_to_cart, cart, add_quantity, remove_quantity, wishlist, add_to_wishlist,product_detail, rate_product, download_invoice, promo_detail
from django.conf.urls.static import static
from django.conf import settings
from .views import InstagramDataView

urlpatterns = [
    path('', homepage, name='homepage'),
    path('store/', store, name='store'),
    path('signup/', signup, name='signup'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('check-out/', CheckOut.as_view(), name='checkout'),
    path('orders/', OrderView.as_view(), name='orders'),
    path('orders/<int:product_id>/', add_to_cart , name='addCart'),
    path('cart/', cart , name='cart'),
    path('cart/add_quantity/<int:cart_id>/', add_quantity , name='add_quantity'),
    path('cart/remove_quantity/<int:cart_item_id>/', remove_quantity, name='remove_quantity'),
    path('wishlist/', wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('rate_product/<int:product_id>/', rate_product, name='rate_product'),  # Add this line
    path('download_invoice/<int:order_id>/', download_invoice, name='download_invoice'),
    path('product/<int:product_id>/', product_detail, name="product_detail"),
    
    # url api
    path('api/instagram-data/', InstagramDataView.as_view(), name='instagram-data'),
    path('promo/<int:promo_id>/', promo_detail, name='promo_detail'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
