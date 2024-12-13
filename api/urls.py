from django.urls import path
from .views import (
    RegisterUser,
    ListCreateCategory,
    ProductListCreateView,
    ProductDetails,
    CartAPIView,
    AddToCartAPIView,
    RemoveFromCartAPIView,
    ProfileView,
    LoginView,
    LogoutView,
    ActivateUserAPIView,
    SyncCartView,
    ProductSearchView,
    CustomTokenRefreshView
)

urlpatterns = [
    # Authentication
    path('register/', RegisterUser.as_view(), name='register_user'),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('activate/<str:uid>/<str:token>/', ActivateUserAPIView.as_view(), name='activate'),
    # products
    path('categories/', ListCreateCategory.as_view(), name='list_create_category'),
    path('products/', ProductListCreateView.as_view(), name='list_create_product'),
    path('product/detail/<slug:slug>/', ProductDetails.as_view(), name='product_details'),
    path('product/search/', ProductSearchView.as_view(), name='product_details'),
    # cart
    path('cart/', CartAPIView.as_view(), name='cart'),
    path('cart/add/', AddToCartAPIView.as_view(), name='add_to_cart'),
    path('cart/item/<int:pk>/remove/', RemoveFromCartAPIView.as_view(), name='remove_from_cart'),
    path('cart/sync/', SyncCartView.as_view(), name='sync_cart'),
]
