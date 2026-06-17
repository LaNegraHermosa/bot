from typing import List, Optional
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