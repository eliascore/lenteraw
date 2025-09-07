import asyncio
import os
from flask import Flask, request
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

# bikin Flask app
web_app = Flask(__name__)



app_bot = ApplicationBuilder().token(TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CallbackQueryHandler(tombol_handler))
app_bot.add_handler(CommandHandler("debuggroup", debug_group))
app_bot.add_handler(MessageHandler(filters.REPLY & (filters.Chat(ADMIN_GROUP_ID) | filters.ChatType.PRIVATE), handle_bidirectional_reply))
print("[DEBUG] Handler handle_bidirectional_reply sudah dipasang.")

# Pastikan handler ini ditambahkan SETELAH app_bot didefinisikan
app_bot.add_handler(MessageHandler((filters.PHOTO | filters.Document.IMAGE | (filters.TEXT & filters.CaptionRegex("(?i)bukti pembayaran"))), monitor_feedback))
app_bot.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, forward_to_admin))

print("Bot polling...")

async def set_webhook():
    WEBHOOK_URL = "https://lenteraw.onrender.com/"  # ganti sesuai URL Render
    await app_bot.bot.set_webhook(WEBHOOK_URL)
    print("[INFO] Webhook Telegram sudah terpasang ✅")

from asgiref.sync import async_to_sync

@web_app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    async_to_sync(app_bot.process_update)(update)  # jalankan async di sync
    return "ok"
async def set_webhook():
    WEBHOOK_URL = "https://lenteraw.onrender.com/"  # ganti sesuai URL Render
    await app_bot.bot.set_webhook(WEBHOOK_URL)

    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    init_db()
