from django.contrib import admin
from .models import User,Product,Cart,CartItem,Category

# Register your models here.

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Cart)



class ProductAdmin(admin.ModelAdmin):
    list_display = ('id',"name", 'price')


class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id','product','size')





admin.site.register(Product,ProductAdmin)
admin.site.register(CartItem,CartItemAdmin)