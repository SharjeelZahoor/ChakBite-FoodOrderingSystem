from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    address = models.TextField()
    
    def __str__(self):
        return self.user.username

class Pizza(models.Model):
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='pizzas/')
    small_price = models.DecimalField(max_digits=5, decimal_places=2)
    medium_price = models.DecimalField(max_digits=5, decimal_places=2)
    large_price = models.DecimalField(max_digits=5, decimal_places=2)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Topping(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    available = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    size = models.CharField(max_length=1, choices=Pizza.SIZE_CHOICES)
    toppings = models.ManyToManyField(Topping, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    
    def get_price(self):
        base_price = getattr(self.pizza, f"{self.size.lower()}_price")
        toppings_price = sum(topping.price for topping in self.toppings.all())
        return (base_price + toppings_price) * self.quantity
    
    def __str__(self):
        return f"{self.quantity}x {self.pizza.name} ({self.size})"

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('D', 'Delivery'),
        ('O', 'On-Spot'),
    ]
    
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('PR', 'Preparing'),
        ('OD', 'Out for Delivery'),
        ('DL', 'Delivered'),
        ('C', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=1, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='P')
    delivery_address = models.TextField(blank=True, null=True)
    delivery_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    estimated_delivery_time = models.CharField(max_length=50, blank=True)
    payment_method = models.CharField(max_length=20, default='Cash on Delivery')
    total_amount = models.DecimalField(max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    pizza = models.ForeignKey(Pizza, on_delete=models.CASCADE)
    size = models.CharField(max_length=1, choices=Pizza.SIZE_CHOICES)
    toppings = models.ManyToManyField(Topping, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.pizza.name} ({self.size})"