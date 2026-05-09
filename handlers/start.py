from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.db import upsert_user, get_user_stats
from utils.keyboards import main_menu_kb, watchlist_filter_kb
import database.db as db

# ══════════════════════════════════════════════════════════════
#   MESSAGES
# ══════════════════════════════════════════════════════════════

WELCOME = (
    "🌸 <b>Konnichiwa, {name}!</b>\n\n"
    "╔════════════════════════╗\n"
    "║  🎌  ANIME WATCHLIST   ║\n"
    "╚════════════════════════╝\n\n"
    "Your personal anime universe tracker — powered by AniList.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🔍  Search any anime instantly\n"
    "📋  Build your watchlist\n"
    "📊  Track episode progress\n"
    "⭐  Rate & review anime\n"
    "⏰  Set episode reminders\n"
    "🏆  Flex your top-rated list\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "👇 <b>Choose from the menu below</b> to get started!"
)

HELP_TEXT = (
    "📖 <b>Command Reference</b>\n\n"
    "┌─ 🔍 <b>SEARCH</b>\n"
    "│  /search &lt;name&gt; — Find any anime\n"
    "│\n"
    "├─ 📋 <b>WATCHLIST</b>\n"
    "│  /list        — View your full list\n"
    "│  /add &lt;name&gt;  — Add anime\n"
    "│  /remove &lt;id&gt; — Remove anime\n"
    "│  /status &lt;id&gt; — Change status\n"
    "│  /progress &lt;id&gt; &lt;ep&gt; — Update episode\n"
    "│\n"
    "├─ 📊 <b>STATS</b>\n"
    "│  /stats — Your personal stats\n"
    "│  /top   — Your top-rated anime\n"
    "│\n"
    "└─ ⏰ <b>REMINDERS</b>\n"
    "   /remind — Manage all reminders\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "💡 <i>Pro tip: Just type any anime name — I'll search it instantly!</i>"
)

# ══════════════════════════════════════════════════════════════
#   ANIME SPOTLIGHT VIDEOS
#   Format: { anime_name: (video_file_id_or_url, description) }
#   Replace file_id values with actual Telegram video file IDs
#   or use direct .mp4 URLs (must be publicly accessible)
# ══════════════════════════════════════════════════════════════

SPOTLIGHT_VIDEOS = {
    "attack_on_titan": {
        "title": "⚔️ Attack on Titan",
        "url": "https://files.catbox.moe/g1b6dp.mp4",   # replace with real clip
        "thumbnail": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx16498-73IhOXpJZiMF.jpg",
        "description": (
            "🎌 <b>Attack on Titan</b> (<i>Shingeki no Kyojin</i>)\n\n"
            "📺 <b>Studio:</b> MAPPA / Wit Studio\n"
            "📅 <b>Aired:</b> Apr 2013 – Nov 2023\n"
            "🎭 <b>Genre:</b> Action · Dark Fantasy · Post-Apocalyptic\n"
            "⭐ <b>Score:</b> 9.0 / 10\n\n"
            "In a world where humanity lives inside massive walled cities to protect "
            "themselves from Titans — giant humanoid creatures — young Eren Yeager "
            "swears revenge after witnessing the destruction of his hometown. "
            "What unfolds is one of anime's most jaw-dropping stories of freedom, "
            "war, and the true nature of evil.\n\n"
            "🏆 <b>Awards:</b> Crunchyroll Anime of the Year 2023\n"
            "💬 <b>Episodes:</b> 87 + 2 specials\n"
            "🌍 <b>Status:</b> ✅ Completed"
        ),
    },
    "demon_slayer": {
        "title": "🌊 Demon Slayer",
        "url": "https://files.catbox.moe/qkeqgs.mp4",
        "thumbnail": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx101922-PEn1CTc93blC.jpg",
        "description": (
            "🎌 <b>Demon Slayer</b> (<i>Kimetsu no Yaiba</i>)\n\n"
            "📺 <b>Studio:</b> ufotable\n"
            "📅 <b>Aired:</b> Apr 2019 – Ongoing\n"
            "🎭 <b>Genre:</b> Action · Supernatural · Historical\n"
            "⭐ <b>Score:</b> 8.7 / 10\n\n"
            "After his family is slaughtered by demons, young Tanjiro Kamado sets "
            "out to become a Demon Slayer to avenge them — and cure his sister Nezuko "
            "who has been turned into a demon. Featuring ufotable's legendary "
            "animation and breathtaking sword-fighting choreography.\n\n"
            "🏆 <b>Notable:</b> Mugen Train — highest-grossing anime film ever\n"
            "💬 <b>Episodes:</b> 55+ (ongoing)\n"
            "🌍 <b>Status:</b> 📡 Airing"
        ),
    },
}

# ══════════════════════════════════════════════════════════════
#   KEYBOARDS
# ══════════════════════════════════════════════════════════════

def spotlight_kb():
    """Keyboard shown below a spotlight video."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add to Watchlist", callback_data="menu_search"),
            InlineKeyboardButton("🔍 Search More",      callback_data="menu_search"),
        ],
        [InlineKeyboardButton("🏠 Main Menu",           callback_data="menu_main")],
    ])

# ══════════════════════════════════════════════════════════════
#   COMMANDS
# ══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    # Send welcome message with main menu
    await update.message.reply_text(
        WELCOME.format(name=user.first_name or "Otaku"),
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )

    # Send a spotlight video automatically on first /start
    await send_spotlight_video(update, ctx, "attack_on_titan")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


async def cmd_spotlight(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /spotlight <anime_key>
    Sends an anime spotlight video with full description.
    Usage: /spotlight demon_slayer
    """
    key = ctx.args[0].lower() if ctx.args else "attack_on_titan"
    if key not in SPOTLIGHT_VIDEOS:
        keys = ", ".join(SPOTLIGHT_VIDEOS.keys())
        await update.message.reply_text(
            f"❓ Unknown anime key.\n\nAvailable: <code>{keys}</code>",
            parse_mode="HTML"
        )
        return
    await send_spotlight_video(update, ctx, key)


# ══════════════════════════════════════════════════════════════
#   SPOTLIGHT VIDEO SENDER
# ══════════════════════════════════════════════════════════════

async def send_spotlight_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE, key: str):
    """
    Sends a spotlight anime video with formatted description below it.
    The video and description are sent as two separate messages for best UX.
    """
    data = SPOTLIGHT_VIDEOS.get(key)
    if not data:
        return

    chat_id = update.effective_chat.id

    try:
        # ── Send the video ──────────────────────────────────────
        # Telegram supports: file_id, HTTP URL (.mp4), or InputFile
        # Caption is kept short (Telegram limits captions to 1024 chars)
        short_caption = f"🎬 <b>Anime Spotlight</b> — {data['title']}"

        await ctx.bot.send_video(
            chat_id=chat_id,
            video=data["url"],          # swap with file_id for faster delivery
            caption=short_caption,
            parse_mode="HTML",
            supports_streaming=True,
            width=1280,
            height=720,
        )

    except Exception as e:
        # If video fails (e.g. URL not accessible), send thumbnail photo instead
        try:
            await ctx.bot.send_photo(
                chat_id=chat_id,
                photo=data["thumbnail"],
                caption=short_caption,
                parse_mode="HTML",
            )
        except Exception:
            pass  # silently skip if both fail

    # ── Send full description as a separate message below ──────
    await ctx.bot.send_message(
        chat_id=chat_id,
        text=data["description"],
        parse_mode="HTML",
        reply_markup=spotlight_kb(),
        disable_web_page_preview=True,
    )


# ══════════════════════════════════════════════════════════════
#   CALLBACK HANDLER  (menu_ buttons)
# ══════════════════════════════════════════════════════════════

async def cb_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    await q.answer()
    user = update.effective_user

    # ── Main menu ──────────────────────────────────────────────
    if data == "menu_main":
        await q.edit_message_text(
            WELCOME.format(name=user.first_name or "Otaku"),
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )

    # ── Watchlist filter ───────────────────────────────────────
    elif data == "menu_watchlist":
        await q.edit_message_text(
            "📋 <b>My Watchlist</b>\n\nKaun si list dekhni hai?",
            parse_mode="HTML",
            reply_markup=watchlist_filter_kb()
        )

    # ── Search ─────────────────────────────────────────────────
    elif data == "menu_search":
        db.set_state(user.id, "searching")
        await q.edit_message_text(
            "🔍 <b>Anime Search</b>\n\n"
            "Anime ka naam type karo — main AniList se dhundh dunga!\n\n"
            "<i>Example: Naruto, One Piece, Solo Leveling...</i>",
            parse_mode="HTML"
        )

    # ── Stats ──────────────────────────────────────────────────
    elif data == "menu_stats":
        stats = get_user_stats(user.id)

        # Progress bar helper
        def bar(n, total, width=10):
            if not total:
                return "░" * width
            filled = round((n / total) * width)
            return "█" * filled + "░" * (width - filled)

        total = stats["total_anime"] or 1
        text = (
            f"📊 <b>{user.first_name}'s Anime Stats</b>\n\n"
            f"👁️  Watching   {bar(stats['watching'],   total)}  {stats['watching']}\n"
            f"✅  Completed  {bar(stats['completed'],  total)}  {stats['completed']}\n"
            f"⏸️  On Hold    {bar(stats['on_hold'],    total)}  {stats['on_hold']}\n"
            f"❌  Dropped   {bar(stats['dropped'],    total)}  {stats['dropped']}\n"
            f"📋  Planned   {bar(stats['plan'],       total)}  {stats['plan']}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎌 Total Anime  : <b>{stats['total_anime']}</b>\n"
            f"📺 Episodes     : <b>{stats['total_episodes']}</b> watched\n"
        )
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=main_menu_kb())

    # ── Reminders ──────────────────────────────────────────────
    elif data == "menu_reminders":
        reminders = db.get_user_reminders(user.id)
        if not reminders:
            text = (
                "⏰ <b>Reminders</b>\n\n"
                "No active reminders.\n\n"
                "💡 Search an anime and tap <b>Set Reminder</b> to create one!"
            )
        else:
            text = f"⏰ <b>Active Reminders ({len(reminders)})</b>\n\n"
            for i, r in enumerate(reminders, 1):
                text += f"{i}. 🔔 <b>{r['title']}</b>\n   📅 {r['remind_at']}\n\n"
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=main_menu_kb())

    # ── Top rated ──────────────────────────────────────────────
    elif data == "menu_top":
        from handlers.watchlist import show_top_rated
        await show_top_rated(q, user.id)

    # ── Spotlight ──────────────────────────────────────────────
    elif data == "menu_spotlight":
        # Triggered from main menu button (if added)
        await send_spotlight_video(
            update, ctx, "demon_slayer"
        )

    # ── Help ───────────────────────────────────────────────────
    elif data == "menu_help":
        await q.edit_message_text(HELP_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())
