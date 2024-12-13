from django.shortcuts import render,HttpResponse,get_object_or_404
from rest_framework import status
from .models import User,Category,Product,Cart,CartItem
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializer import UserSerializer,CategorySerializer,ProductSerializer,LoginSerializer,CartSerializer,CustomTokenRefreshSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny,IsAuthenticated
from .permission import IsAdminUser
from rest_framework.exceptions import NotFound
from .utils import send_activation_email
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from rest_framework.filters import SearchFilter
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.generics import ListAPIView,CreateAPIView,ListCreateAPIView,RetrieveUpdateDestroyAPIView
from .pagination import ProductPagination
from django.core.exceptions import FieldError


# Create your views here.


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer



class RegisterUser(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_activation_email(user, request)
        return Response(
            {"message": "Account created. Check your email to activate your account."},
            status=status.HTTP_201_CREATED
        )

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(email=email, password=password)
        
        if user is None:
            raise AuthenticationFailed('Invalid email or password')
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationFailed('Account is not activated')
        
        refresh = RefreshToken.for_user(user)

        access_token = refresh.access_token
        access_token['is_admin'] = user.is_admin
        access_token['username'] = user.username

        return Response({
                'refresh': str(refresh),
                'access': str(access_token),
            })
        




    
class ActivateUserAPIView(APIView):
    def get(self, request, uid, token):
        try:
            # Decode the user ID
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)

            # Check if the token is valid
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return Response(
                    {"message": "Account activated successfully"},
                    status=status.HTTP_200_OK
                )
            else:
                # Checks if Token is invalid or expired; resend activation email
                send_activation_email(user, request)
                return Response(
                    {"error": "Activation link expired. A new activation email has been sent."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid activation link"},
                status=status.HTTP_400_BAD_REQUEST
            )
        

class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token') 
        response.delete_cookie('refresh_token') 
        return response

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Serialize the authenticated user's data
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class ListCreateCategory(ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly,IsAdminUser]


class RetrieveUpdateDestroyCategory(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly,IsAdminUser]


class ProductListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self,request):
        sort_option = request.query_params.get('sort', None)
        is_available = request.query_params.get('is_available', None)
        category = request.query_params.get('category', None)

        products = Product.objects.all()


        if category:
            products = products.filter(category__name__iexact=category)

        if is_available:
            products = products.filter(is_available=is_available.lower() == 'true')

        if sort_option:
            try:
                products = products.order_by(sort_option)
            except FieldError:
                return Response({"error": "Invalid sorting field"}, status=status.HTTP_400_BAD_REQUEST)
           


        paginator = ProductPagination()

        paginated_product = paginator.paginate_queryset(products, request, view=self)
        serializer = ProductSerializer(paginated_product, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProductDetails(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get_object(self, slug=None):
        try:
            return Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise NotFound({"error": "Product not found"})
        
    def get(self, request,slug):
        product = self.get_object(slug)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    

    def patch(self,request,slug):
        product = self.get_object(slug)
        serializer = ProductSerializer(product, partial=True, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self,request,slug):
        product = self.get_object(slug)
        product.delete()
        return Response({"message": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class ProductSearchView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description']  # Fields to search

    def get_queryset(self):
        search_term = self.request.GET.get('search', '')
        if search_term:
            return super().get_queryset().filter(name__icontains=search_term)
        return super().get_queryset()




class CartAPIView(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    def get(self, request):
        # Get or create a cart for the user
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def delete(self, request):
        # Clear the cart
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        return Response({"message": "Cart cleared successfully"}, status=status.HTTP_204_NO_CONTENT)

class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)
        size = request.data.get("size")
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product matching query does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate size
        if size and size not in dict(Product.SIZE_CHOICES).keys():
            return Response({"error": "Invalid size selected."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check stock availability
        if product.quantity < quantity:
            return Response({"error": "Not enough stock available for this product."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create cart for user
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        # Add product to cart
        cart.add_product(product, quantity, size)
        
        # Serialize and return updated cart
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def patch(self, request):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")
        size = request.data.get("size") 
        
        cart = Cart.objects.filter(user=request.user).first()
        
        if not cart:
            return Response({"detail": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Find cart item with specific product and size
        if size:
            cart_item = cart.items.filter(product_id=product_id, size=size).first()
        else:
            cart_item = cart.items.filter(product_id=product_id).first()
        
        if not cart_item:
            return Response({"detail": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)
        
        product = cart_item.product
        available_quantity = product.quantity
        
        if quantity > available_quantity:
            return Response({
                "detail": f"Requested quantity exceeds available stock. Only {available_quantity} items available."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity == 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        
        # Serialize and return the updated cart data
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RemoveFromCartAPIView(APIView):
    def delete(self, request, pk):
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, id=pk)
        cart_item.delete()
        return Response({"message": "Item removed from cart"}, status=status.HTTP_204_NO_CONTENT)
    



class SyncCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        local_cart = request.data.get('cart', [])

        # Get the user's cart (or create one if it doesn't exist)
        cart, created = Cart.objects.get_or_create(user=user)

        # Iterate through the local cart items and add/update them in the backend cart
        for item in local_cart:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            size = item.get('size')

            # Check if the item exists in the cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_id=product_id,
                size=size
            )

            # Update the quantity if the item exists
            cart_item.quantity = quantity
            cart_item.save()

        return Response({"message": "Cart synced successfully!"}, status=status.HTTP_200_OK)