# menu/cart.py
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple
from .models import Product, Offer

SESSION_KEY = "cart_items"

@dataclass
class CartLine:
    key: str          # "p:12" or "o:3"
    kind: str         # "product" or "offer"
    obj: object       # Product أو Offer
    qty: int
    unit_price: int
    name: str
    note: str = ""

    @property
    def line_total(self) -> int:
        return int(self.unit_price) * int(self.qty)


def _get_raw_cart(session) -> Dict[str, dict]:
    """
    {
      "p:12": {"qty": 2, "note": ""},
      "o:3":  {"qty": 1, "note": "مشروب: ... | أركيلة: ..."}
    }
    """
    cart = session.get(SESSION_KEY)
    if not isinstance(cart, dict):
        cart = {}
        session[SESSION_KEY] = cart
    return cart


def add_product(session, product_id: int, qty: int = 1, note: str = "") -> None:
    cart = _get_raw_cart(session)
    key = f"p:{int(product_id)}"
    row = cart.get(key) or {"qty": 0, "note": ""}
    row["qty"] = int(row.get("qty", 0)) + int(qty)
    if note:
        row["note"] = note
    cart[key] = row
    session.modified = True


def add_offer(session, offer_id: int, qty: int = 1, note: str = "") -> None:
    cart = _get_raw_cart(session)
    key = f"o:{int(offer_id)}"
    row = cart.get(key) or {"qty": 0, "note": ""}
    row["qty"] = int(row.get("qty", 0)) + int(qty)
    if note:
        row["note"] = note
    cart[key] = row
    session.modified = True


def get_qty(session, key: str) -> int:
    cart = _get_raw_cart(session)
    row = cart.get(key) or {}
    return int(row.get("qty", 0))


def set_qty_key(session, key: str, qty: int) -> None:
    cart = _get_raw_cart(session)
    qty = int(qty)
    if qty <= 0:
        cart.pop(key, None)
    else:
        row = cart.get(key) or {"qty": 0, "note": ""}
        row["qty"] = qty
        cart[key] = row
    session.modified = True


def remove_key(session, key: str) -> None:
    cart = _get_raw_cart(session)
    cart.pop(key, None)
    session.modified = True


def clear(session) -> None:
    session.pop(SESSION_KEY, None)
    session.pop("has_submitted_order", None)
    session.modified = True


def get_lines(session) -> Tuple[Iterable[CartLine], int]:
    cart = _get_raw_cart(session)
    if not cart:
        return [], 0

    product_ids = []
    offer_ids = []

    for k in cart.keys():
        if k.startswith("p:"):
            product_ids.append(int(k.split(":")[1]))
        elif k.startswith("o:"):
            offer_ids.append(int(k.split(":")[1]))

    products_map = {p.id: p for p in Product.objects.filter(id__in=product_ids, is_active=True)}
    offers_map = {o.id: o for o in Offer.objects.filter(id__in=offer_ids, is_active=True)}

    lines: list[CartLine] = []
    total = 0

    for key, row in cart.items():
        qty = int(row.get("qty", 1))
        note = (row.get("note") or "").strip()

        if key.startswith("p:"):
            pid = int(key.split(":")[1])
            p = products_map.get(pid)
            if not p:
                continue
            line = CartLine(
                key=key,
                kind="product",
                obj=p,
                qty=qty,
                unit_price=int(p.price_syp),
                name=p.name,
                note=note,
            )
        else:
            oid = int(key.split(":")[1])
            o = offers_map.get(oid)
            if not o:
                continue
            line = CartLine(
                key=key,
                kind="offer",
                obj=o,
                qty=qty,
                unit_price=int(o.price_syp),
                name=o.title,
                note=note,
            )

        lines.append(line)
        total += line.line_total

    return lines, int(total)
