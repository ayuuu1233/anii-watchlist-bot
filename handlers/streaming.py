# ╔══════════════════════════════════════════════════╗
# ║   📺 W H E R E  T O  W A T C H  /  R E A D      ║
# ║        Streaming & Reading links handler         ║
# ╚══════════════════════════════════════════════════╝

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

import database.db as db
from utils.anilist import get_anime_by_id
from utils.streaming import (
    build_watch_caption, build_read_caption,
    watch_links_kb, read_links_kb,
)
from utils.manga_api import ADULT_RATINGS

logger = logging.getLogger(__name__)

# In-memory adult-verified set (shared with manga handler)
try:
    from handlers.manga import ADULT_VERIFIED
except ImportError:
    ADULT_VERIFIED: set = set()


# ╔══════════════════════════════════════════════════╗
# ║            CALLBACK HANDLER (wtw_)               ║
# ╚══════════════════════════════════════════════════╝

async def cb_streaming(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Handles all wtw_ (where to watch/read) callbacks.

    Patterns:
      wtw_anime_<anilist_id>         — anime streaming links
      wtw_manga_<source>_<id>        — manga reading links
      wtw_adult_manga_<source>_<id>  — adult manga (18+ verified)
    """
    q    = update.callback_query
    data = q.data
    user = update.effective_user
    await q.answer()

    # ── ANIME — Where to Watch ─────────────────────────────────
    if data.startswith("wtw_anime_"):
        anime_id = int(data.replace("wtw_anime_", ""))

        # Get title from AniList
        anime = await get_anime_by_id(anime_id)
        if not anime:
            await q.answer("❌ Anime info nahi mila~", show_alert=True)
            return

        title    = anime["title"].get("english") or anime["title"].get("romaji", "?")
        caption  = build_watch_caption(title)
        keyboard = watch_links_kb(title, back_cb=f"srch_info_{anime_id}")

        await _edit_or_reply(q, caption, keyboard)

    # ── MANGA — Where to Read (safe) ───────────────────────────
    elif data.startswith("wtw_manga_"):
        rest   = data.replace("wtw_manga_", "")
        # rest = "anilist_12345" or "mangadex_uuid-..."
        parts  = rest.split("_", 1)
        source = parts[0]
        mid    = parts[1]

        title = await _get_manga_title(source, mid)
        if not title:
            await q.answer("❌ Info nahi mila~", show_alert=True)
            return

        caption  = build_read_caption(title, is_adult=False)
        keyboard = read_links_kb(title, is_adult=False, back_cb=f"mg_info_{source}_{mid}")

        await _edit_or_reply(q, caption, keyboard)

    # ── ADULT MANGA — Where to Read (18+) ──────────────────────
    elif data.startswith("wtw_adult_manga_"):
        # Gate check
        if user.id not in ADULT_VERIFIED:
            await q.answer("🔞 Pehle 18+ verify karo!", show_alert=True)
            return

        rest   = data.replace("wtw_adult_manga_", "")
        parts  = rest.split("_", 1)
        source = parts[0]
        mid    = parts[1]

        title = await _get_manga_title(source, mid)
        if not title:
            await q.answer("❌ Info nahi mila~", show_alert=True)
            return

        caption  = build_read_caption(title, is_adult=True)
        keyboard = read_links_kb(title, is_adult=True, back_cb=f"mg_info_{source}_{mid}")

        await _edit_or_reply(q, caption, keyboard)


# ╔══════════════════════════════════════════════════╗
# ║                  HELPERS                         ║
# ╚══════════════════════════════════════════════════╝

async def _get_manga_title(source: str, mid: str) -> str | None:
    """Fetch manga title from AniList or MangaDex."""
    try:
        if source == "anilist":
            from utils.manga_api import anilist_get_manga
            raw = await anilist_get_manga(int(mid))
            if raw:
                return raw["title"].get("english") or raw["title"].get("romaji")
        else:
            from utils.manga_api import mangadex_get
            raw = await mangadex_get(mid)
            if raw:
                return raw.get("title")
    except Exception as e:
        logger.error(f"_get_manga_title error: {e}")
    return None


async def _edit_or_reply(q, text: str, keyboard: InlineKeyboardMarkup):
    """Try to edit caption, then text, fallback to new message."""
    try:
        await q.edit_message_caption(
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except BadRequest:
        try:
            await q.edit_message_text(
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            await q.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
