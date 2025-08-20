from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pizzas', views.PizzaViewSet)
router.register(r'toppings', views.ToppingViewSet)
router.register(r'cart', views.CartViewSet, basename='cart')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    # Web URLs
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.orders, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # API URLs
    path('api/', include(router.urls)),
    path('api/register/', views.UserRegistrationView.as_view(), name='api_register'),
    path('api/login/', views.UserLoginView.as_view(), name='api_login'),
    path('api/logout/', views.UserLogoutView.as_view(), name='api_logout'),
    path('api/cart/count/', views.get_cart_count, name='get_cart_count'),
    path('api/update_profile/', views.update_profile, name='api_update_profile'),
    path('api/change_password/', views.change_password, name='api_change_password'),
]