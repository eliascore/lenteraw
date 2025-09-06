from flask import Flask, request
import threading

from telegram.ext import (ApplicationBuilder, CommandHandler,
                          CallbackQueryHandler, MessageHandler, filters)
from telegram import Update
from config import TOKEN, ADMIN_GROUP_ID, bot
from db import init_db
from handlers.start import start
from handlers.feedback import monitor_feedback
from utils import debug_group
from handlers.tombol import tombol_handler
from handlers.chatbot import handle_bidirectional_reply
from handlers.chatbot import forward_to_admin

# bikin Flask app
web_app = Flask(__name__)

@web_app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    # di sini kamu bisa panggil dispatcher.handle_update(update)
    # kalau pakai telegram.ext 20+ versi, biasanya:
    asyncio.run(app_dispatcher.process_update(update))
    return "ok"


def main():
    init_db()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(tombol_handler))
    app_bot.add_handler(CommandHandler("debuggroup", debug_group))
    app_bot.add_handler(
        MessageHandler(
            filters.REPLY &
            (filters.Chat(ADMIN_GROUP_ID) | filters.ChatType.PRIVATE),
            handle_bidirectional_reply))
    print("[DEBUG] Handler handle_bidirectional_reply sudah dipasang.")

    # Pastikan handler ini ditambahkan SETELAH app_bot didefinisikan
    app_bot.add_handler(
        MessageHandler(
            (filters.PHOTO | filters.Document.IMAGE |
             (filters.TEXT & filters.CaptionRegex("(?i)bukti pembayaran"))),
            monitor_feedback))

    app_bot.add_handler(
        MessageHandler(
            filters.TEXT
            & filters.ChatType.PRIVATE,  # semua chat user di private
            forward_to_admin))



if __name__ == "__main__":
    main()
