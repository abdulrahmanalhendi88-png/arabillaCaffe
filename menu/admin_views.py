from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import Order, OrderItem

CLOSED = [Order.Status.DELIVERED, Order.Status.CANCELED]


def _recompute_order_total(order: Order) -> None:
    """
    يعيد حساب total_syp بناءً على عناصر الطلب الحالية
    """
    total = 0
    for it in order.items.all():
        total += int(it.price_syp_snapshot) * int(it.qty)

    order.total_syp = int(total)
    # updated_at auto_now=True، بس حفظنا بدون update_fields أفضل لتحديثه
    order.save()


@staff_member_required
def dashboard(request):
    qs = (
        Order.objects
        .exclude(status__in=CLOSED)
        .prefetch_related("items")
        .order_by("table_no", "-created_at")
    )

    latest_by_table = {}
    for o in qs:
        if o.table_no not in latest_by_table:
            latest_by_table[o.table_no] = o  # أول واحد هو الأحدث

    orders = list(latest_by_table.values())

    return render(request, "admin/admin.html", {
        "orders": orders,
        "open_orders": len(orders),
        "active_tables": len(orders),
        "max_order_id": max([o.id for o in orders], default=0),
    })


@staff_member_required
@require_POST
def set_status(request, order_id: int):
    order = get_object_or_404(Order, id=order_id)
    status = request.POST.get("status") or order.status
    order.status = status
    order.save()
    return redirect("admin_dashboard")


@staff_member_required
@require_POST
def done(request, order_id: int):
    """
    ✅ تم التنفيذ / إفراغ:
    - يسلم الطلب
    - يحذف عناصره (تفريغ السلة فعلياً)
    - يصفر الإجمالي
    """
    with transaction.atomic():
        order = get_object_or_404(Order, id=order_id)
        order.status = Order.Status.DELIVERED
        order.save()

        order.items.all().delete()
        order.total_syp = 0
        order.save()

    return redirect("admin_dashboard")


# =========================
# ✅ أزرار تعديل عناصر الطلب من الأدمن
# =========================

@staff_member_required
@require_POST
def item_inc(request, item_id: int):
    it = get_object_or_404(OrderItem, id=item_id)

    # لا تعدل إذا الطلب مغلق
    if it.order.status in CLOSED:
        return redirect("admin_dashboard")

    with transaction.atomic():
        it.qty = min(int(it.qty) + 1, 50)
        it.save(update_fields=["qty"])
        _recompute_order_total(it.order)

    return redirect("admin_dashboard")


@staff_member_required
@require_POST
def item_dec(request, item_id: int):
    it = get_object_or_404(OrderItem, id=item_id)

    if it.order.status in CLOSED:
        return redirect("admin_dashboard")

    with transaction.atomic():
        new_qty = int(it.qty) - 1
        order = it.order

        if new_qty <= 0:
            it.delete()
        else:
            it.qty = new_qty
            it.save(update_fields=["qty"])

        _recompute_order_total(order)

    return redirect("admin_dashboard")


@staff_member_required
@require_POST
def item_remove(request, item_id: int):
    it = get_object_or_404(OrderItem, id=item_id)

    if it.order.status in CLOSED:
        return redirect("admin_dashboard")

    with transaction.atomic():
        order = it.order
        it.delete()
        _recompute_order_total(order)

    return redirect("admin_dashboard")
