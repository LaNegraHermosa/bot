import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from ..services.database import DatabaseService
from ..services.cart import cart_service
from ..models import OrderItem

logger = logging.getLogger(__name__)

def _resolve_customer(update: Update) -> int:
    user = update.effective_user
    c = DatabaseService.get_or_create_customer(
        telegram_id=user.id,
        name=user.first_name or "Cliente"
    )
    return c.id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        _resolve_customer(update)
    except Exception as e:
        logger.error(f"Error al registrar usuario: {e}")

    keyboard = [
        [InlineKeyboardButton("🛍 Ver Productos", callback_data="view_products")],
        [InlineKeyboardButton("🛒 Mi Carrito", callback_data="view_cart")],
        [InlineKeyboardButton("📋 Mis Pedidos", callback_data="view_orders")]
    ]
    await update.message.reply_text(
        f"¡Hola {user.first_name}! Bienvenido a nuestra tienda.\n"
        "Usa los botones de abajo para navegar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def view_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        products = DatabaseService.get_products()
    except Exception as e:
        logger.error(f"Error al obtener productos: {e}")
        await update.callback_query.edit_message_text("Error al cargar productos. Intenta de nuevo.")
        return
    if not products:
        await update.callback_query.edit_message_text("No hay productos disponibles en este momento.")
        return
    keyboard = [[InlineKeyboardButton(f"{p.name} - ${p.price}", callback_data=f"product_{p.id}")] for p in products[:10]]
    keyboard.append([InlineKeyboardButton("🛒 Ver Carrito", callback_data="view_cart")])
    await update.callback_query.edit_message_text(
        "📦 **Productos Disponibles:**\nSelecciona un producto:",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        product_id = int(update.callback_query.data.split("_")[1])
        product = DatabaseService.get_product(product_id)
    except Exception as e:
        logger.error(f"Error al cargar producto: {e}")
        await update.callback_query.edit_message_text("Error al cargar producto.")
        return
    if not product:
        await update.callback_query.edit_message_text("Producto no encontrado.")
        return
    keyboard = [
        [InlineKeyboardButton("➕ Agregar al Carrito", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton("🔙 Volver", callback_data="view_products")]
    ]
    msg = f"*{product.name}*\n\n{product.description}\n\n💰 Precio: ${product.price}\n📦 Stock: {product.stock}"
    if product.image_url:
        try:
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(media=product.image_url, caption=msg, parse_mode="Markdown"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        except Exception as e:
            logger.warning(f"No se pudo enviar imagen: {e}")
    await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, customer_id: int = None):
    if customer_id is None:
        try:
            customer_id = _resolve_customer(update)
        except Exception as e:
            logger.error(f"Error al resolver cliente: {e}")
            await update.callback_query.edit_message_text("❌ Error al cargar tu información.")
            return
    cart = cart_service.get_cart(customer_id)
    if not cart:
        await update.callback_query.edit_message_text(
            "🛒 Tu carrito está vacío.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍 Ver Productos", callback_data="view_products")]])
        )
        return
    total = sum(i.subtotal for i in cart)
    msg = "🛒 **Tu Carrito:**\n\n" + "\n".join(f"• {i.product_name} x{i.quantity} - ${i.subtotal}" for i in cart)
    msg += f"\n\n💵 **Total: ${total}**"
    keyboard = [
        [InlineKeyboardButton("💳 Confirmar Pedido", callback_data="checkout")],
        [InlineKeyboardButton("🗑 Vaciar Carrito", callback_data="clear_cart")],
        [InlineKeyboardButton("🛍 Seguir Comprando", callback_data="view_products")]
    ]
    await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = int(update.callback_query.data.split("_")[1])
    try:
        product = DatabaseService.get_product(product_id)
    except Exception as e:
        logger.error(f"Error al obtener producto: {e}")
        await update.callback_query.answer("Error al cargar producto", show_alert=True)
        return
    if not product:
        await update.callback_query.answer("Producto no encontrado", show_alert=True)
        return
    if product.stock < 1:
        await update.callback_query.answer("❌ Producto sin stock disponible", show_alert=True)
        return
    try:
        customer_id = _resolve_customer(update)
    except Exception as e:
        logger.error(f"Error al resolver cliente: {e}")
        await update.callback_query.answer("Error al cargar tu información", show_alert=True)
        return
    cart = cart_service.get_cart(customer_id)
    cart_qty = sum(i.quantity for i in cart if i.product_id == product_id)
    if cart_qty + 1 > product.stock:
        await update.callback_query.answer(f"❌ Stock máximo alcanzado ({product.stock} unidades)", show_alert=True)
        return
    try:
        cart_service.add_to_cart(customer_id, product_id, 1)
        await update.callback_query.answer(f"✅ {product.name} agregado al carrito", show_alert=False)
    except Exception as e:
        logger.error(f"Error al agregar al carrito: {e}")
        await update.callback_query.answer("Error al procesar el carrito", show_alert=True)

async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        customer_id = _resolve_customer(update)
        orders = DatabaseService.get_customer_orders(customer_id)
    except Exception as e:
        logger.error(f"Error al obtener pedidos: {e}")
        await update.callback_query.edit_message_text("Error al cargar tus pedidos.")
        return
    if not orders:
        await update.callback_query.edit_message_text(
            "📋 No tienes pedidos aún.\n\nUsa *Ver Productos* para hacer tu primer pedido.", parse_mode="Markdown"
        )
        return
    msg = "📋 **Tus Pedidos:**\n\n" + "\n".join(f"• #{o['id']} - ${o['total']} - *{o['status']}*" for o in orders[:5])
    await update.callback_query.edit_message_text(msg + "\n\nUsa /start para volver al menú principal.")

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        customer_id = _resolve_customer(update)
    except Exception as e:
        logger.error(f"Error al resolver cliente: {e}")
        await update.callback_query.edit_message_text("❌ Error al cargar tu información.")
        return
    cart = cart_service.get_cart(customer_id)
    if not cart:
        await update.callback_query.answer("El carrito está vacío", show_alert=True)
        return
    try:
        for i in cart:
            product = DatabaseService.get_product(i.product_id)
            if not product or product.stock < i.quantity:
                await update.callback_query.edit_message_text(
                    f"❌ Stock insuficiente para *{i.product_name}*. Quedan {product.stock if product else 0} unidades.",
                    parse_mode="Markdown"
                )
                return
        total = cart_service.calculate_total(customer_id)
        order = DatabaseService.create_order(customer_id=customer_id, total=total)
        items = [OrderItem(order_id=order.id, product_id=i.product_id, quantity=i.quantity, price=i.price) for i in cart]
        DatabaseService.add_order_items(order.id, items)
        for i in cart:
            DatabaseService.atomic_decrement_stock(i.product_id, i.quantity)
        cart_service.clear_cart(customer_id)
        logger.info(f"Pedido #{order.id} creado (${total})")
        await update.callback_query.edit_message_text(
            f"✅ **Pedido #{order.id} creado exitosamente!**\n\nTotal: ${total}\nEstado: Pendiente\n\nNos pondremos en contacto contigo pronto.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error al crear pedido: {e}")
        await update.callback_query.edit_message_text("❌ Ocurrió un error al procesar tu pedido.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    handlers = {
        "view_products": view_products,
        "view_cart": view_cart,
        "view_orders": view_orders,
        "checkout": checkout,
    }
    if q.data in handlers:
        await handlers[q.data](update, context)
    elif q.data.startswith("product_"):
        await show_product(update, context)
    elif q.data.startswith("add_"):
        await add_to_cart(update, context)
    elif q.data == "clear_cart":
        try:
            customer_id = _resolve_customer(update)
        except Exception as e:
            logger.error(f"Error al resolver cliente: {e}")
            await q.edit_message_text("❌ Error al vaciar carrito.")
            return
        cart_service.clear_cart(customer_id)
        await view_cart(update, context, customer_id=customer_id)

def setup_telegram_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))

async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Usa /start para ver el menú principal o los botones de navegación.")
