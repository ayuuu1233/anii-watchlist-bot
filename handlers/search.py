# ╔══════════════════════════════════════════════════╗
# ║        🔍 S E A R C H  H A N D L E R            ║
# ║     Anime cover photos + full info cards~        ║
# ╚══════════════════════════════════════════════════╝

import datetime
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction
from telegram.error import BadRequest

import database.db as db
from utils.anilist import search_anime, get_anime_by_id
from utils.keyboards import anime_action_kb, main_menu_kb

logger = logging.getLogger(__name__)


# ╔══════════════════════════════════════════════════╗
# ║              CAPTION BUILDERS                    ║
# ╚══════════════════════════════════════════════════╝

def build_result_list_caption(query: str, results: list) -> str:
    """Short caption shown with the search results photo grid."""
    text = (
        f"┏━━━❖ 🔍 ❖━━━┓\n"
        f"  <b>Results for '{query}'</b>\n"
        f"┗━━━❖ 🔍 ❖━━━┛\n\n"
    )
    for i, a in enumerate(results, 1):
        title  = a["title"].get("english") or a["title"].get("romaji", "?")
        score  = f"★{a['averageScore']/10:.1f}" if a.get("averageScore") else "N/A"
        eps    = a.get("episodes") or "?"
        status = _status_icon(a.get("status", ""))
        text  += f"{i}. {status} <b>{title}</b>  {score}  📺{eps}ep\n"
    text += "\n👇 <i>Select one to see full details~</i>"
    return text


def build_anime_detail_caption(anime: dict, in_list: bool) -> str:
    """Full detail card caption shown when user taps a result."""
    title   = anime["title"].get("english") or anime["title"].get("romaji", "?")
    romaji  = anime["title"].get("romaji", "")
    native  = anime["title"].get("native", "")
    score   = f"{anime['averageScore']/10:.1f}/10" if anime.get("averageScore") else "N/A"
    eps     = anime.get("episodes") or "?"
    status  = anime.get("status", "").replace("_", " ").title()
    genres  = " · ".join(anime.get("genres", [])[:4]) or "N/A"
    season  = f"{anime.get('season','').title()} {anime.get('seasonYear','')}" if anime.get("season") else "N/A"
    studios = ", ".join(
        n["name"] for n in anime.get("studios", {}).get("nodes", [])[:2]
    ) or "N/A"

    # Description — clean HTML tags
    raw_desc = anime.get("description") or ""
    desc = raw_desc.replace("<br>", "").replace("<i>", "").replace("</i>", "").replace("\n", " ")
    desc = desc[:280] + "…" if len(desc) > 280 else desc

    # Airing info
    airing = ""
    nxt = anime.get("nextAiringEpisode")
    if nxt:
        t      = datetime.datetime.fromtimestamp(nxt["airingAt"])
        airing = (
            f"\n📡 <b>Next Ep {nxt['episode']}</b> → "
            f"{t.strftime('%d %b %Y  %H:%M')}\n"
        )

    in_list_line = "\n✅ <i>Already in your watchlist~</i>\n" if in_list else ""

    return (
        f"┏━━━❖ 🎌 ❖━━━┓\n"
        f"  <b>{title}</b>\n"
        f"┗━━━❖ 🎌 ❖━━━┛\n\n"
        f"🗾 <i>{romaji}</i>  {f'· {native}' if native else ''}\n\n"
        f"⭐ Score    : <b>{score}</b>\n"
        f"📺 Episodes : <b>{eps}</b>\n"
        f"📡 Status   : <b>{status}</b>\n"
        f"🗓️ Season   : <b>{season}</b>\n"
        f"🎬 Studio   : <b>{studios}</b>\n"
        f"🎭 Genres   : {genres}\n"
        f"{airing}"
        f"{in_list_line}\n"
        f"📖 {desc}"
    )


def _status_icon(status: str) -> str:
    return {
        "RELEASING":        "🟢",
        "FINISHED":         "✅",
        "NOT_YET_RELEASED": "🔜",
        "CANCELLED":        "❌",
        "HIATUS":           "⏸️",
    }.get(status, "📺")


# ╔══════════════════════════════════════════════════╗
# ║           SEARCH RESULTS KEYBOARD               ║
# ╚══════════════════════════════════════════════════╝

def search_results_kb(results: list) -> InlineKeyboardMarkup:
    """One button per result — shows title + score."""
    buttons = []
    for a in results:
        title = (a["title"].get("english") or a["title"].get("romaji", "?"))[:32]
        score = f" ★{a['averageScore']/10:.1f}" if a.get("averageScore") else ""
        buttons.append([
            InlineKeyboardButton(
                f"🎌 {title}{score}",
                callback_data=f"srch_info_{a['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


# ╔══════════════════════════════════════════════════╗
# ║              /search COMMAND                     ║
# ╚══════════════════════════════════════════════════╝

async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        db.set_state(update.effective_user.id, "searching")
        await update.message.reply_text(
            "┏━━━❖ 🔍 ❖━━━┓\n"
            "  <b>Anime Search</b>\n"
            "┗━━━❖ 🔍 ❖━━━┛\n\n"
            "Anime ka naam type karo~\n"
            "Main AniList se dhundh dunga! 🌸\n\n"
            "<i>e.g. Naruto, Solo Leveling, Frieren...</i>",
            parse_mode=ParseMode.HTML
        )
        return
    await do_search(update, ctx, " ".join(ctx.args))


# ╔══════════════════════════════════════════════════╗
# ║              CORE SEARCH LOGIC                   ║
# ╚══════════════════════════════════════════════════╝

async def do_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE, query: str):
    """
    Search AniList → send cover photo of TOP result
    with a list caption + buttons for all results.
    """
    chat_id = update.effective_chat.id

    # Typing indicator
    try:
        await ctx.bot.send_chat_action(chat_id, ChatAction.UPLOAD_PHOTO)
    except Exception:
        pass

    # Fetch results
    results = await search_anime(query)

    if not results:
        await update.message.reply_text(
            "😔 <b>Koi result nahi mila~</b>\n\nDusra naam try karo senpai!",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_kb()
        )
        return

    top = results[0]
    cover_url = top["coverImage"].get("large") or top["coverImage"].get("medium", "")

    caption  = build_result_list_caption(query, results[:8])
    keyboard = search_results_kb(results[:8])

    # Send cover photo of first result + list of all results as buttons
    try:
        await update.message.reply_photo(
            photo=cover_url,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.warning(f"Photo send failed, falling back to text: {e}")
        await update.message.reply_text(
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )


# ╔══════════════════════════════════════════════════╗
# ║           TEXT MESSAGE HANDLER                   ║
# ╚══════════════════════════════════════════════════╝

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    state = db.get_state(user.id)
    text  = update.message.text.strip()

    if not state:
        await do_search(update, ctx, text)
        return

    s = state["state"]

    # ── Searching ──────────────────────────────────────────────
    if s == "searching":
        db.clear_state(user.id)
        await do_search(update, ctx, text)

    # ── Episode progress ───────────────────────────────────────
    elif s.startswith("progress_"):
        anime_id = int(s.replace("progress_", ""))
        db.clear_state(user.id)
        try:
            progress = int(text)
        except ValueError:
            await update.message.reply_text("❌ Sirf number type karo (e.g. 12)")
            return
        entry = db.get_anime_entry(user.id, anime_id)
        if not entry:
            await update.message.reply_text("❌ Anime nahi mila.")
            return
        db.update_progress(user.id, anime_id, progress)

        if entry["total_eps"] and progress >= entry["total_eps"]:
            db.update_status(user.id, anime_id, "completed")
            cover = entry["cover_url"] or ""
            congrats = (
                f"🎉 <b>{entry['title']}</b> complete!\n\n"
                f"📺 {progress}/{entry['total_eps']} eps watched\n"
                f"✅ Status → <b>Completed</b> auto-set!\n\n"
                f"Rate it? Use /progress {anime_id} {progress} &lt;score&gt;"
            )
            try:
                if cover:
                    await update.message.reply_photo(
                        photo=cover, caption=congrats,
                        parse_mode=ParseMode.HTML, reply_markup=main_menu_kb()
                    )
                else:
                    raise Exception("no cover")
            except Exception:
                await update.message.reply_text(
                    congrats, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb()
                )
        else:
            await update.message.reply_text(
                f"✅ Progress updated!\n\n"
                f"📺 <b>{entry['title']}</b>\n"
                f"🔢 Episode: <b>{progress}</b> / {entry['total_eps'] or '?'}",
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_kb()
            )

    # ── Rating ─────────────────────────────────────────────────
    elif s.startswith("rate_"):
        anime_id = int(s.replace("rate_", ""))
        db.clear_state(user.id)
        try:
            score = float(text)
            if not 1 <= score <= 10:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ 1-10 ke beech number do (e.g. 8.5)")
            return
        entry = db.get_anime_entry(user.id, anime_id)
        if not entry:
            await update.message.reply_text("❌ Anime nahi mila.")
            return
        db.update_progress(user.id, anime_id, entry["progress"], score)
        stars = "⭐" * int(score)
        cover = entry["cover_url"] or ""
        rated_text = (
            f"┏━━━❖ ⭐ ❖━━━┓\n"
            f"  <b>Rated!</b>\n"
            f"┗━━━❖ ⭐ ❖━━━┛\n\n"
            f"🎌 <b>{entry['title']}</b>\n\n"
            f"{stars}\n"
            f"Score: <b>{score}/10</b>"
        )
        try:
            if cover:
                await update.message.reply_photo(
                    photo=cover, caption=rated_text,
                    parse_mode=ParseMode.HTML, reply_markup=main_menu_kb()
                )
            else:
                raise Exception("no cover")
        except Exception:
            await update.message.reply_text(
                rated_text, parse_mode=ParseMode.HTML, reply_markup=main_menu_kb()
            )

    else:
        await do_search(update, ctx, text)


# ╔══════════════════════════════════════════════════╗
# ║         CALLBACK: srch_ BUTTONS                  ║
# ╚══════════════════════════════════════════════════╝

async def cb_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    user = update.effective_user
    await q.answer()

    # ── Anime detail card ──────────────────────────────────────
    if data.startswith("srch_info_"):
        anime_id = int(data.replace("srch_info_", ""))

        # Fetch full details from AniList
        anime = await get_anime_by_id(anime_id)
        if not anime:
            await q.answer("❌ Info load nahi ho saki~", show_alert=True)
            return

        cover_url = anime["coverImage"].get("large") or anime["coverImage"].get("medium", "")
        in_list   = db.get_anime_entry(user.id, anime_id) is not None
        caption   = build_anime_detail_caption(anime, in_list)
        keyboard  = anime_action_kb(anime_id, in_list)

        # Try to replace the current photo with anime's own cover
        try:
            await q.edit_message_media(
                media=InputMediaPhoto(
                    media=cover_url,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                ),
                reply_markup=keyboard,
            )
        except BadRequest as e:
            # Media edit failed — try caption-only edit
            logger.warning(f"edit_message_media failed: {e}")
            try:
                await q.edit_message_caption(
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            except Exception as e2:
                logger.error(f"edit_message_caption also failed: {e2}")
                # Last resort — send new photo message
                try:
                    await q.message.reply_photo(
                        photo=cover_url,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard,
                    )
                except Exception:
                    await q.message.reply_text(
                        caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard,
    )            
