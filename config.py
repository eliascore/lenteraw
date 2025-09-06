import os
from telegram import Bot

TOKEN = os.getenv("TOKEN", "")
if not TOKEN:
  raise ValueError("❌ TOKEN Telegram belum diatur di environment variable.")
MENU = "https://t.me/developerlentera/4"
ADMIN_GROUP_ID = -1002357906917

bot = Bot(token=TOKEN)

DB_FILE = "cart.db"

# kata kunci OCR
KEYWORDS = ["WR BU IPAT", "MORK"]
