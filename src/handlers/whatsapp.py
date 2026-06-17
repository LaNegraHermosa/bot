import logging
from typing import Dict
from ..services.database import DatabaseService
from ..services.cart import cart_service
from ..models import OrderItem

logger = logging.getLogger(__name__)

class WhatsAppHandler:
    def __init__(self):
        self.user_states: Dict[str, str] = {}  # phone -> current_state
    
    async def handle_message(self, phone: str, message: str) -> str:
        message_lower = message.lower().strip()
        
        # Comandos básicos
        if message_lower in ["hola", "hello", "inicio", "/start"]:
            return self._welcome_message()
        
        if message_lower in ["productos", "ver productos", "catalogo"]:
            return await self._list_products()
        
        if message_lower in ["carrito", "ver carrito", "cart"]:
            return await self._view_cart(phone)
        
        if message_lower.startswith("agregar") or message_lower.startswith("+"):
            return await self._add_product(message_lower, phone)
        
        if message_lower in ["confirmar", "checkout"]:
            return await self._checkout(phone)
        
        return "❓ No entendí tu mensaje. Usa:\n" \
               "*productos* - Ver catálogo\n" \
               "*carrito* - Ver tu carrito\n" \
               "*agregar [id]* - Agregar producto\n" \
               "*confirmar* - Finalizar pedido"
    
    def _welcome_message(self) -> str:
        return "¡Hola! 👋 Bienvenido a nuestra tienda.\n\n" \
               "Comandos disponibles:\n" \
               "• *productos* - Ver catálogo\n" \
               "• *carrito* - Ver tu carrito\n" \
               "• *agregar [id]* - Agregar producto (ej: agregar 1)\n" \
               "• *confirmar* - Finalizar pedido"
    
    async def _list_products(self) -> str:
        try:
            products = DatabaseService.get_products()
        except Exception as e:
            logger.error(f"Error al listar productos: {e}")
            return "❌ Error al cargar productos. Intenta más tarde."
        
        if not products:
            return "No hay productos disponibles en este momento."
        
        message = "📦 *Productos Disponibles:*\n\n"
        for p in products[:10]:
            message += f"*{p.id}*. {p.name} - ${p.price}\n"
        
        return message + "\nResponde *agregar [id]* para agregar al carrito"
    
    async def _add_product(self, message: str, phone: str) -> str:
        try:
            parts = message.replace("+", "agregar").split()
            product_id = int(parts[1])
        except (IndexError, ValueError):
            return "❓ Formato: *agregar [id]* (ej: agregar 1)"
        
        try:
            product = DatabaseService.get_product(product_id)
            
            if not product:
                return "❌ Producto no encontrado"
            
            customer = DatabaseService.get_or_create_customer(phone=phone, name="Cliente WhatsApp")
            cart_service.add_to_cart(customer.id, product, 1)
            
            return f"✅ *{product.name}* agregado al carrito\n\n" \
                   f"Usa *carrito* para ver tu pedido"
        except Exception as e:
            logger.error(f"Error al agregar producto: {e}")
            return "❌ Error al agregar producto. Intenta más tarde."

    async def _view_cart(self, phone: str) -> str:
        try:
            customer = DatabaseService.get_or_create_customer(phone=phone, name="Cliente WhatsApp")
            cart = cart_service.get_cart(customer.id)
            
            if not cart:
                return "🛒 Tu carrito está vacío.\n\nUsa *productos* para ver el catálogo"
            
            message = "🛒 *Tu Carrito:*\n\n"
            total = 0
            for item in cart:
                message += f"• {item.product_name} x{item.quantity} - ${item.subtotal}\n"
                total += item.subtotal
            
            message += f"\n💵 *Total: ${total}*\n\n"
            message += "Responde *confirmar* para finalizar el pedido"
            
            return message
        except Exception as e:
            logger.error(f"Error al ver carrito: {e}")
            return "❌ Error al cargar carrito. Intenta más tarde."
    
    async def _checkout(self, phone: str) -> str:
        try:
            customer = DatabaseService.get_or_create_customer(phone=phone, name="Cliente WhatsApp")
            cart = cart_service.get_cart(customer.id)
            
            if not cart:
                return "🛒 Tu carrito está vacío. Usa *productos* para agregar artículos."
            
            total = cart_service.calculate_total(customer.id)
            
            order = DatabaseService.create_order(customer_id=customer.id, total=total)
            
            items_to_save = [
                OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=item.price)
                for item in cart
            ]
            DatabaseService.add_order_items(order.id, items_to_save)
            
            for item in cart:
                ok = DatabaseService.atomic_decrement_stock(item.product_id, item.quantity)
                if not ok:
                    logger.warning(f"Stock insuficiente para producto {item.product_id} en pedido #{order.id}")
            
            cart_service.clear_cart(customer.id)
            
            logger.info(f"Pedido #{order.id} creado vía WhatsApp ({customer.name}) - ${total}")
            
            return f"✅ *¡Pedido #{order.id} creado!*\n\n" \
                   f"Total: ${total}\n" \
                   "Nos pondremos en contacto contigo pronto."
        except Exception as e:
            logger.error(f"Error en checkout: {e}")
            return "❌ Error al procesar pedido. Intenta más tarde."

# Instancia única
whatsapp_handler = WhatsAppHandler()