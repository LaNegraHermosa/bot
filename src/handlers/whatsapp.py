from twilio.twiml.messaging_response import MessagingResponse
from fastapi import Request, Response
from typing import Dict, List
from ..services.database import DatabaseService
from ..services.cart import cart_service

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
        products = DatabaseService.get_products()
        
        if not products:
            return "No hay productos disponibles en este momento."
        
        message = "📦 *Productos Disponibles:*\n\n"
        for p in products[:10]:
            message += f"*{p.id}*. {p.name} - ${p.price}\n"
        
        return message + "\nResponde *agregar [id]* para agregar al carrito"
    
    async def _add_product(self, message: str, phone: str) -> str:
        try:
            # Extraer ID del mensaje
            parts = message.replace("+", "agregar").split()
            product_id = int(parts[1])
            product = DatabaseService.get_product(product_id)
            
            if not product:
                return "❌ Producto no encontrado"
            
            # Obtener o crear cliente
            customer = DatabaseService.get_or_create_customer(phone=phone, name="Cliente WhatsApp")
            cart_service.add_to_cart(customer.id, product, 1)
            
            return f"✅ *{product.name}* agregado al carrito\n\n" \
                   f"Usa *carrito* para ver tu pedido"
        except (IndexError, ValueError):
            return "❓ Formato: *agregar [id]* (ej: agregar 1)"
    
    async def _view_cart(self, phone: str) -> str:
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
    
    async def _checkout(self, phone: str) -> str:
        customer = DatabaseService.get_or_create_customer(phone=phone, name="Cliente WhatsApp")
        cart = cart_service.get_cart(customer.id)
        
        if not cart:
            return "🛒 Tu carrito está vacío. Usa *productos* para agregar artículos."
        
        total = cart_service.calculate_total(customer.id)
        
        # Crear orden
        order = DatabaseService.create_order(customer_id=customer.id, total=total)
        
        # Actualizar stock
        for item in cart:
            prod = DatabaseService.get_product(item.product_id)
            if prod:
                DatabaseService.update_stock(item.product_id, prod.stock - item.quantity)
        
        cart_service.clear_cart(customer.id)
        
        return f"✅ *¡Pedido #{order.id} creado!*\n\n" \
               f"Total: ${total}\n" \
               "Nos pondremos en contacto contigo pronto."

# Instancia única
whatsapp_handler = WhatsAppHandler()