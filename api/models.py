from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from autoslug import AutoSlugField
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import FileExtensionValidator



    
# user
class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=200, blank=True)
    is_admin = models.BooleanField(default=False)



class Category(models.Model):
    name = models.CharField(max_length=100,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    


class Product(models.Model):
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    ]
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/',validators=[FileExtensionValidator(['png', 'jpg'])])
    size = models.CharField(max_length=2, choices=SIZE_CHOICES)
    is_available = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=0)
    slug = AutoSlugField(populate_from='name', unique=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name





class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    def add_product(self, product, quantity=1, size=None):
            # Find existing cart item with the same product and size
            cart_item = self.items.filter(product=product, size=size).first()
            
            if cart_item:
                # If item exists, increase quantity
                cart_item.quantity += quantity
                cart_item.save()
            else:
                # If item doesn't exist, create new cart item
                CartItem.objects.create(
                    cart=self, 
                    product=product, 
                    quantity=quantity, 
                    size=size
                )
        
    def __str__(self):
            return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=2, choices=Product.SIZE_CHOICES, blank=True, null=True)

    def get_total_price(self):
        return self.product.discounted_price * self.quantity

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"
