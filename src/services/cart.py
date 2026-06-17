from typing import Dict, List
from ..models import CartItem, Product

class CartService:
    def __init__(self):
        self.carts: Dict[int, List[CartItem]] = {}  # user_id -> cart items
    
    def add_to_cart(self, user_id: int, product: Product, quantity: int) -> List[CartItem]:
        if user_id not in self.carts:
            self.carts[user_id] = []
        
        # Verificar si ya está en el carrito
        existing_item = None
        for item in self.carts[user_id]:
            if item.product_id == product.id:
                existing_item = item
                break
        
        if existing_item:
            existing_item.quantity += quantity
            existing_item.subtotal = existing_item.quantity * existing_item.price
        else:
            self.carts[user_id].append(CartItem(
                product_id=product.id,
                quantity=quantity,
                product_name=product.name,
                price=product.price,
                subtotal=product.price * quantity
            ))
        
        return self.carts[user_id]
    
    def get_cart(self, user_id: int) -> List[CartItem]:
        return self.carts.get(user_id, [])
    
    def clear_cart(self, user_id: int) -> None:
        self.carts[user_id] = []
    
    def calculate_total(self, user_id: int) -> float:
        cart = self.get_cart(user_id)
        return sum(item.subtotal for item in cart)

cart_service = CartService()