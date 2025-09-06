from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import add_to_cart, get_cart
from produk import produk
from utils import safe_reply
from config import MENU

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "TanpaNama"

    args = context.args
    if args:
        item = args[0]
        if item in produk:
            nama_produk, harga = produk[item]
            add_to_cart(user_id, username, nama_produk, harga)
            
            await kirim_nota(update, user_id)
            return

    keyboard = [[InlineKeyboardButton("Mau Lihat Katalog 📖", url=MENU)]]
    await safe_reply(update=update,
                     text="Halo! Apa yang kamu butuhkan? 😸",
                     reply_markup=InlineKeyboardMarkup(keyboard))

async def kirim_nota(update: Update, user_id: int):
    user = update.effective_user
    username = user.username or user.first_name or "TanpaNama"

    items = get_cart(user_id)
    if not items:
        text = f"👤 *Pemesan:* @{username}\n\nBelum ada pesanan."
        keyboard = [[InlineKeyboardButton("➕ Tambah Pesanan", url=MENU)]]
    else:
        total = sum(h for _, _, h in items)
        daftar = "\n".join([
            f"{i+1}. {nama} - Rp {harga:,}"
            for i, (_, nama, harga) in enumerate(items)
        ])
        text = f"👤 *Pemesan:* @{username}\n\n🧾 *Nota Pesanan:*\n\n{daftar}\n\n💰 *Total:* Rp {total:,}"

        tombol_items = [[
            InlineKeyboardButton(f"❌ Hapus {nama}",
                                 callback_data=f"hapus_{item_id}")
        ] for item_id, nama, _ in items]

        tombol_actions = [[InlineKeyboardButton("➕ Tambah Pesanan", url=MENU)],
                          [
                              InlineKeyboardButton("✅ Cukup, Lanjut Bayar",
                                                   callback_data="bayar")
                          ]]

        keyboard = tombol_items + tombol_actions

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard))
    else:

        await safe_reply(update=update,
                         text=text,
                         parse_mode="Markdown",
                         reply_markup=InlineKeyboardMarkup(keyboard))
