from rest_framework import serializers
from .models import User,Category,Product,CartItem,Cart,ProductSize,Order,OrderItem,UserAddress,WishList,WishListItem,Review
from django.contrib.auth.password_validation import validate_password,ValidationError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from django.db.models import Sum



class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        refresh_token = attrs['refresh']
        refresh = RefreshToken(refresh_token)

        user_id = refresh['user_id']
        user = User.objects.get(id=user_id)

        access_token = AccessToken(data['access'])
        access_token['is_admin'] = user.is_admin
        access_token['username'] = user.username

        data['access'] = str(access_token)
        return data
    

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    



class UserSerializer(serializers.ModelSerializer):
    total_purchase = serializers.SerializerMethodField()
    # total_revenue = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('id','first_name', 'last_name', 'username', 'password','email','is_active','date_joined','total_purchase')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False
        )
    
        
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def get_total_purchase(self, obj):
        # Calculate total purchase for a specific user
        total = Order.objects.filter(user=obj).aggregate(Sum('total_amount'))['total_amount__sum']
        return total if total is not None else 0
    
    # def get_total_revenue(self, obj):
    #     # Calculate total revenue for all users
    #     total_revenue = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum']
    #     return total_revenue if total_revenue is not None else 0

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)




class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']



class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = [ 'size', 'quantity']
        

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    sizes = ProductSizeSerializer(many=True,required=False)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Extract sizes data if provided
        sizes_data = validated_data.pop('sizes', None)
        product = Product.objects.create(**validated_data)

        # Handle sizes for sized products
        if validated_data.get('product_type') == 'sized' and sizes_data:
            for size_data in sizes_data:
                ProductSize.objects.create(product=product, **size_data)
        elif validated_data.get('product_type') == 'sized' and not sizes_data:
            raise serializers.ValidationError({"sizes": "This field is required for sized products."})

        return product
    
    def update(self, instance, validated_data):
        # Extract and handle sizes data
        sizes_data = validated_data.pop('sizes', None)

        # Update the main product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle updates for `sizes`
        if instance.product_type == 'sized':
            if sizes_data is None:
                raise serializers.ValidationError({"sizes": "This field is required for sized products."})
            
            # Clear existing sizes and recreate them
            instance.sizes.all().delete()  # Assuming related_name='sizes' in ProductSize
            for size_data in sizes_data:
                ProductSize.objects.create(product=instance, **size_data)

        return instance




class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_image = serializers.ImageField(source="product.image", read_only=True) 
    price = serializers.CharField(source='product.price',read_only=True) 
    discounted_price = serializers.CharField(source='product.discounted_price',read_only=True) 
    slug = serializers.SlugField(source="product.slug", read_only=True)
    product_size = serializers.CharField(source='product_size.size', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product_name', 'product_id','product_image','discounted_price', 'quantity','price', 'get_total_price','product_size','slug']



class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True,read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items']






class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    price = serializers.CharField(source='product.discounted_price',read_only=True) 
    product_image = serializers.ImageField(source='product.image')
    reference = serializers.CharField(source='order.reference')
    delivered_date = serializers.CharField(source='order.delivered_date')
    total_price = serializers.SerializerMethodField()


    class Meta:
        model = OrderItem
        fields = '__all__'

    def get_total_price(self, obj):
        return obj.get_total_price()


class AddressSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="user.email", read_only=True)
    class Meta:
        model = UserAddress
        fields = '__all__'
        read_only_fields = ('user','created_at')




class OrderSerializer(serializers.ModelSerializer):
    orders = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    address = AddressSerializer()

    class Meta:
        model = Order
        fields = ["id", "username","email", "reference", "status","delivery_status", "total_amount",'address', "created_at", "orders"]

        







class WishListItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    size = serializers.CharField()

    class Meta:
        model = WishListItem
        fields = ['product', 'size']


class WishListSerializer(serializers.ModelSerializer):
    items = WishListItemSerializer(many=True)

    class Meta:
        model = WishList
        fields = ['items']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    product = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Review
        exclude = ('order_item',)
        read_only_fields = ['user', 'created_at',"product"]

class MonthlyOrderSerializer(serializers.Serializer):
    month = serializers.CharField()
    total_orders = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)