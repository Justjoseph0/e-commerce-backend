from rest_framework import serializers
from .models import User,Category,Product,CartItem,Cart
from django.contrib.auth.password_validation import validate_password,ValidationError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from .models import User



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
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password','email')
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

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)




class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']



class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']




class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_image = serializers.ImageField(source="product.image", read_only=True) 
    price = serializers.CharField(source='product.price',read_only=True) 
    discounted_price = serializers.CharField(source='product.discounted_price',read_only=True) 
    slug = serializers.SlugField(source="product.slug", read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product_name', 'product_id','product_image','discounted_price', 'quantity','price', 'get_total_price','size','slug']



class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True,read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items']







# class CartItemSerializer(serializers.ModelSerializer):
#     product_name = serializers.ReadOnlyField(source='product.name')
#     price = serializers.ReadOnlyField(source='product.price')

#     class Meta:
#         model = CartItem
#         fields = ['id', 'product', 'product_name', 'price', 'quantity']

# class CartSerializer(serializers.ModelSerializer):
#     items = CartItemSerializer(many=True)

#     class Meta:
#         model = Cart
#         fields = ['id', 'items']



