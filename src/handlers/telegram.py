from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from ..config import settings
from ..services.database import DatabaseService
from ..services.cart import cart_service

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Registrar o obtener cliente
    customer = DatabaseService.get_or_create_customer(
        telegram_id=update.effective_user.id,
        name=user.first_name or "Cliente"
    )
    
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
    products = DatabaseService.get_products()
    
    if not products:
        await update.callback_query.edit_message_text("No hay productos disponibles en este momento.")
        return
    
    keyboard = []
    for product in products[:10]:  # Limitar a 10 para no saturar
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
    product_id = int(update.callback_query.data.split("_")[1])
    product = DatabaseService.get_product(product_id)
    
    if not product:
        await update.callback_query.edit_message_text("Producto no encontrado.")
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Agregar al Carrito", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton("🔙 Volver", callback_data="view_products")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"*{product.name}*\n\n{product.description}\n\n💰 Precio: ${product.price}\n📦 Stock: {product.stock}"
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
    product = DatabaseService.get_product(product_id)
    
    if not product:
        await update.callback_query.answer("Producto no encontrado", show_alert=True)
        return
    
    user_id = update.effective_user.id
    cart_service.add_to_cart(user_id, product, 1)
    
    await update.callback_query.answer(f"✅ {product.name} agregado al carrito", show_alert=False)

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = cart_service.get_cart(user_id)
    
    if not cart:
        await update.callback_query.answer("El carrito está vacío", show_alert=True)
        return
    
    # Obtener o crear cliente
    customer = DatabaseService.get_or_create_customer(telegram_id=user_id, name=f"Cliente_{user_id}")
    
    # Calcular total
    total = cart_service.calculate_total(user_id)
    
    # Crear orden
    order = DatabaseService.create_order(customer_id=customer.id, total=total)
    
    # Agregar items a la orden
    order_items = [
        {"product_id": item.product_id, "quantity": item.quantity, "price": item.price}
        for item in cart
    ]
    
    # Actualizar stock
    for item in cart:
        prod = DatabaseService.get_product(item.product_id)
        if prod:
            DatabaseService.update_stock(item.product_id, prod.stock - item.quantity)
    
    cart_service.clear_cart(user_id)
    
    await update.callback_query.edit_message_text(
        f"✅ **Pedido #{order.id} creado exitosamente!**\n\n"
        f"Total: ${total}\n"
        "Estado: Pendiente de confirmación\n\n"
        "Nos pondremos en contacto contigo pronto.",
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "view_products":
        await view_products(update, context)
    elif query.data == "view_cart":
        await view_cart(update, context)
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