from typing import List
from ..services.database import DatabaseService
from ..models import CartItem

class CartService:

    def add_to_cart(self, customer_id: int, product_id: int, quantity: int) -> bool:
        try:
            existing = DatabaseService.get_cart_item(customer_id, product_id)
            if existing:
                new_qty = existing["quantity"] + quantity
                DatabaseService.update_cart_item(customer_id, product_id, new_qty)
            else:
                DatabaseService.insert_cart_item(customer_id, product_id, quantity)
            return True
        except Exception as e:
            raise RuntimeError(f"Error adding to cart: {e}")

    def get_cart(self, customer_id: int) -> List[CartItem]:
        return DatabaseService.get_cart_items(customer_id)

    def clear_cart(self, customer_id: int) -> None:
        DatabaseService.clear_cart(customer_id)

    def calculate_total(self, customer_id: int) -> float:
        cart = self.get_cart(customer_id)
        return sum(item.subtotal for item in cart)

cart_service = CartService()
