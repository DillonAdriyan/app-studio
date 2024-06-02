from django.urls import path
from .views import login, logout, homepage, signup, CheckOut, OrderView, store
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
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
