from typing import List, Optional
from ..database import get_supabase_client
from ..models import Product, Customer, Order, OrderItem, CartItem

def _db():
    return get_supabase_client()


class DatabaseService:

    # ── PRODUCTOS ──────────────────────────────────

    @staticmethod
    def get_products(category: Optional[str] = None, active_only: bool = True) -> List[Product]:
        query = _db().table("products").select("*")
        if active_only:
            query = query.eq("active", True)
        if category:
            query = query.eq("category", category)
        query = query.order("id")
        return [Product(**p) for p in query.execute().data]

    @staticmethod
    def get_product(product_id: int) -> Optional[Product]:
        resp = _db().table("products").select("*").eq("id", product_id).execute()
        return Product(**resp.data[0]) if resp.data else None

    @staticmethod
    def update_stock(product_id: int, new_stock: int) -> bool:
        resp = _db().table("products").update({"stock": new_stock}).eq("id", product_id).execute()
        return len(resp.data) > 0

    @staticmethod
    def atomic_decrement_stock(product_id: int, quantity: int) -> bool:
        resp = _db().rpc("atomic_decrement_stock", {
            "p_product_id": product_id,
            "p_quantity": quantity
        }).execute()
        return bool(resp.data)

    # ── CLIENTES ───────────────────────────────────

    @staticmethod
    def get_or_create_customer(telegram_id: Optional[int] = None, phone: Optional[str] = None, name: str = "") -> Customer:
        query = _db().table("customers").select("*")
        if telegram_id:
            query = query.eq("telegram_id", telegram_id)
        elif phone:
            query = query.eq("phone", phone)
        resp = query.execute()
        if resp.data:
            return Customer(**resp.data[0])
        data = {"name": name}
        if telegram_id:
            data["telegram_id"] = telegram_id
        if phone:
            data["phone"] = phone
        resp = _db().table("customers").insert(data).execute()
        return Customer(**resp.data[0])

    @staticmethod
    def get_customer_by_id(customer_id: int) -> Optional[Customer]:
        resp = _db().table("customers").select("*").eq("id", customer_id).execute()
        return Customer(**resp.data[0]) if resp.data else None

    # ── CARRITO (DB persistente) ───────────────────

    @staticmethod
    def get_cart_item(customer_id: int, product_id: int) -> Optional[dict]:
        resp = _db().table("carts").select("*") \
            .eq("customer_id", customer_id) \
            .eq("product_id", product_id) \
            .execute()
        return resp.data[0] if resp.data else None

    @staticmethod
    def insert_cart_item(customer_id: int, product_id: int, quantity: int) -> None:
        _db().table("carts").insert({
            "customer_id": customer_id,
            "product_id": product_id,
            "quantity": quantity
        }).execute()

    @staticmethod
    def update_cart_item(customer_id: int, product_id: int, quantity: int) -> None:
        _db().table("carts").update({"quantity": quantity}) \
            .eq("customer_id", customer_id) \
            .eq("product_id", product_id) \
            .execute()

    @staticmethod
    def get_cart_items(customer_id: int) -> List[CartItem]:
        resp = _db().table("carts").select("product_id, quantity, products!inner(name, price)") \
            .eq("customer_id", customer_id) \
            .execute()
        items = []
        for row in resp.data:
            product = row.get("products")
            if not product:
                continue
            price = float(product["price"])
            qty = row["quantity"]
            items.append(CartItem(
                product_id=row["product_id"],
                quantity=qty,
                product_name=product["name"],
                price=price,
                subtotal=round(price * qty, 2)
            ))
        return items

    @staticmethod
    def clear_cart(customer_id: int) -> None:
        _db().table("carts").delete().eq("customer_id", customer_id).execute()

    # ── ÓRDENES ────────────────────────────────────

    @staticmethod
    def create_order(customer_id: int, total: float, notes: Optional[str] = None) -> Order:
        data = {"customer_id": customer_id, "total": total, "status": "pending"}
        if notes:
            data["notes"] = notes
        resp = _db().table("orders").insert(data).execute()
        return Order(**resp.data[0])

    @staticmethod
    def add_order_items(order_id: int, items: List[OrderItem]) -> List[OrderItem]:
        data = [i.model_dump(exclude={"id"}) for i in items]
        resp = _db().table("order_items").insert(data).execute()
        return [OrderItem(**r) for r in resp.data]

    @staticmethod
    def get_order(order_id: int) -> Optional[Order]:
        resp = _db().table("orders").select("*").eq("id", order_id).execute()
        return Order(**resp.data[0]) if resp.data else None

    @staticmethod
    def get_customer_orders(customer_id: int) -> list:
        resp = _db().table("orders").select("id, total, status, created_at") \
            .eq("customer_id", customer_id) \
            .order("id", desc=True).limit(10).execute()
        return resp.data or []

    @staticmethod
    def update_order_status(order_id: int, status: str) -> bool:
        resp = _db().table("orders").update({"status": status}).eq("id", order_id).execute()
        return len(resp.data) > 0

    # ── ADMIN ──────────────────────────────────────

    @staticmethod
    def get_all_orders() -> list:
        resp = _db().table("orders").select("id, customer_id, total, status, created_at, customers(name)") \
            .order("id", desc=True).limit(50).execute()
        for o in resp.data:
            o["customer_name"] = o.pop("customers", {}).get("name", "—") if o.get("customers") else "—"
        return resp.data

    @staticmethod
    def get_admin_stats() -> dict:
        orders = _db().table("orders").select("*").execute()
        customers = _db().table("customers").select("id", count="exact").execute()
        products = _db().table("products").select("id", count="exact").execute()
        total_revenue = sum(o.get("total", 0) for o in orders.data if o.get("status") != "cancelled")
        pending = sum(1 for o in orders.data if o.get("status") == "pending")
        return {
            "total_orders": len(orders.data),
            "pending_orders": pending,
            "total_customers": getattr(customers, 'count', len(customers.data)),
            "total_products": getattr(products, 'count', len(products.data)),
            "total_revenue": round(total_revenue, 2),
        }
