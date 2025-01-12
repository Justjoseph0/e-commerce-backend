from django.contrib import admin
from .models import User,Product,Cart,CartItem,Category,ProductSize,Order,OrderItem,UserAddress,WishList,WishListItem,Review

# Register your models here.

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(WishList)
admin.site.register(WishListItem)






class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('id','user',  'city', 'state')
    search_fields = ('user__username', 'city', 'state')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'reference', 'total_amount','status','delivery_status')


class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id','product','product_size')


class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'quantity')
    list_filter = ('product', 'size')
    search_fields = ('product__name',)


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id','order', 'product', 'quantity',"order__status", 'order__delivery_status','order__reference')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'category', 'product_type', 'price', 'quantity', 'is_available')
    list_filter = ('category', 'product_type', 'is_available')
    search_fields = ('name', 'category__name')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id",'rating','review','user__username']




admin.site.register(Review,ReviewAdmin)
admin.site.register(Product,ProductAdmin)
admin.site.register(CartItem,CartItemAdmin)
admin.site.register(ProductSize,ProductSizeAdmin)
admin.site.register(OrderItem,OrderItemAdmin)
admin.site.register(Order,OrderAdmin)
admin.site.register(UserAddress,UserAddressAdmin)
