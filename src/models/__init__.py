from pydantic import BaseModel
from typing import Optional

class Product(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    price: float
    stock: int
    category: Optional[str] = None
    image_url: Optional[str] = None
    active: bool = True

class Customer(BaseModel):
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    phone: Optional[str] = None
    name: str
    email: Optional[str] = None

class Order(BaseModel):
    id: Optional[int] = None
    customer_id: int
    total: float
    status: str
    notes: Optional[str] = None

class OrderItem(BaseModel):
    id: Optional[int] = None
    order_id: int
    product_id: int
    quantity: int
    price: float

class CartItem(BaseModel):
    product_id: int
    quantity: int
    product_name: str
    price: float
    subtotal: float
