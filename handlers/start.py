#═════════════════════════════════════════════════╗
# ║   🎌 A N I M E  W A T C H L I S T  B O T  🎌    ║
# ║        ✦ Kawaii · Powerful · Premium ✦           ║
# ╚══════════════════════════════════════════════════╝

import asyncio
import random
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from database.db import upsert_user, get_user_stats
from utils.keyboards import watchlist_filter_kb
import database.db as db

logger = logging.getLogger(__name__)


# ╔══════════════════════════════════════════════════╗
# ║                    CONFIG                        ║
# ╚══════════════════════════════════════════════════╝

BOT_NAME      = "『 ᴀɴɪᴍᴇ ᴡᴀᴛᴄʜ 』"
BOT_USERNAME  = "YourBotUsername"        # 👈 apna bot username dalo
SUPPORT_GROUP = "YourSupportGroup"       # 👈 support group link dalo

# 🎬 Anime vibe short clips — catbox ya Telegram file_id
VIDEO_PRIVATE = "https://files.catbox.moe/931ph0.mp4"   # 👈 replace karo
VIDEO_GROUP   = "https://files.catbox.moe/dlg0rb.mp4"   # 👈 replace karo

# 🌸 Sticker pool — randomly pick hoga har baar
STICKER_POOL = [
    "CAACAgUAAxkBAAFGPRZpzjXBHq7-IjDYsyawr6QAAQ5Oey8AAp0LAAK5UtFVp098U-zMvyc6BA",
    # aur stickers add karo 👇
    # "CAACAgIAAxkBAAI...",
]


# ╔══════════════════════════════════════════════════╗
# ║                  GREETINGS                       ║
# ╚══════════════════════════════════════════════════╝

GREETINGS = [
    "ʜᴇʏʏ~ ᴜᴡᴜ 💕",
    "ɴʏᴀᴀ~ 🌸",
    "ʏᴏʜʜᴏ~ ✨",
    "ᴋᴏɴɴɪᴄʜɪᴡᴀ~ 🫶",
    "ʜᴏʟᴀ sᴇɴᴘᴀɪ~ 🎀",
    "ᴀʀᴀ ᴀʀᴀ~ 🌺",
    "ᴏʜᴀʏᴏᴜ~ ☀️",
    "ᴋᴀᴡᴀɪɪ ᴅᴇsᴜ~ 💫",
    "ʏᴀᴀᴀ~ 🌙",
    "sᴜᴘ sᴇɴᴘᴀɪ~ 🔥",
]


# ╔══════════════════════════════════════════════════╗
# ║                  HELP TEXT                       ║
# ╚══════════════════════════════════════════════════╝

HELP_TEXT = """
🌸 <b>Anime Watchlist Bot — Commands</b>

<b>🔍 Search</b>
/search &lt;name&gt; — Search any anime (AniList)

<b>📋 Watchlist</b>
/list — View your full watchlist
/add &lt;name&gt; — Add anime to list
/remove &lt;id&gt; — Remove anime
/status &lt;id&gt; — Change watching status
/progress &lt;id&gt; &lt;ep&gt; — Update episode progress

<b>📊 Stats</b>
/stats — Your personal anime stats
/top — Your top-rated anime list

<b>⏰ Reminders</b>
/remind — View &amp; manage all reminders

<b>💡 Pro Tip:</b>
Just type any anime name — I'll search it instantly~ 🎌
"""


# ╔══════════════════════════════════════════════════╗
# ║                  CAPTIONS                        ║
# ╚══════════════════════════════════════════════════╝

def build_private_caption(user):
    greet = random.choice(GREETINGS)
    return (
        f"┏━━━❖ 🎌 ❖━━━┓\n"
        f"  {greet}\n\n"
        f"  <b><a href='tg://user?id={user.id}'>{user.first_name}</a></b>\n"
        f"┗━━━❖ 🎌 ❖━━━┛\n\n"
        f"✨ <b>Welcome to {BOT_NAME}</b>\n\n"
        f"➤ Your Personal Anime Tracker 📺\n"
        f"➤ Powered by AniList Database 🌐\n\n"
        f"───────────────\n"
        f"🌸 <b>Features:</b>\n\n"
        f"✦ Search 15,000+ Anime\n"
        f"✦ Watchlist with 5 Statuses\n"
        f"✦ Episode Progress Tracker\n"
        f"✦ Rating System ⭐\n"
        f"✦ Smart Reminders ⏰\n"
        f"✦ Personal Stats 📊\n\n"
        f"───────────────\n\n"
        f"💖 Use the menu below\n"
        f"to start your anime journey~ 🎌"
    )


def build_group_caption(user):
    return (
        f"🎌 <b>{BOT_NAME} is here!</b>\n\n"
        f"ʜᴇʏ <a href='tg://user?id={user.id}'>{user.first_name}</a>~ 👀\n\n"
        f"✨ Track your anime watchlist\n"
        f"📺 15,000+ anime from AniList\n"
        f"⭐ Rate, review &amp; set reminders\n\n"
        f"➤ Use /help to see all commands~ 🌸"
    )


# ╔══════════════════════════════════════════════════╗
# ║                  KEYBOARDS                       ║
# ╚══════════════════════════════════════════════════╝

def main_menu_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 My Watchlist",  callback_data="menu_watchlist"),
            InlineKeyboardButton("🔍 Search Anime",  callback_data="menu_search"),
        ],
        [
            InlineKeyboardButton("📊 My Stats",      callback_data="menu_stats"),
            InlineKeyboardButton("⏰ Reminders",      callback_data="menu_reminders"),
        ],
        [
            InlineKeyboardButton("🏆 Top Rated",     callback_data="menu_top"),
            InlineKeyboardButton("❓ Help",           callback_data="menu_help"),
        ],
    ])


def private_buttons():
    """Full keyboard shown on /start video — includes Add to Group."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 My Watchlist",  callback_data="menu_watchlist"),
            InlineKeyboardButton("🔍 Search Anime",  callback_data="menu_search"),
        ],
        [
            InlineKeyboardButton("📊 My Stats",      callback_data="menu_stats"),
            InlineKeyboardButton("⏰ Reminders",      callback_data="menu_reminders"),
        ],
        [
            InlineKeyboardButton("🏆 Top Rated",     callback_data="menu_top"),
            InlineKeyboardButton("❓ Help",           callback_data="menu_help"),
        ],
        [
            InlineKeyboardButton(
                "➕ Add to Group",
                url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
            ),
            InlineKeyboardButton(
                "🌸 Support",
                url=f"https://t.me/{SUPPORT_GROUP}"
            ),
        ],
    ])


def group_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Add Me to Your Group",
                url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton("🌸 Support", url=f"https://t.me/{SUPPORT_GROUP}"),
            InlineKeyboardButton("❓ Help",    callback_data="menu_help"),
        ],
    ])


def help_back_kb():
    """Back button shown below help text."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="back_start")]
    ])


# ╔══════════════════════════════════════════════════╗
# ║               START COMMAND                      ║
# ╚══════════════════════════════════════════════════╝

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # Save user to DB
    upsert_user(user.id, user.username or "", user.first_name or "")

    # ── GROUP MODE ──────────────────────────────────────────────
    if chat.type != "private":
        try:
            await ctx.bot.send_video(
                chat_id=chat.id,
                video=VIDEO_GROUP,
                caption=build_group_caption(user),
                parse_mode=ParseMode.HTML,
                reply_markup=group_buttons(),
                supports_streaming=True,
            )
        except Exception as e:
            logger.warning(f"Group video failed: {e}")
            await update.message.reply_html(
                build_group_caption(user),
                reply_markup=group_buttons()
            )
        return

    # ── PRIVATE MODE ────────────────────────────────────────────

    # 1️⃣  Random sticker
    try:
        sticker = random.choice(STICKER_POOL)
        await ctx.bot.send_sticker(chat.id, sticker)
        await asyncio.sleep(0.4)
    except Exception as e:
        logger.warning(f"Sticker failed: {e}")

    # 2️⃣  Typing effect (feels alive~)
    try:
        await ctx.bot.send_chat_action(chat.id, ChatAction.TYPING)
        await asyncio.sleep(0.8)
    except Exception as e:
        logger.warning(f"Chat action failed: {e}")

    # 3️⃣  Video + caption + full menu buttons
    try:
        await ctx.bot.send_video(
            chat_id=chat.id,
            video=VIDEO_PRIVATE,
            caption=build_private_caption(user),
            parse_mode=ParseMode.HTML,
            reply_markup=private_buttons(),
            supports_streaming=True,
        )
    except Exception as e:
        logger.error(f"Private video failed: {e}")
        # Fallback — text only
        await update.message.reply_html(
            build_private_caption(user),
            reply_markup=private_buttons()
        )


# ╔══════════════════════════════════════════════════╗
# ║               HELP COMMAND                       ║
# ╚══════════════════════════════════════════════════╝

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=help_back_kb()
    )


# ╔══════════════════════════════════════════════════╗
# ║           CALLBACK HANDLER (menu_)               ║
# ╚══════════════════════════════════════════════════╝

async def cb_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    await q.answer()
    user = update.effective_user

    # ── Back to start (from help page) ────────────────────────
    if data == "back_start":
        try:
            await q.message.delete()
        except Exception:
            pass

        # Re-send sticker + video
        try:
            sticker = random.choice(STICKER_POOL)
            await ctx.bot.send_sticker(q.message.chat.id, sticker)
            await asyncio.sleep(0.4)
        except Exception:
            pass

        try:
            await ctx.bot.send_video(
                chat_id=q.message.chat.id,
                video=VIDEO_PRIVATE,
                caption=build_private_caption(user),
                parse_mode=ParseMode.HTML,
                reply_markup=private_buttons(),
                supports_streaming=True,
            )
        except Exception as e:
            logger.error(f"Back → video failed: {e}")
            await ctx.bot.send_message(
                chat_id=q.message.chat.id,
                text=build_private_caption(user),
                parse_mode=ParseMode.HTML,
                reply_markup=private_buttons()
            )

    # ── Main menu ──────────────────────────────────────────────
    elif data == "menu_main":
        await q.edit_message_caption(
            caption=build_private_caption(user),
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_kb()
        )

    # ── Watchlist ──────────────────────────────────────────────
    elif data == "menu_watchlist":
        await q.edit_message_caption(
            caption=(
                "┏━━━❖ 📋 ❖━━━┓\n"
                "  <b>My Watchlist</b>\n"
                "┗━━━❖ 📋 ❖━━━┛\n\n"
                "Kaun si list dekhni hai~ 🌸"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=watchlist_filter_kb()
        )

    # ── Search ─────────────────────────────────────────────────
    elif data == "menu_search":
        db.set_state(user.id, "searching")
        await q.edit_message_caption(
            caption=(
                "┏━━━❖ 🔍 ❖━━━┓\n"
                "  <b>Anime Search</b>\n"
                "┗━━━❖ 🔍 ❖━━━┛\n\n"
                "Anime ka naam type karo~\n"
                "Main AniList se dhundh dunga! 🌸\n\n"
                "<i>e.g. Naruto, Solo Leveling, Frieren...</i>"
            ),
            parse_mode=ParseMode.HTML,
        )

    # ── Stats ──────────────────────────────────────────────────
    elif data == "menu_stats":
        stats = get_user_stats(user.id)
        total = stats["total_anime"] or 1

        def bar(n):
            filled = round((n / total) * 8)
            return "█" * filled + "░" * (8 - filled)

        text = (
            f"┏━━━❖ 📊 ❖━━━┓\n"
            f"  <b>{user.first_name}'s Stats</b>\n"
            f"┗━━━❖ 📊 ❖━━━┛\n\n"
            f"👁️  Watching   {bar(stats['watching'])}  <b>{stats['watching']}</b>\n"
            f"✅  Completed  {bar(stats['completed'])}  <b>{stats['completed']}</b>\n"
            f"⏸️  On Hold    {bar(stats['on_hold'])}  <b>{stats['on_hold']}</b>\n"
            f"❌  Dropped   {bar(stats['dropped'])}  <b>{stats['dropped']}</b>\n"
            f"📋  Planned   {bar(stats['plan'])}  <b>{stats['plan']}</b>\n\n"
            f"───────────────\n"
            f"🎌 Total Anime  : <b>{stats['total_anime']}</b>\n"
            f"📺 Episodes     : <b>{stats['total_episodes']}</b> watched~"
        )
        await q.edit_message_caption(
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_kb()
        )

    # ── Reminders ──────────────────────────────────────────────
    elif data == "menu_reminders":
        reminders = db.get_user_reminders(user.id)
        if not reminders:
            text = (
                "┏━━━❖ ⏰ ❖━━━┓\n"
                "  <b>Reminders</b>\n"
                "┗━━━❖ ⏰ ❖━━━┛\n\n"
                "Koi reminder nahi hai abhi~\n\n"
                "💡 Anime search karo aur\n"
                "reminder set karo senpai! 🌸"
            )
        else:
            text = (
                f"┏━━━❖ ⏰ ❖━━━┓\n"
                f"  <b>Active Reminders ({len(reminders)})</b>\n"
                f"┗━━━❖ ⏰ ❖━━━┛\n\n"
            )
            for i, r in enumerate(reminders, 1):
                text += f"{i}. 🔔 <b>{r['title']}</b>\n   📅 {r['remind_at']}\n\n"
        await q.edit_message_caption(
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_kb()
        )

    # ── Top rated ──────────────────────────────────────────────
    elif data == "menu_top":
        from handlers.watchlist import show_top_rated
        await show_top_rated(q, user.id)

    # ── Help ───────────────────────────────────────────────────
    elif data == "menu_help":
        try:
            await q.message.delete()
        except Exception:
            pass
        await ctx.bot.send_message(
            chat_id=q.message.chat.id,
            text=HELP_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=help_back_kb()
        )
