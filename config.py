import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
  raise ValueError("❌ TOKEN Telegram belum diatur di environment variable.")
MENU = "https://t.me/developerlentera/4"
ADMIN_GROUP_ID = os.getenv(int("ADMIN_GROUP_ID"))

DB_FILE = "cart.db"

# kata kunci OCR
KEYWORDS = ["WR BU IPAT", "MORK"]
