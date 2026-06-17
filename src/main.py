import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from .config import settings
from .handlers.telegram import setup_telegram_handlers

async def main():
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    setup_telegram_handlers(app)
    
    # Iniciar el bot
    print("Bot de Telegram iniciado...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())