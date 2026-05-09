from telegram import Update
from telegram.ext import ContextTypes
import database.db as db
from utils.anilist import search_anime, get_anime_by_id, format_anime_info
from utils.keyboards import search_results_kb, anime_action_kb, main_menu_kb

# ── /search command ────────────────────────────────────────────────
async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        db.set_state(update.effective_user.id, "searching")
        await update.message.reply_text(
            "🔍 <b>Anime Search</b>\n\nAnime ka naam type karo:",
            parse_mode="HTML"
        )
        return
    query = " ".join(ctx.args)
    await do_search(update, ctx, query)

async def do_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE, query: str):
    msg = await update.message.reply_text(f"🔍 Searching <b>{query}</b>...", parse_mode="HTML")
    results = await search_anime(query)
    if not results:
        await msg.edit_text("😔 Koi result nahi mila. Dusra naam try karo.")
        return
    await msg.edit_text(
        f"🎌 <b>'{query}'</b> ke liye {len(results)} results:\n\nSelect karo:",
        parse_mode="HTML",
        reply_markup=search_results_kb(results)
    )

# ── Text message handler (when in searching state) ─────────────────
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    state   = db.get_state(user.id)
    text    = update.message.text.strip()

    if not state:
        # No state — treat as search
        await do_search(update, ctx, text)
        return

    s = state["state"]

    # ── Searching ──────────────────────────────────────────────────
    if s == "searching":
        db.clear_state(user.id)
        await do_search(update, ctx, text)

    # ── Progress update ────────────────────────────────────────────
    elif s.startswith("progress_"):
        anime_id = int(s.replace("progress_", ""))
        db.clear_state(user.id)
        try:
            progress = int(text)
        except ValueError:
            await update.message.reply_text("❌ Sirf number type karo (e.g. 12)"); return
        entry = db.get_anime_entry(user.id, anime_id)
        if not entry:
            await update.message.reply_text("❌ Anime nahi mila."); return
        db.update_progress(user.id, anime_id, progress)
        # Auto-complete if finished
        if entry["total_eps"] and progress >= entry["total_eps"]:
            db.update_status(user.id, anime_id, "completed")
            await update.message.reply_text(
                f"🎉 <b>{entry['title']}</b> complete!\n"
                f"📺 {progress}/{entry['total_eps']} eps\n"
                f"✅ Status auto-completed!",
                parse_mode="HTML",
                reply_markup=main_menu_kb()
            )
        else:
            await update.message.reply_text(
                f"✅ Progress updated!\n📺 <b>{entry['title']}</b>: {progress} eps",
                parse_mode="HTML",
                reply_markup=main_menu_kb()
            )

    # ── Rating ─────────────────────────────────────────────────────
    elif s.startswith("rate_"):
        anime_id = int(s.replace("rate_", ""))
        db.clear_state(user.id)
        try:
            score = float(text)
            if not 1 <= score <= 10:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ 1-10 ke beech number do (e.g. 8.5)"); return
        entry = db.get_anime_entry(user.id, anime_id)
        if not entry:
            await update.message.reply_text("❌ Anime nahi mila."); return
        db.update_progress(user.id, anime_id, entry["progress"], score)
        stars = "⭐" * int(score)
        await update.message.reply_text(
            f"⭐ <b>{entry['title']}</b> rated!\n{stars} {score}/10",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )

    else:
        await do_search(update, ctx, text)

# ── Callback: srch_ buttons ────────────────────────────────────────
async def cb_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    user = update.effective_user
    await q.answer()

    if data.startswith("srch_info_"):
        anime_id = int(data.replace("srch_info_", ""))
        anime    = await get_anime_by_id(anime_id)
        if not anime:
            await q.edit_message_text("❌ Info load nahi ho saki."); return

        info    = format_anime_info(anime)
        in_list = db.get_anime_entry(user.id, anime_id) is not None

        # Airing info
        nxt = anime.get("nextAiringEpisode")
        if nxt:
            import datetime
            t = datetime.datetime.fromtimestamp(nxt["airingAt"])
            info += f"\n\n📡 <b>Next Ep {nxt['episode']}</b>: {t.strftime('%d %b %Y %H:%M')}"

        await q.edit_message_text(
            info,
            parse_mode="HTML",
            reply_markup=anime_action_kb(anime_id, in_list)
      )
