from django.contrib import admin
from .models import UserProfile, Pizza, Topping, Cart, CartItem, Order, OrderItem

admin.site.register(UserProfile)
admin.site.register(Pizza)
admin.site.register(Topping)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)