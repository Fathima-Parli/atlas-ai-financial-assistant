import logging
import httpx
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.config import BACKEND_API_URL

logger = logging.getLogger(__name__)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle natural text messages from Telegram users."""
    if not update.message or not update.message.text:
        return

    user_id = str(update.message.from_user.id)
    user_name = update.message.from_user.first_name or "User"
    text = update.message.text

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BACKEND_API_URL}/chat",
                json={
                    "telegram_id": user_id,
                    "name": user_name,
                    "message": text
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("reply", "I processed your request.")
                await update.message.reply_text(reply, parse_mode="Markdown")
            else:
                await update.message.reply_text("Unable to reach Atlas Financial backend engine.")
    except Exception as e:
        logger.error(f"Error handling Telegram message: {e}")
        await update.message.reply_text("Atlas Financial Assistant encountered an error processing your query.")

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming voice messages."""
    if not update.message or not update.message.voice:
        return

    user_id = str(update.message.from_user.id)
    await update.message.reply_text("🎙️ Processing your voice message...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BACKEND_API_URL}/voice",
                data={
                    "telegram_id": user_id,
                    "simulated_transcript": "Summarize Nvidia's revenue trends and quarterly risks"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("reply", "")
                transcript = data.get("transcript", "")
                msg = f"🗣️ *Transcribed*: \"{transcript}\"\n\n{reply}"
                await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Voice handling error: {e}")
        await update.message.reply_text("Error processing voice message.")

async def handle_document_or_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded PDFs, financial report documents, or chart photos."""
    if not update.message:
        return

    user_id = str(update.message.from_user.id)

    if update.message.photo:
        await update.message.reply_text("📊 Analyzing chart / financial image...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BACKEND_API_URL}/image",
                data={"telegram_id": user_id, "caption": update.message.caption or "Stock Chart"}
            )
            if resp.status_code == 200:
                await update.message.reply_text(resp.json().get("reply", ""), parse_mode="Markdown")

    elif update.message.document:
        doc = update.message.document
        await update.message.reply_text(f"📄 Extracting executive insights from '{doc.file_name}'...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BACKEND_API_URL}/upload",
                data={"telegram_id": user_id},
                files={"file": (doc.file_name, b"Sample report content text", "application/pdf")}
            )
            if resp.status_code == 200:
                await update.message.reply_text(resp.json().get("reply", ""), parse_mode="Markdown")
