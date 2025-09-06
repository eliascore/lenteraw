import sqlite3
import time
from datetime import datetime
from config import DB_FILE


def init_db():
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   # Tabel cart + kode bayar
   c.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        nama_produk TEXT,
        harga INTEGER,
        status TEXT DEFAULT 'pending',
        kode_bayar TEXT,       -- kode bayar unik per user
        metode_bayar TEXT,     -- simpan metode pembayaran (QRIS, DANA, GOPAY, dll)
        created_at TEXT        -- timestamp generate kode
    )
    """)

   # Tabel pending_payment untuk hold status pembayaran
   c.execute("""
        CREATE TABLE IF NOT EXISTS pending_payment (
            user_id INTEGER PRIMARY KEY,
            order_id TEXT,
            expected_nominal REAL,
            status TEXT
        )
    """)

   # 🆕 Tabel message_map
   c.execute("""
    CREATE TABLE IF NOT EXISTS message_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_message_id INTEGER,
        user_message_id INTEGER,
        user_id INTEGER,
        session_id TEXT,
        created_at TEXT
    )

    """)
   conn.commit()
   conn.close()


def save_pending_payment(user_id, order_id, expected_nominal):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
        INSERT OR REPLACE INTO pending_payment (user_id, order_id, expected_nominal, status)
        VALUES (?, ?, ?, ?)
    """, (user_id, order_id, expected_nominal, "WAITING_PROOF"))
   conn.commit()
   conn.close()


# Menyimpan kode bayar + timestamp ke cart
def simpan_kode_bayar_di_cart(user_id, username, kode_bayar):
   created_at = datetime.now().isoformat()
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
        UPDATE cart
        SET kode_bayar = ?, created_at = ?
        WHERE user_id = ? AND status = 'pending'
    """, (kode_bayar, created_at, user_id))
   conn.commit()
   conn.close()


# Menyimpan metode bayar ke cart (dipanggil saat user pilih metode)
def simpan_metode_bayar_di_cart(user_id, metode_bayar):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
        UPDATE cart
        SET metode_bayar = ?
        WHERE user_id = ? AND status = 'pending'
    """, (metode_bayar, user_id))
   conn.commit()
   conn.close()


# Ambil kode bayar + metode bayar sekaligus
def ambil_kode_dan_metode_bayar(user_id):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
        SELECT kode_bayar, metode_bayar 
        FROM cart 
        WHERE user_id = ? AND status = 'pending' 
        LIMIT 1
    """, (user_id, ))
   row = c.fetchone()
   conn.close()
   return (row[0], row[1]) if row else (None, None)


def get_pending_payment(user_id):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
        SELECT order_id, expected_nominal, status 
        FROM pending_payment 
        WHERE user_id = ?
    """, (user_id, ))
   row = c.fetchone()
   conn.close()
   return row


def clear_pending_payment(user_id):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute("DELETE FROM pending_payment WHERE user_id = ?", (user_id, ))
   conn.commit()
   conn.close()


# Ambil cart pending
def get_cart(user_id):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
        SELECT id, nama_produk, harga 
        FROM cart 
        WHERE user_id = ? AND status = 'pending'
    """, (user_id, ))
   items = c.fetchall()
   conn.close()
   return items


def get_cart_total(user_id: int) -> int:
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
        SELECT COALESCE(SUM(harga), 0)
        FROM cart
        WHERE user_id = ? AND status = 'pending'
    """, (user_id, ))
   total = c.fetchone()[0] or 0
   conn.close()
   return int(total)


def delete_item(item_id):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute("DELETE FROM cart WHERE id = ?", (item_id, ))
   conn.commit()
   conn.close()


def clear_cart(user_id):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute("DELETE FROM cart WHERE user_id = ? AND status = 'pending'",
             (user_id, ))
   conn.commit()
   conn.close()


def mark_cart_done(user_id):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
        UPDATE cart 
        SET status = 'done' 
        WHERE user_id = ? AND status = 'pending'
    """, (user_id, ))
   conn.commit()
   conn.close()


# Fungsi memasukkan ke cart
def add_to_cart(user_id, username, nama_produk, harga, metode_bayar=None):
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
        INSERT INTO cart (user_id, username, nama_produk, harga, status, metode_bayar)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (user_id, username, nama_produk, harga, metode_bayar))
   conn.commit()
   conn.close()


def simpan_message_map(group_message_id: int, user_message_id: int,
                       user_id: int) -> str:
   """
   Simpan mapping antara message grup & message user.
   Tidak overwrite data lama, sehingga bisa handle multiple replies.
   """
   session_id = f"SESSION-{user_id}-{int(time.time())}"
   created_at = datetime.now().isoformat()

   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   c.execute(
       """
   INSERT INTO message_map (group_message_id, user_message_id, user_id, session_id, created_at)
   VALUES (?, ?, ?, ?, ?)
   """, (group_message_id, user_message_id, user_id, session_id, created_at))
   conn.commit()
   conn.close()
   print(
       f"[DEBUG] Mapping baru disimpan: group_msg_id={group_message_id}, user_msg_id={user_message_id}"
   )
   return session_id


def ambil_mapping_dari_reply(reply_message_id: int, dari_admin: bool):
   """
    Ambil mapping berdasarkan message_id yang di-reply.
    dari_admin=True → cari di group_message_id
    dari_admin=False → cari di user_message_id
    """
   conn = sqlite3.connect(DB_FILE)
   c = conn.cursor()
   if dari_admin:
      c.execute(
          """
            SELECT user_id, user_message_id FROM message_map
            WHERE group_message_id = ?
            ORDER BY id DESC LIMIT 1
        """, (reply_message_id, ))
   else:
      c.execute(
          """
            SELECT user_id, group_message_id FROM message_map
            WHERE user_message_id = ?
            ORDER BY id DESC LIMIT 1
        """, (reply_message_id, ))
   result = c.fetchone()
   conn.close()
   return result
