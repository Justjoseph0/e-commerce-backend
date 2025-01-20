from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from autoslug import AutoSlugField
from django.core.validators import FileExtensionValidator
from django.utils.timezone import now
from cloudinary.models import CloudinaryField



    
# user
class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)


class UserAddress(models.Model):
    COUNTRY_CHOICES = [
        ('Nigeria', 'Nigeria'),
    ]

    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home'),
        ('office', 'Office')
    ]

    STATE_CHOICES = [
        ('Abia', 'Abia'),
        ('Adamawa', 'Adamawa'),
        ('Akwa Ibom', 'Akwa Ibom'),
        ('Anambra', 'Anambra'),
        ('Bauchi', 'Bauchi'),
        ('Bayelsa', 'Bayelsa'),
        ('Benue', 'Benue'),
        ('Borno', 'Borno'),
        ('Cross River', 'Cross River'),
        ('Delta', 'Delta'),
        ('Ebonyi', 'Ebonyi'),
        ('Edo', 'Edo'),
        ('Ekiti', 'Ekiti'),
        ('Enugu', 'Enugu'),
        ('Gombe', 'Gombe'),
        ('Imo', 'Imo'),
        ('Jigawa', 'Jigawa'),
        ('Kaduna', 'Kaduna'),
        ('Kano', 'Kano'),
        ('Katsina', 'Katsina'),
        ('Kebbi', 'Kebbi'),
        ('Kogi', 'Kogi'),
        ('Kwara', 'Kwara'),
        ('Lagos', 'Lagos'),
        ('Nasarawa', 'Nasarawa'),
        ('Niger', 'Niger'),
        ('Ogun', 'Ogun'),
        ('Ondo', 'Ondo'),
        ('Osun', 'Osun'),
        ('Oyo', 'Oyo'),
        ('Plateau', 'Plateau'),
        ('Rivers', 'Rivers'),
        ('Sokoto', 'Sokoto'),
        ('Taraba', 'Taraba'),
        ('Yobe', 'Yobe'),
        ('Zamfara', 'Zamfara'),
        ('FCT', 'FCT'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, default='Nigeria')
    state = models.CharField(max_length=50, choices=STATE_CHOICES)
    city = models.CharField(max_length=100)
    street_address = models.TextField()
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    is_default = models.BooleanField(default=False)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='home')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses of the user to non-default
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        elif not self.is_default and not UserAddress.objects.filter(user=self.user, is_default=True).exists():
            # If this address is not default, and the user doesn't have any default address, make this one default
            self.is_default = True

        super().save(*args, **kwargs)



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
    image = CloudinaryField('image', null=True, blank=True) 
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
                
    def __str__(self):
        return self.user.username
        
                
     
        


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, blank=True, null=True)

    def get_total_price(self):
        return self.product.discounted_price * self.quantity

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"
    


class Order(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    reference = models.CharField(max_length=100, unique=True)  
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='Pending')
    address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        if self.delivery_status == 'Delivered' and not self.delivered_date:
            self.delivered_date = now()  
        super().save(*args, **kwargs)
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    size = models.CharField(max_length=10, blank=True, null=True)

    def get_total_price(self):
        return self.quantity * self.product.discounted_price
    
    def __str__(self):
        return self.order.user.username
    





class WishList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
    

class WishListItem(models.Model):
    wishlist = models.ForeignKey(WishList, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='wishlist_items', on_delete=models.CASCADE)
    size = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.product.name} - {self.size if self.size else 'No Size'}"



class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="review")
    name = models.CharField(max_length=50, blank=True, null=True)
    title = models.CharField(max_length=100)
    rating = models.PositiveIntegerField()
    review = models.TextField()
    size = models.CharField(max_length=10, blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username