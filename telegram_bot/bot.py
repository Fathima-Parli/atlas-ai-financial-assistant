import logging
import asyncio
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telegram_bot.config import TELEGRAM_BOT_TOKEN
from telegram_bot.handlers import handle_text_message, handle_voice_message, handle_document_or_photo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Launching in simulator-only mode. Provide token in .env for live Telegram deployment.")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers - Natural conversation, text, voice, documents, photos
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    app.add_handler(MessageHandler(filters.DOCUMENT | filters.PHOTO, handle_document_or_photo))

    logger.info("Atlas AI Financial Assistant Telegram Bot starting long-polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
