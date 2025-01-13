from django.shortcuts import render,HttpResponse,get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .models import User,Category,Product,Cart,CartItem,Order,OrderItem,UserAddress,WishList,WishListItem,Review
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializer import UserSerializer,CategorySerializer,ProductSerializer,LoginSerializer,CartSerializer,CustomTokenRefreshSerializer,OrderSerializer,AddressSerializer,WishListSerializer,MonthlyOrderSerializer,PasswordResetSerializer,PasswordResetConfirmSerializer,ReviewSerializer,OrderItemSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny,IsAuthenticated
from .permission import IsAdminUser,IsAdminGetOnly
from rest_framework.exceptions import NotFound
from .utils import send_activation_email,send_resetpassword_email,notify_user
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework.filters import SearchFilter
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.generics import ListAPIView,CreateAPIView,ListCreateAPIView,RetrieveUpdateDestroyAPIView
from .pagination import ProductPagination,OrderPagination,UserPagination
from django.core.exceptions import FieldError
import requests
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import hashlib
import hmac  
from django.db.models import Q 
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count

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
        

class PasswordResetAPIView(APIView):
    def post(self,request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                 return Response(
                    {"detail": "No user is registered with this email."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            send_resetpassword_email(user,request)
            return Response(
                {"detail": "Password reset email has been sent."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
class PasswordResetConfirmAPIView(APIView):
    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                print("Decoded UID:", uid)
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, User.DoesNotExist):
                return Response(
                    {"detail": "Invalid reset link."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if default_token_generator.check_token(user, token):
                user.set_password(serializer.validated_data['password'])
                user.save()
                return Response(  {"detail": "Password has been reset successfully."},status=status.HTTP_200_OK)
            return Response( {"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
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
    permission_classes = [IsAuthenticatedOrReadOnly,IsAdminUser]

    def get(self,request):
        sort_option = request.query_params.get('sort', None)
        is_available = request.query_params.get('is_available', None)
        category = request.query_params.get('category', None)
        size = request.query_params.get('size', None)

        products = Product.objects.all()


        if category:
            products = products.filter(category__name__iexact=category)
        
        if size:
            products = products.filter(sizes__size__iexact=size)

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
    permission_classes = [IsAuthenticatedOrReadOnly,IsAdminUser]
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
    permission_classes = [IsAuthenticated]
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

        # Get or create cart for user
        cart, _ = Cart.objects.get_or_create(user=request.user)

        try:
            # Use the existing add_product method from the Cart model
            cart.add_product(product, quantity, size)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

        cart_item = cart.items.filter(product_id=product_id, product_size__size=size if size else None).first()
        if not cart_item:
            return Response({"detail": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)

        if quantity == 0:
            cart_item.delete()
        else:
            if cart_item.product.product_type == 'sized':
                product_size = cart_item.product_size
                if product_size.quantity < quantity:
                    return Response({"detail": f"Not enough stock for size {size}. Available: {product_size.quantity}"}, status=status.HTTP_400_BAD_REQUEST)
            elif cart_item.product.quantity < quantity:
                return Response({"detail": "Not enough stock available!"}, status=status.HTTP_400_BAD_REQUEST)

            cart_item.quantity = quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)




class RemoveFromCartAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, pk):
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, id=pk)
        cart_item.delete()
        return Response({"message": "Item removed from cart"}, status=status.HTTP_204_NO_CONTENT)


    



@method_decorator(csrf_exempt, name="dispatch")
class InitializePaymentView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user

        # Get the user's cart
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total amount from cart items
        cart_total = sum(item.get_total_price() for item in cart.items.all())

        if cart_total <= 0:
            return Response({"error": "Invalid cart total"}, status=status.HTTP_400_BAD_REQUEST)

        # Convert amount to kobo (Paystack accepts values in kobo)
        amount_in_kobo = int(cart_total * 100)

        address_id = request.data.get("address_id")
        if not address_id:
            return Response({"error": "Address is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the address exists and belongs to the user
        address = get_object_or_404(UserAddress, id=address_id, user=user)

        # Generate a unique payment reference
        reference = f"{user.id}-{int(amount_in_kobo)}-{Order.objects.count()}"

        # Create an Order and link it with the cart
        order = Order.objects.create(
            user=user,
            reference=reference,
            total_amount=cart_total,
            status="pending",
            address=address
        )

        # Copy cart items to order items
        for item in cart.items.all():
            size = item.product_size.size if hasattr(item.product_size, 'size') else None
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                size=size 
            )

        #  Clear the cart after creating the order
        # cart.items.all().delete()

        # Send request to Paystack
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "email": user.email,
            "amount": amount_in_kobo,
            "reference": reference,
            "callback_url": "https://e-commerce-navy-nine.vercel.app/verify-payment",
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return Response(response.json(), status=status.HTTP_200_OK)
        return Response(response.json(), status=status.HTTP_400_BAD_REQUEST)
    



@method_decorator(csrf_exempt, name="dispatch")
class PaystackWebhookView(APIView):
    def post(self, request):
        # Get Paystack's signature from headers
        paystack_signature = request.headers.get("X-Paystack-Signature")
        # print(paystack_signature)
        if not paystack_signature:
            return Response({"error": "Missing Paystack signature"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the signature
        payload = request.body
        print("Raw Payload: ", payload)
        secret_key = settings.PAYSTACK_SECRET_KEY
        expected_signature = hmac.new(
            bytes(secret_key, "utf-8"),
            payload,
            hashlib.sha512
        ).hexdigest()

        if paystack_signature != expected_signature:
            return Response({"error": "Invalid signature"}, status=status.HTTP_403_FORBIDDEN)

        # Parse the payload
        event = json.loads(payload)
        print("Event received: ", event)
        event_type = event.get("event")
        print(f"Event Type: {event_type}")

        if event_type == "charge.success":
            # Extract the reference from the webhook data
            reference = event["data"]["reference"]
            payment_status = event["data"]["status"] 

            # Verify that the payment is successful
            if payment_status == "success":
                try:
                    # Find the order using the reference
                    order = Order.objects.get(reference=reference)
                    # Update the order status to "success"
                    order.status = "success"
                    order.save()
                    notify_user(order, "Processing")
                    return Response({"message": "Order updated successfully"}, status=status.HTTP_200_OK)
                except Order.DoesNotExist:
                    return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
                
        elif event_type == "charge.failed":
            reference = event["data"].get("reference")
            try:
                order = Order.objects.get(reference=reference)
                order.status = "failed"
                order.save()
                return Response({"message": "Order updated to failed"}, status=status.HTTP_200_OK)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


        return Response({"message": "Webhook received"}, status=status.HTTP_200_OK)
    


class OrderStatusView(APIView):
    def get(self, request, reference):
        try:
            order = Order.objects.get(reference=reference)
            return Response({"status": order.status, "amount": order.total_amount,"transaction_id": order.reference, "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, reference):
        if not reference:
            return Response({"error": "Reference is required"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        }
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        response = requests.get(url, headers=headers)
        res = response.json()

        if res.get('status'):
            # Extract transaction details
            payment_status = res['data']['status']
            order = Order.objects.filter(reference=reference).first()

            if payment_status == "success":
                if order:
                    order.status = "success"
                    order.save()
                return Response({"message": "Payment verified successfully" }, status=status.HTTP_200_OK)

            elif payment_status == "failed":
                if order:
                    order.status = "failed"
                    order.save()
                return Response({"message": "Payment failed. The payment was unsuccessful."}, status=status.HTTP_400_BAD_REQUEST)

            else: 
                if order:
                    order.status = payment_status 
                    order.save()
                return Response({
                    "error": f"Payment verification incomplete. Status: {payment_status}",
                    "details": res['data'].get('gateway_response', "No additional information available.")
                }, status=status.HTTP_400_BAD_REQUEST)

        else:
            # Handle cases where the Paystack response indicates an error
            return Response({
                "error": "Failed to verify payment.",
                "details": res.get("message", "An unknown error occurred.")
            }, status=status.HTTP_400_BAD_REQUEST)


        

    


class UserOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")

        paginator = OrderPagination()


        paginated_order = paginator.paginate_queryset(orders, request, view=self)
        serializer = OrderSerializer(paginated_order, many=True)
        return paginator.get_paginated_response(serializer.data)



class AdminOrderView(APIView):
    permission_classes = [IsAdminGetOnly]

    def get(self,request):
        status_filter = request.query_params.get('status', None)
        search_query = request.query_params.get('search', None)


        orders = Order.objects.all().order_by('-created_at')

        if status_filter:
            try:
               orders = orders.filter(status=status_filter)
            except FieldError:
                return Response({"error": "Invalid sorting field"}, status=status.HTTP_400_BAD_REQUEST)
            
        if search_query:
                orders = orders.filter(
                    Q(user__username__icontains=search_query) |  # Searching by order reference
                    Q(reference__icontains=search_query) | # Searching by user name 
                    Q(user__email__icontains=search_query)   # Searching by user email 
                )
        paginator = OrderPagination()

        paginated_order = paginator.paginate_queryset(orders, request, view=self)
        serializer = OrderSerializer(paginated_order, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class AdminOrderDetail(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,reference):
        print(reference)
        try:
            order = Order.objects.get(reference=reference)
            serializer = OrderSerializer(order)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "oder not found"}, status=status.HTTP_404_NOT_FOUND)
        
class OrderStatusUpdateAPIView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)

            if order.status != "success":
                return Response({'error': 'Only orders with a status of "successful" can be updated.'}, status=status.HTTP_400_BAD_REQUEST)


            new_status = request.data.get('delivery_status')
            if new_status in ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']:
                if order.delivery_status == new_status:
                    return Response({'error': f'The order is already marked as "{new_status}".'}, status=status.HTTP_400_BAD_REQUEST)
                order.delivery_status = new_status
                order.save()
                # notify_user(order)
                return Response({'message': f'Status updated to {new_status}'})
            else:
                return Response({'error': 'Invalid status!'}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found!'}, status=status.HTTP_404_NOT_FOUND)

class AdminUserView(APIView):
    permission_classes = [IsAdminGetOnly]
    def get(self,request):
        search_query = request.query_params.get('search', None)
        status_filter = request.query_params.get('status',None)

        users = User.objects.all().order_by('-date_joined')

        if status_filter:
                users = users.filter(is_active=status_filter.lower() == "true")

        if search_query:
                users = users.filter(
                    Q(username__icontains=search_query) |  
                    Q(first_name__icontains=search_query) | 
                    Q(last_name__icontains=search_query) | 
                    Q(email__icontains=search_query)
                )

        paginator = UserPagination()

        paginated_order = paginator.paginate_queryset(users, request, view=self)
        
        serializer = UserSerializer(paginated_order, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class UserAddressView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        addresses = UserAddress.objects.filter(user=user).order_by('-is_default')
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    

    def post(self,request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    

class UserAddressEditDelete(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self,pk):
        return get_object_or_404(UserAddress, pk=pk)
    
    def get(self,request,pk):
        address = self.get_object(pk)
        serializer = AddressSerializer(address)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def patch(self,request,pk):
        address = self.get_object(pk)
        serializer = AddressSerializer(address,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,pk):
        address = self.get_object(pk)
        address.delete()
        return Response({"message":"Address deleted successfully"},status=status.HTTP_204_NO_CONTENT)
    


class WishListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        wishlist, _ = WishList.objects.get_or_create(user=user)
        serializer = WishListSerializer(wishlist)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        product_id = request.data.get('product_id')
        size = request.data.get('size')

        if not product_id:
            return Response(
                {'error': 'Product ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(Product, id=product_id)
        wishlist, created = WishList.objects.get_or_create(user=request.user)

        # Check if the product is sized and requires a size
        if product.product_type == 'sized':
            if not size:
                return Response(
                    {'error': 'Size is required for this product'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Check for duplicate product with size
            if wishlist.items.filter(product=product, size=size).exists():
                return Response(
                    {'error': f'Product "{product.name}" in size "{size}" is already in your wishlist'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Check for duplicate non-sized product
            if wishlist.items.filter(product=product).exists():
                return Response(
                    {'error': f'Product "{product.name}" is already in your wishlist'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Add the product to the wishlist
        wishlist_item = WishListItem.objects.create(
            wishlist=wishlist,
            product=product,
            size=size if product.product_type == 'sized' else None 
        )

        serializer = WishListSerializer(wishlist)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def delete(self, request):
        product_id = request.data.get('product_id')
        size = request.data.get('size', None)

        if not product_id:
            return Response(
                {'error': 'Product ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        wishlist = get_object_or_404(WishList, user=request.user)
        product = get_object_or_404(Product, id=product_id)

        # Handle removal of sized product or regular product
        try:
            if size:  # It's a sized product
                wishlist_item = wishlist.items.get(product=product, size=size)
            else:  # It's a regular product
                wishlist_item = wishlist.items.get(product=product, size__isnull=True)

            wishlist_item.delete()

            return Response({"message": "Item removed from wishlist"}, status=status.HTTP_204_NO_CONTENT)
        except WishListItem.DoesNotExist:
            return Response(
                {'error': 'Product not in wishlist'},
                status=status.HTTP_404_NOT_FOUND
            )



class MonthlyOrdersAPIView(APIView):
    def get(self, request):
        orders = (
            Order.objects.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                total_orders=Count('id'),
                total_amount=Sum('total_amount')
            )
            .order_by('month')
        )
        serializer = MonthlyOrderSerializer(orders, many=True)
        return Response(serializer.data)
    


class ProductReviewApiView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewSerializer

    def get_object(self, product_id):
        return get_object_or_404(Product, pk=product_id)

    def post(self, request, product_id):
        product = self.get_object(product_id)
        reference = request.data.get("reference")
        size = request.data.get("size")

        if not reference:
            return Response(
                {"error": "Reference is required to review the product."},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        order_items = OrderItem.objects.filter(
            order__reference=reference,
            order__user=request.user,
            order__status="success",
            order__delivery_status="Delivered",
            product=product
        )

        if not order_items.exists():
            return Response(
                {"error": "You can only review products you have successfully purchased and that have been delivered."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if this is a sized product
        first_item = order_items.first()
        is_sized_product = first_item.size is not None

        if is_sized_product:
            if not size:
                return Response(
                    {"error": "Size is required for this product."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # , filter by the specific size
            order_item = order_items.filter(size=size).first()
            if not order_item:
                return Response(
                    {"error": f"You haven't purchased this product in size {size}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # For non-sized products
            order_item = first_item
            size = None 

        # Check for existing review
        existing_review = Review.objects.filter(
            user=request.user,
            product=product,
            size=size
        ).exists()

        if existing_review:
            return Response(
                {"error": "You have already reviewed this product" + (f" in size {size}" if size else "") + "."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the review
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                user=request.user,
                product=product,
                order_item=order_item,
                size=size
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class PendingReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        
        delivered_items = OrderItem.objects.filter(
            order__user=user,
            order__status="success",
            order__delivery_status="Delivered"
        )

        reviewed_items = Review.objects.filter(user=user).values('product', 'size')

        
        reviewed_combinations = {(review['product'], review['size']) for review in reviewed_items}

      
        pending_items = [
            item for item in delivered_items
            if (item.product.id, item.size) not in reviewed_combinations
        ]

        serializer = OrderItemSerializer(pending_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PendingReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        user = request.user
        size = request.query_params.get("size", None)
        reference = request.query_params.get("reference", None)

        try:
            order_items = OrderItem.objects.filter(
                order__reference=reference,
                product_id=product_id,
                order__user=user,
                order__status="success",
                order__delivery_status="Delivered"
            )
            
            if not order_items.exists():
                return Response(
                    {"error": "Order item not found or not eligible for review."},
                    status=status.HTTP_404_NOT_FOUND
                )

        
            first_item = order_items.first()
            is_sized_product = first_item.size is not None

            if is_sized_product:
                if not size:
                    return Response(
                        {"error": "Size parameter is required for this product."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                order_item = order_items.filter(size=size).first()
                if not order_item:
                    return Response(
                        {"error": f"No order item found with size {size}."},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                order_item = first_item
                size = None

            # Check for existing review
            existing_review = Review.objects.filter(
                product_id=product_id,
                user=user,
                size=size
            ).exists()

            if existing_review:
                return Response(
                    {"error": "You have already reviewed this product" + 
                             (f" in size {size}" if size else "") + "."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = OrderItemSerializer(order_item)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

