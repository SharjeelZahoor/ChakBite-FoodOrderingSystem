from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile, Pizza, Topping, Cart, CartItem, Order, OrderItem
from .serializers import (
    UserSerializer, UserProfileSerializer, PizzaSerializer, ToppingSerializer,
    CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer
)
from django.db import models
from django.db.models import Q

# Web Views
def home(request):
    featured_pizzas = Pizza.objects.filter(available=True)[:3]
    return render(request, 'core/home.html', {'featured_pizzas': featured_pizzas})

def menu(request):
    search_query = request.GET.get('search', '')
    pizzas = Pizza.objects.filter(available=True)
    toppings = Topping.objects.filter(available=True)
    
    # Filter pizzas based on search query
    if search_query:
        pizzas = pizzas.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    return render(request, 'core/menu.html', {'pizzas': pizzas, 'toppings': toppings, 'search_query': search_query})

@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user, active=True)
    return render(request, 'core/cart.html', {'cart': cart})

@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user, active=True)
    if not cart.items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('cart')
    return render(request, 'core/checkout.html', {'cart': cart})

@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': user_orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/order_detail.html', {'order': order})

@login_required
def profile(request):
    return render(request, 'core/profile.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "core/login.html")

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()
        messages.success(request, "Account created successfully! Please login.")
        return redirect("login")
    return render(request, "core/register.html")

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('home')

# API Views
class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        phone = request.data.get('phone')
        address = request.data.get('address')
        
        if not username or not password or not email or not phone or not address:
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        UserProfile.objects.create(
            user=user,
            phone=phone,
            address=address
        )
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class PizzaViewSet(viewsets.ModelViewSet):
    queryset = Pizza.objects.all()
    serializer_class = PizzaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

class ToppingViewSet(viewsets.ModelViewSet):
    queryset = Topping.objects.all()
    serializer_class = ToppingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user, active=True)
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(
            user=self.request.user,
            active=True
        )
        return cart
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_object()
        pizza_id = request.data.get('pizza_id')
        size = request.data.get('size')
        quantity = request.data.get('quantity', 1)
        topping_ids = request.data.get('topping_ids', [])
        notes = request.data.get('notes', '')
        
        try:
            pizza = Pizza.objects.get(id=pizza_id)
        except Pizza.DoesNotExist:
            return Response({'error': 'Pizza not found'}, status=status.HTTP_404_NOT_FOUND)
        
        cart_item = CartItem.objects.create(
            cart=cart,
            pizza=pizza,
            size=size,
            quantity=quantity,
            notes=notes
        )
        
        if topping_ids:
            toppings = Topping.objects.filter(id__in=topping_ids)
            cart_item.toppings.set(toppings)
        
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        item_id = request.data.get('item_id')
        
        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
            item.delete()
            return Response({'message': 'Item removed from cart'}, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found in cart'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def update_item_quantity(self, request):
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
            item.quantity = quantity
            item.save()
            return Response({
                'price': item.get_price()
            }, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found in cart'}, status=status.HTTP_404_NOT_FOUND)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        cart = Cart.objects.filter(user=request.user, active=True).first()
        if not cart or not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        order_type = request.data.get('order_type', 'D')
        delivery_address = request.data.get('delivery_address', '')
        notes = request.data.get('notes', '')
        
        if order_type == 'D' and not delivery_address:
            return Response({'error': 'Delivery address is required for delivery orders'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate total amount
        total_amount = sum(item.get_price() for item in cart.items.all())
        
        # Add delivery fee if applicable
        delivery_fee = 0
        if order_type == 'D':
            delivery_fee = 50  # Flat delivery fee
            total_amount += delivery_fee
        
        order = Order.objects.create(
            user=request.user,
            order_type=order_type,
            delivery_address=delivery_address,
            delivery_fee=delivery_fee,
            estimated_delivery_time='30-45 minutes',
            payment_method='Cash on Delivery',
            total_amount=total_amount,
            notes=notes
        )
        
        # Create order items from cart items
        for item in cart.items.all():
            order_item = OrderItem.objects.create(
                order=order,
                pizza=item.pizza,
                size=item.size,
                quantity=item.quantity,
                price=item.get_price()
            )
            order_item.toppings.set(item.toppings.all())
        
        # Clear the cart
        cart.items.all().delete()
        cart.active = False
        cart.save()
        
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = new_status
        order.save()
        
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    user = request.user
    profile = user.userprofile
    
    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.email = request.data.get('email', user.email)
    user.save()
    
    profile.phone = request.data.get('phone', profile.phone)
    profile.address = request.data.get('address', profile.address)
    profile.save()
    
    return Response({'success': True})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not user.check_password(current_password):
        return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()
    
    return Response({'success': True})