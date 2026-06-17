import asyncio
import logging
import uvicorn
from telegram.ext import Application
from .config import settings
from .handlers.telegram import setup_telegram_handlers
from .api import app as fastapi_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_telegram():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN no configurado. Bot de Telegram desactivado.")
        return
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    setup_telegram_handlers(app)
    logger.info("Bot de Telegram iniciado...")
    await app.run_polling()


async def run_api():
    logger.info("API iniciada en http://0.0.0.0:8000")
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    logger.info("Iniciando Bot Multi-plataforma...")
    await asyncio.gather(run_telegram(), run_api())


if __name__ == "__main__":
    asyncio.run(main())