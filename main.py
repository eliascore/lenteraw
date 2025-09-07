import asyncio
import os

from telegram.ext import (ApplicationBuilder, CommandHandler,
                          CallbackQueryHandler, MessageHandler, filters)
from telegram import Update
from config import TOKEN, ADMIN_GROUP_ID
from db import init_db
from handlers.start import start
from handlers.feedback import monitor_feedback
from utils import debug_group
from handlers.tombol import tombol_handler
from handlers.chatbot import handle_bidirectional_reply, forward_to_admin

WEBHOOK_URL = "https://lenteraw.onrender.com"
PORT = int(os.environ.get("PORT", 8080))

async def main():
    init_db()
    app_bot = ApplicationBuilder().token(TOKEN).build()

    # Pasang handler
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(tombol_handler))
    app_bot.add_handler(CommandHandler("debuggroup", debug_group))
    app_bot.add_handler(MessageHandler(
        filters.REPLY & (filters.Chat(ADMIN_GROUP_ID) | filters.ChatType.PRIVATE),
        handle_bidirectional_reply
    ))
    app_bot.add_handler(MessageHandler(
        (filters.PHOTO | filters.Document.IMAGE | (filters.TEXT & filters.CaptionRegex("(?i)bukti pembayaran"))),
        monitor_feedback
    ))
    app_bot.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE,
        forward_to_admin
    ))

    # Set webhook & run
    await app_bot.bot.set_webhook(WEBHOOK_URL)
    print("[INFO] Webhook Telegram sudah terpasang ✅")
    await app_bot.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    asyncio.run(main())
