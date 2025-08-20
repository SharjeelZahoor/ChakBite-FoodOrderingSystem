from .models import Cart

def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, active=True)
        count = cart.items.count()
    return {'cart_count': count}