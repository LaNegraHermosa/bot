import logging
from ..services.database import DatabaseService
from ..services.cart import cart_service
from ..models import OrderItem
from ..config import settings

logger = logging.getLogger(__name__)

class WhatsAppHandler:
    def __init__(self):
        self.user_states: dict = {}

    def _resolve_customer(self, phone: str) -> int:
        c = DatabaseService.get_or_create_customer(phone=phone, name="Cliente WhatsApp")
        return c.id

    async def handle_message(self, phone: str, message: str) -> str:
        if not settings.WHATSAPP_ENABLED:
            return "❌ WhatsApp desactivado. Usa Telegram."
        ml = message.lower().strip()
        if ml in ["hola", "hello", "inicio", "/start"]:
            return self._welcome_message()
        if ml in ["productos", "ver productos", "catalogo"]:
            return await self._list_products()
        if ml in ["carrito", "ver carrito", "cart"]:
            return await self._view_cart(phone)
        if ml.startswith("agregar") or ml.startswith("+"):
            return await self._add_product(ml, phone)
        if ml in ["confirmar", "checkout"]:
            return await self._checkout(phone)
        return "❓ No entendí. Usa: *productos*, *carrito*, *agregar [id]*, *confirmar*"

    def _welcome_message(self) -> str:
        return "¡Hola! Bienvenido.\n\n• *productos* - Catálogo\n• *carrito* - Tu carrito\n• *agregar [id]* - Agregar\n• *confirmar* - Finalizar"

    async def _list_products(self) -> str:
        try:
            prods = DatabaseService.get_products()
        except Exception:
            return "❌ Error al cargar productos."
        if not prods:
            return "No hay productos disponibles."
        return "📦 *Productos:*\n\n" + "\n".join(f"*{p.id}*. {p.name} - ${p.price}" for p in prods[:10]) + "\n\nResponde *agregar [id]*"

    async def _add_product(self, msg: str, phone: str) -> str:
        try:
            pid = int(msg.replace("+", "agregar").split()[1])
        except (IndexError, ValueError):
            return "❓ Formato: *agregar [id]*"
        try:
            product = DatabaseService.get_product(pid)
        except Exception:
            return "❌ Error al buscar producto."
        if not product:
            return "❌ Producto no encontrado."
        if product.stock < 1:
            return "❌ Producto sin stock."
        customer_id = self._resolve_customer(phone)
        try:
            cart_service.add_to_cart(customer_id, pid, 1)
            return f"✅ *{product.name}* agregado.\nUsa *carrito* para ver."
        except Exception as e:
            logger.error(f"Error al agregar: {e}")
            return "❌ Error al agregar."

    async def _view_cart(self, phone: str) -> str:
        try:
            customer_id = self._resolve_customer(phone)
            cart = cart_service.get_cart(customer_id)
        except Exception:
            return "❌ Error al cargar carrito."
        if not cart:
            return "🛒 Carrito vacío. Usa *productos*."
        total = sum(i.subtotal for i in cart)
        msg = "🛒 *Carrito:*\n\n" + "\n".join(f"• {i.product_name} x{i.quantity} - ${i.subtotal}" for i in cart)
        return msg + f"\n\n💵 *Total: ${total}*\n\nResponde *confirmar*"

    async def _checkout(self, phone: str) -> str:
        customer_id = self._resolve_customer(phone)
        cart = cart_service.get_cart(customer_id)
        if not cart:
            return "🛒 Carrito vacío."
        try:
            total = cart_service.calculate_total(customer_id)
            order = DatabaseService.create_order(customer_id=customer_id, total=total)
            items = [OrderItem(order_id=order.id, product_id=i.product_id, quantity=i.quantity, price=i.price) for i in cart]
            DatabaseService.add_order_items(order.id, items)
            for i in cart:
                if not DatabaseService.atomic_decrement_stock(i.product_id, i.quantity):
                    logger.warning(f"Stock insuficiente #{order.id} producto {i.product_id}")
            cart_service.clear_cart(customer_id)
            logger.info(f"Pedido #{order.id} WhatsApp ${total}")
            return f"✅ *Pedido #{order.id} creado!*\nTotal: ${total}\nNos pondremos en contacto."
        except Exception as e:
            logger.error(f"Error checkout: {e}")
            return "❌ Error al procesar."

whatsapp_handler = WhatsAppHandler()
