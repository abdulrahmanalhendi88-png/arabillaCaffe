from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("home/", views.home, name="home"),

    # صفحات العروض
    path("offers/", views.offers, name="offers"),

    # ✅ تخصيص عرض (Route واحد فقط) - حسب الـ slug
    path("offer/<slug:slug>/", views.offer_customize, name="offer_customize"),

    # تفاصيل منتج
    path("product/<slug:slug>/", views.product_details, name="product_details"),

    # السلة
    path("cart/", views.cart_page, name="cart"),
    path("cart/add/<slug:slug>/", views.cart_add, name="cart_add"),
    path("cart/add-offer/<int:offer_id>/", views.cart_add_offer, name="cart_add_offer"),

    # تحديث/حذف بسطر السلة باستخدام key (p:12 / o:3)
    path("cart/update-key/", views.cart_update_key, name="cart_update_key"),
    path("cart/remove-key/", views.cart_remove_key, name="cart_remove_key"),

    path("cart/set-table/", views.set_table, name="set_table"),
    path("checkout/", views.checkout, name="checkout"),
    path("_debug/session/", views.debug_session, name="debug_session"),

    # الطلب
    path("order/success/<int:order_id>/", views.order_success, name="order_success"),
    path("order/status/<int:order_id>/", views.order_status, name="order_status"),

    # لوحة الأدمن
    path("panel/", admin_views.dashboard, name="admin_dashboard"),
    path("panel/order/<int:order_id>/status/", admin_views.set_status, name="admin_set_status"),
    path("panel/order/<int:order_id>/done/", admin_views.done, name="admin_done"),



]
