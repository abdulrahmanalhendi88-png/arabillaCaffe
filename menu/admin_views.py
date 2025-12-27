from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Order, OrderItem

CLOSED = [Order.Status.DELIVERED, Order.Status.CANCELED]

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
    order.save(update_fields=["status"])
    return redirect("admin_dashboard")


@staff_member_required
@require_POST
def done(request, order_id: int):
    order = get_object_or_404(Order, id=order_id)
    order.status = Order.Status.DELIVERED
    order.save(update_fields=["status"])
    return redirect("admin_dashboard")
