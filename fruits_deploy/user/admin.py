from django.contrib import admin
from .models import Supplier, Seller, Container, Item, ContainerItem, Sale,Payment, Lose, ContainerExpense, ContainerBill, SupplierPay
from django.db.models import Sum

admin.site.site_header = 'Tiger tech'
admin.site.site_title = 'إدارة موقع تايجر'
admin.site.index_title = 'الإدارة'


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    readonly_fields = ('num_of_items','main_total_count','con_weight','total_con_price')

class ContainerItemAdmin(admin.ModelAdmin):
    readonly_fields = ('total_item_price','name','remaining_count')

class ContainerAdmin(admin.ModelAdmin):
    readonly_fields = ('total_con_price',)

admin.site.register(Supplier)
admin.site.register(Seller)
admin.site.register(Item)
admin.site.register(ContainerItem)
admin.site.register(Sale)
admin.site.register(Payment)
admin.site.register(Lose)
admin.site.register(ContainerExpense)
admin.site.register(ContainerBill)
admin.site.register(SupplierPay)