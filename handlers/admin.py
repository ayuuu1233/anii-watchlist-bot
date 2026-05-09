from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import ADMIN_IDS
import database.db as db

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

ADMIN_PANEL = (
    "🔧 <b>Admin Panel</b>\n\n"
    "Bot manage karo:"
)

def admin_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 All Users",   callback_data="adm_users"),
            InlineKeyboardButton("📊 DB Stats",    callback_data="adm_stats"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast",   callback_data="adm_broadcast"),
        ],
        [InlineKeyboardButton("🔙 Back",           callback_data="menu_main")],
    ])

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Tumhare paas access nahi hai.")
        return
    await update.message.reply_text(ADMIN_PANEL, parse_mode="HTML", reply_markup=admin_kb())

async def cb_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    user = update.effective_user
    await q.answer()
    if not is_admin(user.id):
        await q.answer("❌ Access denied!", show_alert=True); return

    data = q.data

    if data == "adm_users":
        conn = db.get_conn()
        users = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        conn.close()
        await q.edit_message_text(
            f"👥 <b>Total Users:</b> {users['cnt']}",
            parse_mode="HTML", reply_markup=admin_kb()
        )

    elif data == "adm_stats":
        conn = db.get_conn()
        animes = conn.execute("SELECT COUNT(*) as cnt FROM watchlist").fetchone()
        reminders = conn.execute("SELECT COUNT(*) as cnt FROM reminders WHERE sent=0").fetchone()
        conn.close()
        text = (
            f"📊 <b>Database Stats</b>\n\n"
            f"🎌 Total anime entries : {animes['cnt']}\n"
            f"⏰ Active reminders    : {reminders['cnt']}"
        )
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=admin_kb())

    elif data == "adm_broadcast":
        db.set_state(user.id, "broadcast")
        await q.edit_message_text(
            "📢 <b>Broadcast Message</b>\n\nSabko bhejne ke liye message type karo:",
            parse_mode="HTML"
      )
