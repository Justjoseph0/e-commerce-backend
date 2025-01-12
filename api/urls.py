from django.urls import path
from .views import (
    RegisterUser,
    PasswordResetAPIView,
    PasswordResetConfirmAPIView,
    ListCreateCategory,
    ProductListCreateView,
    ProductDetails,
    CartAPIView,
    AddToCartAPIView,
    RemoveFromCartAPIView,
    ProfileView,
    LoginView,
    ActivateUserAPIView,
    ProductSearchView,
    CustomTokenRefreshView,
    InitializePaymentView,
    PaystackWebhookView,
    VerifyPaymentView,
    OrderStatusView,
    UserOrderView,
    AdminOrderView,
    AdminOrderDetail,
    AdminUserView,
    UserAddressView,
    UserAddressEditDelete,
    WishListView,
    MonthlyOrdersAPIView,
    ProductReviewApiView,
    OrderStatusUpdateAPIView,
    PendingReviewsView,
    PendingReviewDetailView
)

urlpatterns = [
    # Authentication
    path('register/', RegisterUser.as_view(), name='register_user'),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('address/', UserAddressView.as_view(), name='user-address'),
    path('address/<int:pk>/', UserAddressEditDelete.as_view(), name='user-address'),
    path('admin/users/', AdminUserView.as_view(), name='admin-users'),
    path('activate/<str:uid>/<str:token>/', ActivateUserAPIView.as_view(), name='activate'),
    path('reset-password/',PasswordResetAPIView.as_view(),name='reset-password'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/',PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),

    # products
    path('categories/', ListCreateCategory.as_view(), name='list_create_category'),
    path('products/', ProductListCreateView.as_view(), name='list_create_product'),
    path('product/detail/<slug:slug>/', ProductDetails.as_view(), name='product_details'),
    path('product/search/', ProductSearchView.as_view(), name='product_details'),
    # cart
    path('cart/', CartAPIView.as_view(), name='cart'),
    path('cart/add/', AddToCartAPIView.as_view(), name='add_to_cart'),
    path('cart/item/<int:pk>/remove/', RemoveFromCartAPIView.as_view(), name='remove_from_cart'),

    # payment
    path('payment/',InitializePaymentView.as_view(),name='initialize-payment'),
     path("paystack/webhook/", PaystackWebhookView.as_view(), name="paystack-webhook"),
     path("orders/status/<str:reference>/", OrderStatusView.as_view(), name="order-status"),
     path('verify-payment/<str:reference>/', VerifyPaymentView.as_view(), name='verify_payment'),

    #  order
     path("user/orders/", UserOrderView.as_view(), name="user-orders"),
     path('admin/orders/',AdminOrderView.as_view(),name='admin-orders'),
     path('admin/order/<str:reference>/',AdminOrderDetail.as_view(),name='admin-orders-detail'),
     path('admin/update-delivery/<str:order_id>/', OrderStatusUpdateAPIView.as_view(), name="admin-update-delivery-status"),
    #  wishlist
    path('wishlist/', WishListView.as_view(), name='wishlist'),  
    path('monthly-orders/', MonthlyOrdersAPIView.as_view(), name='monthly-orders'),
    # reviews
    path('product/<int:product_id>/reviews/', ProductReviewApiView.as_view(), name='product-review'),
    path('order/pending_review/', PendingReviewsView.as_view(),name="pending-review"),
     path('order/pending/<str:reference>/', PendingReviewDetailView.as_view(), name='pending-review-detail'),

]
