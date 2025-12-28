from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from .models import Category, Product, Offer, Order, OrderItem
from . import cart as cart_srv


CLOSED_STATUSES = [Order.Status.DELIVERED, Order.Status.CANCELED]


def capture_table_from_qr(request):
    t = (request.GET.get("t") or "").strip()
    if t:
        request.session["table_no"] = t
        request.session.modified = True

def ensure_cart_not_cleared_if_open(request):
    """
    ✅ إذا العميل كان عنده Order مفتوح وبعدين الأدمن سلّمه/فرّغه
    عند أول زيارة لاحقًا:
    - نمسح session cart
    - ونشيل flags
    """
    if not request.session.get("has_submitted_order"):
        return

    table_no = (request.session.get("table_no") or "").strip()
    if not table_no:
        return

    open_order_exists = Order.objects.filter(table_no=table_no).exclude(status__in=CLOSED_STATUSES).exists()
    if not open_order_exists:
        cart_srv.clear(request.session)
        request.session["has_submitted_order"] = False
        request.session.pop("order_id", None)
        request.session.modified = True




def _cart_summary(session):
    table_no = (session.get("table_no") or "").strip()
    if session.get("has_submitted_order") and table_no:
        return _db_cart_summary(table_no)

    lines, total = cart_srv.get_lines(session)
    count = sum(int(ln.qty) for ln in lines)
    return int(count), int(total)



def landing(request):
    capture_table_from_qr(request)
    ensure_cart_not_cleared_if_open(request)
    return render(request, "index.html")


def home(request):
    capture_table_from_qr(request)

    q = (request.GET.get("q") or "").strip()
    selected_cat = (request.GET.get("cat") or "all").strip()

    categories = Category.objects.filter(is_active=True).order_by("order", "name")
    offers = Offer.objects.filter(is_active=True).order_by("order", "title")[:10]

    products = Product.objects.filter(
        is_active=True,
        category__is_active=True
    ).select_related("category")

    # ✅ فلترة حسب التصنيف
    if selected_cat != "all":
        products = products.filter(category__slug=selected_cat)

    # ✅ فلترة حسب البحث
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    cart_count, cart_total = _cart_summary(request.session)

    return render(request, "home.html", {
        "categories": categories,
        "offers": offers,
        "products": products,
        "cart_count": cart_count,
        "cart_total": cart_total,
        "selected_cat": selected_cat,  # ✅ مهم للـ is-active
        "q": q,                        # ✅ مهم ليضل البحث ظاهر
    })

def product_details(request, slug: str):
    capture_table_from_qr(request)
    ensure_cart_not_cleared_if_open(request)

    product = get_object_or_404(Product, slug=slug, is_active=True)
    cart_count, cart_total = _cart_summary(request.session)
    return render(request, "product.html", {
        "product": product,
        "cart_count": cart_count,
        "cart_total": cart_total,
    })


def offers(request):
    capture_table_from_qr(request)
    ensure_cart_not_cleared_if_open(request)

    offers_qs = Offer.objects.filter(is_active=True).order_by("order", "title")
    cart_count, cart_total = _cart_summary(request.session)
    return render(request, "offers.html", {
        "offers": offers_qs,
        "cart_count": cart_count,
        "cart_total": cart_total,
    })



# ✅ صفحة تخصيص عرض ديناميكية
def offer_customize(request, slug: str):
    capture_table_from_qr(request)
    ensure_cart_not_cleared_if_open(request)

    offer = get_object_or_404(Offer, slug=slug, is_active=True)
    cart_count, cart_total = _cart_summary(request.session)
    return render(request, "offer-customize.html", {
        "offer": offer,
        "cart_count": cart_count,
        "cart_total": cart_total,
    })


def cart_page(request):
    capture_table_from_qr(request)
    ensure_cart_not_cleared_if_open(request)

    table_no = (request.session.get("table_no") or "").strip()

    # ✅ إذا في Order مفتوح بعد checkout: اعرض من DB
    if request.session.get("has_submitted_order") and table_no:
        order = _get_open_order_for_table(table_no)
        if order:
            ui_lines = []
            for it in order.items.all():
                kind = "offer" if it.item_type == OrderItem.ItemType.OFFER else "product"

                img = None
                if it.item_type == OrderItem.ItemType.PRODUCT and it.product_id:
                    if it.product and it.product.image:
                        img = it.product.image.url
                if it.item_type == OrderItem.ItemType.OFFER and it.offer_id:
                    if it.offer and it.offer.image:
                        img = it.offer.image.url

                unit = int(it.price_syp_snapshot)
                qty = int(it.qty)
                ui_lines.append({
                    "kind": kind,
                    "name": it.name_snapshot,
                    "image": img,
                    "qty": qty,
                    "unit_price": unit,
                    "line_total": unit * qty,
                    "note": it.note_snapshot,
                })

            total = sum(int(x["line_total"]) for x in ui_lines)
            if int(order.total_syp) != int(total):
                order.total_syp = int(total)
                order.save()

            return render(request, "cart.html", {
                "lines": ui_lines,
                "total": int(total),
                "table_no": table_no,
            })

    # ✅ قبل checkout: اعرض من session cart
    lines, total = cart_srv.get_lines(request.session)
    ui_lines = []

    for ln in lines:
        if ln.kind == "product":
            p: Product = ln.obj
            img = (p.image.url if p.image else None)
            ui_lines.append({
                "key": ln.key,
                "kind": "product",
                "name": p.name,
                "image": img,
                "qty": int(ln.qty),
                "unit_price": int(ln.unit_price),
                "line_total": int(ln.line_total),
                "note": ln.note,
            })
        else:
            o: Offer = ln.obj
            img = (o.image.url if o.image else None)
            ui_lines.append({
                "key": ln.key,
                "kind": "offer",
                "name": o.title,
                "image": img,
                "qty": int(ln.qty),
                "unit_price": int(ln.unit_price),
                "line_total": int(ln.line_total),
                "note": ln.note,
            })

    return render(request, "cart.html", {
        "lines": ui_lines,
        "total": int(total),
        "table_no": table_no,
    })


def debug_session(request):
    return JsonResponse(dict(request.session))


# -----------------------------
# ✅ إضافة منتج للسلة
# -----------------------------
@require_POST
def cart_add(request, slug: str):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    qty = int(request.POST.get("qty", "1") or 1)
    qty = max(1, min(qty, 50))
    cart_srv.add_product(request.session, product.id, qty)
    return redirect("cart")


# -----------------------------
# ✅ إضافة عرض للسلة مع التخصيص
# -----------------------------

@require_POST
def cart_add_offer(request, offer_id: int):
    offer = get_object_or_404(Offer, id=offer_id, is_active=True)

    qty = int(request.POST.get("qty", "1") or 1)
    qty = max(1, min(qty, 50))

    drink = (request.POST.get("drink") or "").strip()
    shisha = (request.POST.get("shisha") or "").strip()
    note = (request.POST.get("note") or "").strip()

    parts = []
    if drink: parts.append(f"مشروب: {drink}")
    if shisha: parts.append(f"أركيلة: {shisha}")
    if note: parts.append(f"ملاحظة: {note}")
    note_str = " | ".join(parts)

    cart_srv.add_offer(request.session, offer.id, qty=qty, note=note_str)
    return redirect("cart")


@require_POST
def cart_update_key(request):
    key = (request.POST.get("key") or "").strip()

    # ✅ دعم delta مثل القديم
    delta = request.POST.get("delta")
    if delta is not None:
        try:
            delta = int(delta)
        except ValueError:
            delta = 0
        current = cart_srv.get_qty(request.session, key)
        new_qty = max(0, min(current + delta, 50))
        cart_srv.set_qty_key(request.session, key, new_qty)
        return redirect("cart")

    # qty مباشر
    try:
        qty = int(request.POST.get("qty", "1") or 1)
    except ValueError:
        qty = 1
    qty = max(0, min(qty, 50))
    cart_srv.set_qty_key(request.session, key, qty)
    return redirect("cart")

# -----------------------------
# ✅ تحديث/حذف باستخدام key (يدعم المنتج والعرض)
# -----------------------------
# views.py


@require_POST
def cart_remove_key(request):
    key = (request.POST.get("key") or "").strip()
    cart_srv.remove_key(request.session, key)
    return redirect("cart")


def _get_or_create_open_order(table_no: str) -> Order:
    # آخر Order مفتوح لنفس الطاولة
    open_order = (
        Order.objects
        .filter(table_no=table_no)
        .exclude(status__in=CLOSED_STATUSES)
        .order_by("-created_at")
        .first()
    )
    if open_order:
        return open_order
    return Order.objects.create(
        table_no=table_no,
        total_syp=0,
        status=Order.Status.NEW
    )


@require_POST
def set_table(request):
    table_no = (request.POST.get("table_no") or "").strip()
    request.session["table_no"] = table_no
    request.session.modified = True
    return redirect("cart")


@require_POST
def checkout(request):
    lines, total = cart_srv.get_lines(request.session)
    if not lines:
        return redirect("cart")

    table_no = (request.POST.get("table_no") or request.session.get("table_no") or "").strip()
    note = (request.POST.get("note") or "").strip()

    if not table_no:
        return render(request, "cart.html", {
            "lines": [],
            "total": int(total),
            "table_no": request.session.get("table_no", ""),
            "error": "رقم الطاولة مطلوب لتأكيد الطلب",
        })

    with transaction.atomic():
        order = _get_or_create_open_order(table_no)

        order.note = note
        order.total_syp = int(total)
        order.save()

        # استبدال العناصر بما في السلة الحالية
        order.items.all().delete()

        items = []
        for ln in lines:
            if ln.kind == "product":
                p: Product = ln.obj
                items.append(OrderItem(
                    order=order,
                    item_type=OrderItem.ItemType.PRODUCT,
                    product=p,
                    offer=None,
                    name_snapshot=p.name,
                    price_syp_snapshot=int(p.price_syp),
                    qty=int(ln.qty),
                    note_snapshot=ln.note,
                ))
            else:
                o: Offer = ln.obj
                items.append(OrderItem(
                    order=order,
                    item_type=OrderItem.ItemType.OFFER,
                    product=None,
                    offer=o,
                    name_snapshot=o.title,
                    price_syp_snapshot=int(o.price_syp),
                    qty=int(ln.qty),
                    note_snapshot=ln.note,
                ))

        OrderItem.objects.bulk_create(items)

    request.session["table_no"] = table_no
    request.session["has_submitted_order"] = True
    request.session["order_id"] = order.id
    request.session.modified = True

    return redirect("order_status", order_id=order.id)

def _get_open_order_for_table(table_no: str):
    if not table_no:
        return None
    return (
        Order.objects
        .filter(table_no=table_no)
        .exclude(status__in=CLOSED_STATUSES)
        .order_by("-created_at")
        .first()
    )

def _db_cart_summary(table_no: str):
    o = _get_open_order_for_table(table_no)
    if not o:
        return 0, 0
    items = o.items.all()
    count = sum(int(i.qty) for i in items)
    total = sum(int(i.qty) * int(i.price_syp_snapshot) for i in items)
    if int(o.total_syp) != int(total):
        o.total_syp = int(total)
        o.save()
    return int(count), int(total)


def order_success(request, order_id: int):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "order-success.html", {"order": order})


def order_status(request, order_id: int):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "order-status.html", {"order": order})
