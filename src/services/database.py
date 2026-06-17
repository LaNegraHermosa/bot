from typing import List, Optional
from datetime import datetime
from ..database import supabase_client
from ..models import Product, Customer, Order, OrderItem

class DatabaseService:
    # PRODUCTOS
    @staticmethod
    def get_products(category: Optional[str] = None, active_only: bool = True) -> List[Product]:
        query = supabase_client.table("products").select("*")
        if active_only:
            query = query.eq("active", True)
        if category:
            query = query.eq("category", category)
        query = query.order("id")
        response = query.execute()
        return [Product(**p) for p in response.data]
    
    @staticmethod
    def get_product(product_id: int) -> Optional[Product]:
        response = supabase_client.table("products").select("*").eq("id", product_id).execute()
        if response.data:
            return Product(**response.data[0])
        return None
    
    @staticmethod
    def create_product(product: Product) -> Product:
        response = supabase_client.table("products").insert(product.model_dump(exclude={"id"})).execute()
        return Product(**response.data[0])
    
    @staticmethod
    def update_stock(product_id: int, new_stock: int) -> bool:
        response = supabase_client.table("products").update({"stock": new_stock}).eq("id", product_id).execute()
        return len(response.data) > 0
    
    # CLIENTES
    @staticmethod
    def get_or_create_customer(telegram_id: Optional[int] = None, phone: Optional[str] = None, name: str = "") -> Customer:
        query = supabase_client.table("customers").select("*")
        if telegram_id:
            query = query.eq("telegram_id", telegram_id)
        elif phone:
            query = query.eq("phone", phone)
        
        response = query.execute()
        if response.data:
            return Customer(**response.data[0])
        
        # Crear nuevo cliente
        customer_data = {"name": name}
        if telegram_id:
            customer_data["telegram_id"] = telegram_id
        if phone:
            customer_data["phone"] = phone
            
        response = supabase_client.table("customers").insert(customer_data).execute()
        return Customer(**response.data[0])
    
    @staticmethod
    def get_customer_by_id(customer_id: int) -> Optional[Customer]:
        response = supabase_client.table("customers").select("*").eq("id", customer_id).execute()
        if response.data:
            return Customer(**response.data[0])
        return None
    
    # ORDENES
    @staticmethod
    def create_order(customer_id: int, total: float, notes: Optional[str] = None) -> Order:
        order_data = {
            "customer_id": customer_id,
            "total": total,
            "status": "pending",
            "notes": notes
        }
        response = supabase_client.table("orders").insert(order_data).execute()
        return Order(**response.data[0])
    
    @staticmethod
    def add_order_items(order_id: int, items: List[OrderItem]) -> List[OrderItem]:
        items_data = [item.model_dump(exclude={"id"}) for item in items]
        response = supabase_client.table("order_items").insert(items_data).execute()
        return [OrderItem(**item) for item in response.data]
    
    @staticmethod
    def get_order(order_id: int) -> Optional[Order]:
        response = supabase_client.table("orders").select("*").eq("id", order_id).execute()
        if response.data:
            return Order(**response.data[0])
        return None
    
    @staticmethod
    def update_order_status(order_id: int, status: str) -> bool:
        response = supabase_client.table("orders").update({
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", order_id).execute()
        return len(response.data) > 0
    
    # ADMIN
    @staticmethod
    def get_all_orders() -> list:
        response = supabase_client.table("orders").select("*").order("id", desc=True).limit(50).execute()
        orders = response.data
        for o in orders:
            customer = supabase_client.table("customers").select("name").eq("id", o["customer_id"]).execute()
            o["customer_name"] = customer.data[0]["name"] if customer.data else "—"
        return orders
    
    @staticmethod
    def get_admin_stats() -> dict:
        orders = supabase_client.table("orders").select("*").execute()
        customers = supabase_client.table("customers").select("id", count="exact").execute()
        products = supabase_client.table("products").select("id", count="exact").execute()
        
        total_revenue = sum(o.get("total", 0) for o in orders.data if o.get("status") != "cancelled")
        pending = sum(1 for o in orders.data if o.get("status") == "pending")
        
        return {
            "total_orders": len(orders.data),
            "pending_orders": pending,
            "total_customers": customers.count if hasattr(customers, 'count') else len(customers.data),
            "total_products": products.count if hasattr(products, 'count') else len(products.data),
            "total_revenue": round(total_revenue, 2),
        }