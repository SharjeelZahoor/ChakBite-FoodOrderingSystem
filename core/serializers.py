from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Pizza, Topping, Cart, CartItem, Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        read_only_fields = ('id',)

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'phone', 'address')
        read_only_fields = ('id',)

class ToppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topping
        fields = ('id', 'name', 'price', 'available')
        read_only_fields = ('id',)

class PizzaSerializer(serializers.ModelSerializer):
    toppings = ToppingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Pizza
        fields = ('id', 'name', 'description', 'image', 'small_price', 
                 'medium_price', 'large_price', 'available', 'toppings')
        read_only_fields = ('id',)

class CartItemSerializer(serializers.ModelSerializer):
    pizza = PizzaSerializer(read_only=True)
    toppings = ToppingSerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ('id', 'pizza', 'size', 'toppings', 'quantity', 'notes', 'price')
        read_only_fields = ('id',)
    
    def get_price(self, obj):
        return obj.get_price()

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ('id', 'user', 'created_at', 'updated_at', 'active', 'items', 'total_price')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def get_total_price(self, obj):
        return sum(item.get_price() for item in obj.items.all())

class OrderItemSerializer(serializers.ModelSerializer):
    pizza = PizzaSerializer(read_only=True)
    toppings = ToppingSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ('id', 'pizza', 'size', 'toppings', 'quantity', 'price')
        read_only_fields = ('id',)

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'user', 'order_type', 'status', 'delivery_address', 
                 'delivery_fee', 'estimated_delivery_time', 'payment_method', 
                 'total_amount', 'created_at', 'updated_at', 'notes', 'items')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')