import sqlite3

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import DB_FILE, MENU
from handlers.start import kirim_nota
from db import delete_item, get_cart, simpan_metode_bayar_di_cart, simpan_kode_bayar_di_cart, save_pending_payment
from utils import generate_kode_bayar, obfuscate_kode, create_order_id
from config import DB_FILE


async def tombol_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "TanpaNama"
    query = update.callback_query
    await query.answer()

    if query.data.startswith("hapus_"):
        item_id = int(query.data.split("_")[1])
        delete_item(item_id)
        await kirim_nota(update, query.from_user.id)

    elif query.data == "bayar":
        items = get_cart(query.from_user.id)
        if not items:
            await query.message.reply_text("Belum ada pesanan.")
            return

        total = sum(harga for _, _, harga in items)
        daftar = "\n".join([
            f"{i+1}. {nama} - Rp {harga:,}"
            for i, (_, nama, harga) in enumerate(items)
        ])
        text = f"🧾 *Nota Pesanan:*\n\n{daftar}\n\n💰 *Total:* Rp {total:,}"

        keyboard = [
            [InlineKeyboardButton("QRIS", callback_data="pay_qris")],
            [InlineKeyboardButton("ShopeePay", callback_data="pay_shopeepay")],
            [InlineKeyboardButton("DANA", callback_data="pay_dana")],
            [InlineKeyboardButton("OVO", callback_data="pay_ovo")],
            [InlineKeyboardButton("GoPay", callback_data="pay_gopay")],
        ]
        await query.message.reply_text(
            text=f"{text}\n\n💵 Silakan pilih metode pembayaran:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pay_"):
        metode = query.data.replace("pay_", "").upper()

        # Kirim QR code atau nomor sesuai metode
        if metode == "QRIS" or metode == "DANA":
            # 1️⃣ Ambil total nominal
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                "SELECT SUM(harga) FROM cart WHERE user_id=? AND status='pending'",
                (user_id, ))
            row = c.fetchone()
            conn.close()
            nominal = row[0] if row and row[0] is not None else 0

            if nominal <= 0:
                await query.message.reply_text(
                    "Keranjangmu kosong atau tidak ada yang perlu dibayar.")
                return

            save_pending_payment(user_id, create_order_id(user_id), nominal)
            simpan_metode_bayar_di_cart(user_id, metode)

            file_path = "QRIS.jpg"
            with open(file_path, "rb") as f:
                await query.message.reply_photo(
                    photo=f,
                    caption=
                    "Scan QR Code untuk pembayaran, lalu kirim bukti dengan caption 'Bukti Pembayaran' tanpa tanda kutip."
                )

        elif metode == "GOPAY":
            # 1️⃣ Ambil total nominal
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                "SELECT SUM(harga) FROM cart WHERE user_id=? AND status='pending'",
                (user_id, ))
            row = c.fetchone()
            conn.close()
            nominal = row[0] if row and row[0] is not None else 0

            if nominal <= 0:
                await query.message.reply_text(
                    "Keranjangmu kosong atau tidak ada yang perlu dibayar.")
                return

            save_pending_payment(user_id, create_order_id(user_id), nominal)
            simpan_metode_bayar_di_cart(user_id, metode)

            file_path = "QR_GOPAY.png"
            with open(file_path, "rb") as f:
                await query.message.reply_photo(
                    photo=f,
                    caption=
                    "Scan QR Code untuk pembayaran, lalu kirim bukti dengan caption 'Bukti Pembayaran' tanpa tanda kutip."
                )

        elif metode in ["SHOPEEPAY", "OVO"]:
            # 1️⃣ Ambil total nominal
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                "SELECT SUM(harga) FROM cart WHERE user_id=? AND status='pending'",
                (user_id, ))
            row = c.fetchone()
            conn.close()
            nominal = row[0] if row and row[0] is not None else 0

            if nominal <= 0:
                await query.message.reply_text(
                    "Keranjangmu kosong atau tidak ada yang perlu dibayar.")
                return

            # Generate kode bayar rumit
            kode_bayar = obfuscate_kode(generate_kode_bayar(nominal))

            # Safe username: pakai username kalau ada, kalau tidak pakai nama depan
            username_safe = username if username else user.first_name
            kode_bayar_str = f"@{username_safe}{kode_bayar}"

            # Simpan ke cart
            simpan_kode_bayar_di_cart(user_id, username_safe, kode_bayar_str)
            save_pending_payment(user_id, create_order_id(user_id), nominal)
            simpan_metode_bayar_di_cart(user_id, metode)

            nomor = "+6285713869358"
            await query.message.reply_text(
                f"💰 Bayarkan ke nomor berikut: {nomor}\n"
                f"🆔 Kode Bayar: {kode_bayar_str}\n\n"
                f"⚠️ Pastikan menuliskan Kode Bayar ini di bukti pembayaran agar otomatis terdeteksi.",
                parse_mode="Markdown")
