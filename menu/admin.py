from django.contrib import admin
from .models import Category, Product, Offer
from .models import Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price_syp", "is_active", "is_featured")
    list_filter = ("category", "is_active", "is_featured")
    list_editable = ("price_syp", "is_active", "is_featured")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug", "description")


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("title", "price_syp", "order", "is_active")
    list_editable = ("order", "is_active", "price_syp")
    search_fields = ("title", "subtitle")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("name_snapshot", "price_syp_snapshot", "qty")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "table_no", "status", "total_syp", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("table_no", "id")
    inlines = [OrderItemInline]