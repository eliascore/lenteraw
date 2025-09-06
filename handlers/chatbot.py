from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_GROUP_ID
from db import ambil_mapping_dari_reply, simpan_message_map


# handler khusus untuk tangkap reply di grup admin
async def handle_bidirectional_reply(update: Update,
                                     context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.reply_to_message:
        return

    chat_id = message.chat.id
    from_admin = (chat_id == ADMIN_GROUP_ID)
    print(
        f"[DEBUG] handle_bidirectional_reply triggered. from_admin={from_admin}"
    )

    reply_to_id = message.reply_to_message.message_id
    mapping = ambil_mapping_dari_reply(reply_to_id, dari_admin=from_admin)

    if not mapping:
        print("[DEBUG] Tidak ada mapping untuk reply ini.")
        return

    if from_admin:
        # mapping: (user_id, user_message_id)
        user_id, user_message_id = mapping
        sent_msg = await context.bot.send_message(
            chat_id=user_id,
            text=f"👨‍💻 Admin:\n{message.text}",
            reply_to_message_id=user_message_id)
        simpan_message_map(message.message_id, sent_msg.message_id, user_id)

    else:
        # mapping: (user_id, group_message_id)
        user_id, group_message_id = mapping
        sent_msg = await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=
            f"👤 {message.from_user.first_name or message.from_user.id}:\n{message.text}",
            reply_to_message_id=group_message_id)
        simpan_message_map(sent_msg.message_id, message.message_id, user_id)

# Semua chat user → terus ke admin group
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    # Pastikan hanya forward dari private chat (user → bot)
    if message.chat.type != "private":
        return

    # teruskan pesan ke grup admin
    sent_msg = await context.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=f"👤 {message.from_user.first_name or message.from_user.id}:\n{message.text}",
    )

    # simpan mapping agar admin bisa balas
    simpan_message_map(sent_msg.message_id, message.message_id, message.from_user.id)