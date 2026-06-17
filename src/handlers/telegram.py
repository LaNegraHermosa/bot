import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from ..services.database import DatabaseService
from ..services.cart import cart_service
from ..models import OrderItem

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        DatabaseService.get_or_create_customer(
            telegram_id=update.effective_user.id,
            name=user.first_name or "Cliente"
        )
    except Exception as e:
        logger.error(f"Error al registrar usuario: {e}")

    keyboard = [
        [InlineKeyboardButton("🛍 Ver Productos", callback_data="view_products")],
        [InlineKeyboardButton("🛒 Mi Carrito", callback_data="view_cart")],
        [InlineKeyboardButton("📋 Mis Pedidos", callback_data="view_orders")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"¡Hola {user.first_name}! Bienvenido a nuestra tienda.\n"
        "Usa los botones de abajo para navegar:",
        reply_markup=reply_markup
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

    keyboard = []
    for product in products[:10]:
        keyboard.append([InlineKeyboardButton(
            f"{product.name} - ${product.price}",
            callback_data=f"product_{product.id}"
        )])

    keyboard.append([InlineKeyboardButton("🛒 Ver Carrito", callback_data="view_cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        "📦 **Productos Disponibles:**\nSelecciona un producto:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        product_id = int(update.callback_query.data.split("_")[1])
        product = DatabaseService.get_product(product_id)
    except Exception as e:
        logger.error(f"Error al obtener producto: {e}")
        await update.callback_query.edit_message_text("Error al cargar producto.")
        return

    if not product:
        await update.callback_query.edit_message_text("Producto no encontrado.")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Agregar al Carrito", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton("🔙 Volver", callback_data="view_products")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = f"*{product.name}*\n\n{product.description}\n\n💰 Precio: ${product.price}\n📦 Stock: {product.stock}"

    if product.image_url:
        try:
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(
                    media=product.image_url,
                    caption=message,
                    parse_mode="Markdown"
                ),
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"No se pudo enviar imagen: {e}")
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = cart_service.get_cart(user_id)

    if not cart:
        await update.callback_query.edit_message_text(
            "🛒 Tu carrito está vacío.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍 Ver Productos", callback_data="view_products")]])
        )
        return

    message = "🛒 **Tu Carrito:**\n\n"
    total = 0
    for item in cart:
        message += f"• {item.product_name} x{item.quantity} - ${item.subtotal}\n"
        total += item.subtotal

    message += f"\n💵 **Total: ${total}**"

    keyboard = [
        [InlineKeyboardButton("💳 Confirmar Pedido", callback_data="checkout")],
        [InlineKeyboardButton("🗑 Vaciar Carrito", callback_data="clear_cart")],
        [InlineKeyboardButton("🛍 Seguir Comprando", callback_data="view_products")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = int(update.callback_query.data.split("_")[1])
    try:
        product = DatabaseService.get_product(product_id)
    except Exception as e:
        logger.error(f"Error al obtener producto {product_id}: {e}")
        await update.callback_query.answer("Error al cargar producto", show_alert=True)
        return

    if not product:
        await update.callback_query.answer("Producto no encontrado", show_alert=True)
        return

    if product.stock < 1:
        await update.callback_query.answer("❌ Producto sin stock disponible", show_alert=True)
        return

    user_id = update.effective_user.id
    try:
        cart = cart_service.get_cart(user_id)
        cart_quantity = sum(item.quantity for item in cart if item.product_id == product_id)

        if cart_quantity + 1 > product.stock:
            await update.callback_query.answer(
                f"❌ Stock máximo alcanzado ({product.stock} unidades)",
                show_alert=True
            )
            return

        cart_service.add_to_cart(user_id, product, 1)
        await update.callback_query.answer(f"✅ {product.name} agregado al carrito", show_alert=False)
    except Exception as e:
        logger.error(f"Error al agregar al carrito: {e}")
        await update.callback_query.answer("Error al procesar el carrito", show_alert=True)

async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        customer = DatabaseService.get_or_create_customer(
            telegram_id=update.effective_user.id,
            name=update.effective_user.first_name or "Cliente"
        )
        orders_data = DatabaseService.get_customer_orders(customer.id)
    except Exception as e:
        logger.error(f"Error al obtener pedidos: {e}")
        await update.callback_query.edit_message_text("Error al cargar tus pedidos. Intenta de nuevo.")
        return

    if not orders_data:
        await update.callback_query.edit_message_text(
            "📋 No tienes pedidos aún.\n\nUsa *Ver Productos* para hacer tu primer pedido.",
            parse_mode="Markdown"
        )
        return

    message = "📋 **Tus Pedidos:**\n\n"
    for o in orders_data[:5]:
        message += f"• #{o['id']} - ${o['total']} - *{o['status']}*\n"

    await update.callback_query.edit_message_text(
        message + "\nUsa /start para volver al menú principal."
    )

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = cart_service.get_cart(user_id)

    if not cart:
        await update.callback_query.answer("El carrito está vacío", show_alert=True)
        return

    try:
        customer = DatabaseService.get_or_create_customer(telegram_id=user_id, name=f"Cliente_{user_id}")
        total = cart_service.calculate_total(user_id)

        order = DatabaseService.create_order(customer_id=customer.id, total=total)

        items_to_save = [
            OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=item.price)
            for item in cart
        ]
        DatabaseService.add_order_items(order.id, items_to_save)

        for item in cart:
            ok = DatabaseService.atomic_decrement_stock(item.product_id, item.quantity)
            if not ok:
                logger.warning(f"Stock insuficiente para producto {item.product_id} al crear orden #{order.id}")

        cart_service.clear_cart(user_id)

        logger.info(f"Pedido #{order.id} creado por {customer.name} (${total})")

        await update.callback_query.edit_message_text(
            f"✅ **Pedido #{order.id} creado exitosamente!**\n\n"
            f"Total: ${total}\n"
            "Estado: Pendiente de confirmación\n\n"
            "Nos pondremos en contacto contigo pronto.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error al crear pedido: {e}")
        await update.callback_query.edit_message_text(
            "❌ Ocurrió un error al procesar tu pedido. Intenta de nuevo."
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "view_products":
        await view_products(update, context)
    elif query.data == "view_cart":
        await view_cart(update, context)
    elif query.data == "view_orders":
        await view_orders(update, context)
    elif query.data.startswith("product_"):
        await show_product(update, context)
    elif query.data.startswith("add_"):
        await add_to_cart(update, context)
    elif query.data == "checkout":
        await checkout(update, context)
    elif query.data == "clear_cart":
        user_id = update.effective_user.id
        cart_service.clear_cart(user_id)
        await view_cart(update, context)

def setup_telegram_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))

async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Usa /start para ver el menú principal o los botones de navegación."
    )