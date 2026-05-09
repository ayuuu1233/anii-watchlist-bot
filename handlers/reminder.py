import datetime
from telegram import Update
from telegram.ext import ContextTypes
import database.db as db
from utils.keyboards import reminder_time_kb, main_menu_kb
from utils.anilist import get_anime_by_id

DELTA = {
    "1h":  datetime.timedelta(hours=1),
    "3h":  datetime.timedelta(hours=3),
    "1d":  datetime.timedelta(days=1),
    "7d":  datetime.timedelta(days=7),
}

DELTA_LABEL = {
    "1h": "1 hour",
    "3h": "3 hours",
    "1d": "Tomorrow",
    "7d": "1 Week",
}

# ── /remind command ────────────────────────────────────────────────
async def cmd_remind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    reminders = db.get_user_reminders(update.effective_user.id)
    if not reminders:
        text = (
            "⏰ <b>Reminders</b>\n\n"
            "Koi active reminder nahi hai.\n\n"
            "💡 Kisi anime ko search karo aur reminder set karo!"
        )
    else:
        text = f"⏰ <b>Active Reminders ({len(reminders)})</b>\n\n"
        for r in reminders:
            text += f"🔔 <b>{r['title']}</b>\n📅 {r['remind_at']}\n🆔 ID: {r['id']}\n\n"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_menu_kb())

# ── Callback: rem_ buttons ─────────────────────────────────────────
async def cb_reminder(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    user = update.effective_user
    await q.answer()

    # Show time picker
    if data.startswith("rem_set_"):
        anime_id = int(data.replace("rem_set_", ""))
        anime = await get_anime_by_id(anime_id)
        title = "?"
        if anime:
            title = anime["title"].get("english") or anime["title"].get("romaji","?")
        await q.edit_message_text(
            f"⏰ <b>Reminder for:</b>\n🎌 {title}\n\nKab yaad dilana hai?",
            parse_mode="HTML",
            reply_markup=reminder_time_kb(anime_id)
        )

    # Save reminder
    elif data.startswith("rem_time_"):
        parts    = data.replace("rem_time_", "").split("_")
        anime_id = int(parts[0])
        delta_key = parts[1]

        anime = await get_anime_by_id(anime_id)
        title = "?"
        if anime:
            title = anime["title"].get("english") or anime["title"].get("romaji","?")

        remind_at = datetime.datetime.now() + DELTA[delta_key]
        db.add_reminder(user.id, anime_id, title, remind_at.strftime("%Y-%m-%d %H:%M:%S"))

        await q.edit_message_text(
            f"✅ <b>Reminder set!</b>\n\n"
            f"🎌 {title}\n"
            f"⏰ {DELTA_LABEL[delta_key]} baad remind karunga!\n"
            f"📅 {remind_at.strftime('%d %b %Y %H:%M')}",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )

# ── Background job: check & send due reminders ─────────────────────
async def check_reminders(ctx: ContextTypes.DEFAULT_TYPE):
    due = db.get_due_reminders()
    for r in due:
        try:
            await ctx.bot.send_message(
                chat_id=r["user_id"],
                text=(
                    f"🔔 <b>Reminder!</b>\n\n"
                    f"🎌 <b>{r['title']}</b>\n"
                    f"Tumne iska reminder set kiya tha!\n"
                    f"Ab dekho? 👀"
                ),
                parse_mode="HTML",
                reply_markup=main_menu_kb()
            )
            db.mark_reminder_sent(r["id"])
        except Exception:
            pass
