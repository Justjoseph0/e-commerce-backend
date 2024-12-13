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
    PRODUCT_TYPE_CHOICES = [
        ('sized', 'Sized Product'),
        ('non-sized', 'Non-Sized Product'),
    ]
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/',validators=[FileExtensionValidator(['png', 'jpg'])],null=True,blank=True)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default='sized')
    is_available = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=0)
    slug = AutoSlugField(populate_from='name', unique=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name





class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='sizes',limit_choices_to={'product_type': 'sized'})   # Only allow sized products here
    size = models.CharField(max_length=2, choices=Product.SIZE_CHOICES,null=True,blank=True)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.product.name
    




class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def add_product(self, product, quantity=1, size=None):
        # Validate product type and size
        if product.product_type == 'sized':
            # Ensure size is provided for sized products
            if not size:
                raise ValueError("Size must be specified for sized products!")
            
            try:
                # Explicitly check if ProductSize exists
                product_size = ProductSize.objects.get(product=product, size=size)
            except ProductSize.DoesNotExist:
                raise ValueError(f"Size {size} is not available for this product!")
            
            # Check stock for sized products
            cart_item = self.items.filter(product=product, product_size=product_size).first()
            
            if cart_item:
                # Updating existing cart item
                if product_size.quantity >= cart_item.quantity + quantity:
                    cart_item.quantity += quantity
                    cart_item.save()
                else:
                    raise ValueError(f"Not enough stock for size {size}. Available: {product_size.quantity}")
            else:
                # Creating new cart item
                if product_size.quantity >= quantity:
                    CartItem.objects.create(
                        cart=self,
                        product=product,
                        product_size=product_size,
                        quantity=quantity
                    )
                else:
                    raise ValueError(f"Not enough stock for size {size}. Available: {product_size.quantity}")
        
        else:
            # Handle non-sized products
            cart_item = self.items.filter(product=product, product_size=None).first()
            
            if cart_item:
                # Updating existing cart item
                if product.quantity >= cart_item.quantity + quantity:
                    cart_item.quantity += quantity
                    cart_item.save()
                else:
                    raise ValueError("Not enough stock available!")
            else:
                # Creating new cart item
                if product.quantity >= quantity:
                    CartItem.objects.create(
                        cart=self,
                        product=product,
                        quantity=quantity
                    )
                else:
                    raise ValueError("Not enough stock available!")
                
     
        


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, blank=True, null=True)

    def get_total_price(self):
        return self.product.discounted_price * self.quantity

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"
