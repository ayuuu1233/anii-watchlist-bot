# ╔══════════════════════════════════════════════════╗
# ║     📚 M A N G A  /  M A N H W A  H A N D L E R ║
# ║   Manga · Manhwa · Manhua · Webtoon · Adult 🔞  ║
# ╚══════════════════════════════════════════════════╝

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction
from telegram.error import BadRequest

import database.db as db
from utils.manga_api import (
    combined_search, anilist_get_manga, mangadex_get,
    build_manga_list_caption, build_manga_detail_caption,
    ADULT_RATINGS, get_type_label,
)

logger = logging.getLogger(__name__)

# Track which users have passed 18+ gate (in-memory, resets on restart)
# For persistence, store in DB user_states
ADULT_VERIFIED: set = set()


# ╔══════════════════════════════════════════════════╗
# ║                  KEYBOARDS                       ║
# ╚══════════════════════════════════════════════════╝

def manga_main_kb() -> InlineKeyboardMarkup:
    """Main manga/manhwa category selection menu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇯🇵 Manga",        callback_data="mg_cat_manga"),
            InlineKeyboardButton("🇰🇷 Manhwa",       callback_data="mg_cat_manhwa"),
        ],
        [
            InlineKeyboardButton("🇨🇳 Manhua",       callback_data="mg_cat_manhua"),
            InlineKeyboardButton("📱 Webtoon",       callback_data="mg_cat_webtoon"),
        ],
        [
            InlineKeyboardButton("🔞 Adult Manhwa",  callback_data="mg_cat_adult"),
            InlineKeyboardButton("📚 All Types",     callback_data="mg_cat_all"),
        ],
        [
            InlineKeyboardButton("🔍 Search",        callback_data="mg_search"),
            InlineKeyboardButton("🏠 Main Menu",     callback_data="menu_main"),
        ],
    ])


def adult_gate_kb() -> InlineKeyboardMarkup:
    """18+ age verification buttons."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Haan, main 18+ hoon",  callback_data="mg_adult_confirm"),
            InlineKeyboardButton("❌ Nahi, wapas jao",      callback_data="mg_adult_deny"),
        ],
    ])


def manga_results_kb(results: list) -> InlineKeyboardMarkup:
    """One button per result."""
    buttons = []
    for r in results[:10]:
        source = r.get("source", "anilist")
        mid    = r.get("id", "")
        title  = r["title"][:30]
        adult  = " 🔞" if r.get("content_rating") in ADULT_RATINGS else ""
        label  = get_type_label(r.get("origin", ""))
        buttons.append([
            InlineKeyboardButton(
                f"{label} {title}{adult}",
                callback_data=f"mg_info_{source}_{mid}"
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="mg_main")])
    return InlineKeyboardMarkup(buttons)


def manga_action_kb(source: str, mid: str, in_list: bool, is_adult: bool = False) -> InlineKeyboardMarkup:
    """Action buttons below manga detail card."""
    key      = f"{source}_{mid}"
    read_cb  = f"wtw_adult_manga_{key}" if is_adult else f"wtw_manga_{key}"

    if in_list:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Update Status",  callback_data=f"mg_status_{key}"),
                InlineKeyboardButton("📖 Progress",       callback_data=f"mg_progress_{key}"),
            ],
            [
                InlineKeyboardButton("⭐ Rate",           callback_data=f"mg_rate_{key}"),
                InlineKeyboardButton("🗑️ Remove",         callback_data=f"mg_remove_{key}"),
            ],
            [InlineKeyboardButton("📖 Where to Read",     callback_data=read_cb)],
            [InlineKeyboardButton("🔙 Back to Results",   callback_data="mg_main")],
        ])
    else:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add to List",    callback_data=f"mg_add_{key}"),
                InlineKeyboardButton("📖 Where to Read",  callback_data=read_cb),
            ],
            [InlineKeyboardButton("🔙 Back to Results",   callback_data="mg_main")],
        ])


def manga_status_kb(source: str, mid: str) -> InlineKeyboardMarkup:
    key = f"{source}_{mid}"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Reading",     callback_data=f"mg_setstatus_{key}_reading"),
            InlineKeyboardButton("✅ Completed",   callback_data=f"mg_setstatus_{key}_completed"),
        ],
        [
            InlineKeyboardButton("⏸️ On Hold",     callback_data=f"mg_setstatus_{key}_on_hold"),
            InlineKeyboardButton("❌ Dropped",     callback_data=f"mg_setstatus_{key}_dropped"),
        ],
        [
            InlineKeyboardButton("📋 Plan",        callback_data=f"mg_setstatus_{key}_plan"),
        ],
        [InlineKeyboardButton("🔙 Cancel",         callback_data=f"mg_info_{source}_{mid}")],
    ])


# ╔══════════════════════════════════════════════════╗
# ║               /manga COMMAND                     ║
# ╚══════════════════════════════════════════════════╝

async def cmd_manga(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "┏━━━❖ 📚 ❖━━━┓\n"
        "  <b>Manga / Manhwa Hub</b>\n"
        "┗━━━❖ 📚 ❖━━━┛\n\n"
        "🇯🇵 Manga · 🇰🇷 Manhwa · 🇨🇳 Manhua\n"
        "📱 Webtoon · 🔞 Adult\n\n"
        "Category choose karo~",
        parse_mode=ParseMode.HTML,
        reply_markup=manga_main_kb()
    )


# ╔══════════════════════════════════════════════════╗
# ║            CALLBACK HANDLER                      ║
# ╚══════════════════════════════════════════════════╝

async def cb_manga(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    user = update.effective_user
    await q.answer()

    # ── Main manga menu ────────────────────────────────────────
    if data == "mg_main":
        await _send_or_edit_text(
            q,
            "┏━━━❖ 📚 ❖━━━┓\n"
            "  <b>Manga / Manhwa Hub</b>\n"
            "┗━━━❖ 📚 ❖━━━┛\n\n"
            "🇯🇵 Manga · 🇰🇷 Manhwa · 🇨🇳 Manhua\n"
            "📱 Webtoon · 🔞 Adult\n\n"
            "Category choose karo~",
            manga_main_kb()
        )

    # ── Search prompt ──────────────────────────────────────────
    elif data == "mg_search":
        db.set_state(user.id, "mg_searching_all")
        await _send_or_edit_text(
            q,
            "┏━━━❖ 🔍 ❖━━━┓\n"
            "  <b>Manga Search</b>\n"
            "┗━━━❖ 🔍 ❖━━━┛\n\n"
            "Manga / Manhwa / Webtoon ka naam type karo~\n\n"
            "<i>e.g. Solo Leveling, Berserk, Tower of God...</i>",
            None
        )

    # ── Category buttons ───────────────────────────────────────
    elif data.startswith("mg_cat_"):
        cat = data.replace("mg_cat_", "")

        if cat == "adult":
            # 18+ gate
            if user.id in ADULT_VERIFIED:
                db.set_state(user.id, "mg_searching_adult")
                await _send_or_edit_text(
                    q,
                    "🔞 <b>Adult Manhwa Search</b>\n\n"
                    "Title type karo~",
                    InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back", callback_data="mg_main")
                    ]])
                )
            else:
                await _send_or_edit_text(
                    q,
                    "┏━━━❖ 🔞 ❖━━━┓\n"
                    "  <b>Age Verification</b>\n"
                    "┗━━━❖ 🔞 ❖━━━┛\n\n"
                    "⚠️ Yeh section <b>18+ Adult Content</b> hai.\n\n"
                    "Aage badhne ke liye confirm karo ki\n"
                    "tum <b>18 saal ya usse bade</b> ho~\n\n"
                    "<i>Is content ko dekh ke tum khud zimmedaar ho.</i>",
                    adult_gate_kb()
                )
        else:
            state_map = {
                "manga":   "mg_searching_manga",
                "manhwa":  "mg_searching_manhwa",
                "manhua":  "mg_searching_manhua",
                "webtoon": "mg_searching_webtoon",
                "all":     "mg_searching_all",
            }
            state = state_map.get(cat, "mg_searching_all")
            db.set_state(user.id, state)

            label_map = {
                "manga":   "🇯🇵 Manga",
                "manhwa":  "🇰🇷 Manhwa",
                "manhua":  "🇨🇳 Manhua",
                "webtoon": "📱 Webtoon",
                "all":     "📚 All Types",
            }
            label = label_map.get(cat, "📚")

            await _send_or_edit_text(
                q,
                f"┏━━━❖ 📚 ❖━━━┓\n"
                f"  <b>{label} Search</b>\n"
                f"┗━━━❖ 📚 ❖━━━┛\n\n"
                f"Title type karo~\n\n"
                f"<i>AniList + MangaDex dono search karunga!</i>",
                InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="mg_main")
                ]])
            )

    # ── 18+ confirm / deny ─────────────────────────────────────
    elif data == "mg_adult_confirm":
        ADULT_VERIFIED.add(user.id)
        db.set_state(user.id, "mg_searching_adult")
        await _send_or_edit_text(
            q,
            "✅ <b>Verified!</b>\n\n"
            "🔞 Adult Manhwa section unlock ho gaya~\n\n"
            "Title type karo:",
            InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="mg_main")
            ]])
        )

    elif data == "mg_adult_deny":
        await _send_or_edit_text(q, "👍 Sahi decision~", manga_main_kb())

    # ── Manga detail card ──────────────────────────────────────
    elif data.startswith("mg_info_"):
        parts  = data.replace("mg_info_", "").split("_", 1)
        source = parts[0]
        mid    = parts[1]

        await q.answer("Loading details~")

        if source == "anilist":
            raw = await anilist_get_manga(int(mid))
            if not raw:
                await q.answer("❌ Info nahi mila!", show_alert=True); return
            r = {
                "source":         "anilist",
                "id":             str(raw["id"]),
                "al_id":          raw["id"],
                "title":          raw["title"].get("english") or raw["title"].get("romaji","?"),
                "cover_url":      raw["coverImage"].get("large",""),
                "status":         raw.get("status","").replace("_"," ").title(),
                "chapters":       raw.get("chapters") or "?",
                "volumes":        raw.get("volumes") or "?",
                "content_rating": "safe",
                "origin":         raw.get("countryOfOrigin",""),
                "year":           raw.get("startDate",{}).get("year","?"),
                "genres":         raw.get("genres",[])[:5],
                "description":    (raw.get("description") or "")[:350],
                "author":         "",
                "score":          raw.get("averageScore"),
            }
        else:
            r = await mangadex_get(mid)
            if not r:
                await q.answer("❌ Info nahi mila!", show_alert=True); return

        # Check if in user's manga list (use "mg_" prefix in DB)
        db_id    = f"mg_{source}_{mid}"
        in_list  = db.get_anime_entry(user.id, hash(db_id) % 10**9) is not None
        caption  = build_manga_detail_caption(r)
        keyboard = manga_action_kb(source, mid, in_list)
        cover    = r.get("cover_url","")

        try:
            if cover:
                await q.edit_message_media(
                    media=InputMediaPhoto(
                        media=cover,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                    ),
                    reply_markup=keyboard,
                )
            else:
                raise Exception("no cover")
        except BadRequest:
            try:
                await q.edit_message_caption(
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            except Exception:
                await q.message.reply_text(
                    caption, parse_mode=ParseMode.HTML, reply_markup=keyboard
                )

    # ── Add to list ────────────────────────────────────────────
    elif data.startswith("mg_add_"):
        key    = data.replace("mg_add_", "")
        parts  = key.split("_", 1)
        source = parts[0]; mid = parts[1]
        # Use a numeric ID derived from the key
        fake_id = hash(f"mg_{source}_{mid}") % 10**9
        title   = "Manga"  # ideally fetch from cache
        db.add_anime(user.id, fake_id, title, "", "", 0, "plan")
        await q.answer("✅ Added to your list~", show_alert=False)

    # ── Status change ──────────────────────────────────────────
    elif data.startswith("mg_status_"):
        key    = data.replace("mg_status_", "")
        parts  = key.split("_", 1)
        source = parts[0]; mid = parts[1]
        await _send_or_edit_text(
            q, "📝 Status choose karo~",
            manga_status_kb(source, mid)
        )

    elif data.startswith("mg_setstatus_"):
        # mg_setstatus_anilist_12345_reading
        rest   = data.replace("mg_setstatus_", "")
        # last part is status
        *key_parts, new_status = rest.split("_")
        key    = "_".join(key_parts)
        parts  = key.split("_", 1)
        source = parts[0]; mid = parts[1]
        fake_id = hash(f"mg_{source}_{mid}") % 10**9
        db.update_status(user.id, fake_id, new_status)
        status_labels = {
            "reading":"📖 Reading","completed":"✅ Completed",
            "on_hold":"⏸️ On Hold","dropped":"❌ Dropped","plan":"📋 Plan"
        }
        await q.answer(f"✅ Status → {status_labels.get(new_status, new_status)}", show_alert=False)

    # ── Remove ─────────────────────────────────────────────────
    elif data.startswith("mg_remove_"):
        key     = data.replace("mg_remove_", "")
        parts   = key.split("_", 1)
        source  = parts[0]; mid = parts[1]
        fake_id = hash(f"mg_{source}_{mid}") % 10**9
        db.remove_anime(user.id, fake_id)
        await q.answer("🗑️ Removed from list~", show_alert=False)


# ╔══════════════════════════════════════════════════╗
# ║          TEXT HANDLER (manga search)             ║
# ╚══════════════════════════════════════════════════╝

async def handle_manga_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Called from main text handler.
    Returns True if it handled the message, False otherwise.
    """
    user  = update.effective_user
    state = db.get_state(user.id)
    if not state:
        return False

    s = state["state"]
    if not s.startswith("mg_searching_"):
        return False

    cat  = s.replace("mg_searching_", "")   # manga / manhwa / adult / all etc.
    text = update.message.text.strip()
    db.clear_state(user.id)

    content_type = "adult" if cat == "adult" else "safe"
    manga_type   = cat if cat not in ("all", "adult") else "all"

    try:
        await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_PHOTO)
    except Exception:
        pass

    results = await combined_search(text, content_type=content_type, manga_type=manga_type)

    if not results:
        await update.message.reply_text(
            "😔 <b>Koi result nahi mila~</b>\n\nDusra title try karo!",
            parse_mode=ParseMode.HTML,
            reply_markup=manga_main_kb()
        )
        return True

    top_cover = results[0].get("cover_url", "")
    caption   = build_manga_list_caption(text, results)
    keyboard  = manga_results_kb(results)

    try:
        if top_cover:
            await update.message.reply_photo(
                photo=top_cover,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:
            raise Exception("no cover")
    except Exception:
        await update.message.reply_text(
            caption, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )

    return True


# ╔══════════════════════════════════════════════════╗
# ║                   HELPERS                        ║
# ╚══════════════════════════════════════════════════╝

async def _send_or_edit_text(q, text: str, keyboard):
    """Try edit_message_text; if it's a photo message use reply instead."""
    try:
        await q.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )
    except BadRequest:
        try:
            await q.edit_message_caption(
                caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard
            )
        except Exception:
            await q.message.reply_text(
                text, parse_mode=ParseMode.HTML, reply_markup=keyboard
  )
