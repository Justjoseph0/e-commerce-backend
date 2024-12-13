from django.contrib import admin
from .models import User,Product,Cart,CartItem,Category,ProductSize

# Register your models here.

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Cart)



class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id','product','product_size')


class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'quantity')
    list_filter = ('product', 'size')
    search_fields = ('product__name',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'product_type', 'price', 'quantity', 'is_available')
    list_filter = ('category', 'product_type', 'is_available')
    search_fields = ('name', 'category__name')





admin.site.register(Product,ProductAdmin)
admin.site.register(CartItem,CartItemAdmin)
admin.site.register(ProductSize,ProductSizeAdmin)