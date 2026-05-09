from telegram import Update
from telegram.ext import ContextTypes
import database.db as db
from utils.keyboards import (
    watchlist_filter_kb, status_picker_kb, add_status_kb,
    entry_actions_kb, main_menu_kb
)
from utils.anilist import get_anime_by_id
from config import STATUS_LABELS

# ── /list command ──────────────────────────────────────────────────
async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 <b>My Watchlist</b>\n\nFilter karo:",
        parse_mode="HTML",
        reply_markup=watchlist_filter_kb()
    )

# ── /add <name> command ────────────────────────────────────────────
async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("❓ Usage: /add &lt;anime name&gt;", parse_mode="HTML")
        return
    query = " ".join(ctx.args)
    db.set_state(update.effective_user.id, "searching")
    await update.message.reply_text(f"🔍 Searching: <b>{query}</b>...", parse_mode="HTML")
    # Trigger search inline
    from handlers.search import do_search
    await do_search(update, ctx, query)

# ── /remove <anime_id> command ─────────────────────────────────────
async def cmd_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("❓ Usage: /remove &lt;anime_id&gt;", parse_mode="HTML")
        return
    try:
        anime_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("❌ Anime ID number hona chahiye."); return
    ok = db.remove_anime(update.effective_user.id, anime_id)
    if ok:
        await update.message.reply_text("✅ Anime removed from your watchlist!")
    else:
        await update.message.reply_text("❌ Yeh anime tumhari list mein nahi hai.")

# ── /status <anime_id> command ─────────────────────────────────────
async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("❓ Usage: /status &lt;anime_id&gt;", parse_mode="HTML")
        return
    try:
        anime_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("❌ Anime ID number hona chahiye."); return
    entry = db.get_anime_entry(update.effective_user.id, anime_id)
    if not entry:
        await update.message.reply_text("❌ Yeh anime tumhari list mein nahi hai."); return
    await update.message.reply_text(
        f"📝 <b>{entry['title']}</b> ka status change karo:",
        parse_mode="HTML",
        reply_markup=status_picker_kb(anime_id)
    )

# ── /progress <anime_id> <episodes> [score] command ───────────────
async def cmd_progress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "❓ Usage: /progress &lt;anime_id&gt; &lt;episodes&gt; [score 1-10]",
            parse_mode="HTML"
        )
        return
    try:
        anime_id = int(ctx.args[0])
        progress = int(ctx.args[1])
        score    = float(ctx.args[2]) if len(ctx.args) > 2 else None
    except ValueError:
        await update.message.reply_text("❌ Numbers dalo properly."); return

    entry = db.get_anime_entry(update.effective_user.id, anime_id)
    if not entry:
        await update.message.reply_text("❌ Yeh anime tumhari list mein nahi hai."); return

    db.update_progress(update.effective_user.id, anime_id, progress, score)
    text = f"✅ Progress updated!\n📺 <b>{entry['title']}</b>\n🔢 Episode: {progress}"
    if score:
        text += f"\n⭐ Score: {score}/10"
    await update.message.reply_text(text, parse_mode="HTML")

# ── /stats command ─────────────────────────────────────────────────
async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    stats = db.get_user_stats(user.id)
    text = (
        f"📊 <b>{user.first_name}'s Anime Stats</b>\n\n"
        f"👁️ Watching    : <b>{stats['watching']}</b>\n"
        f"✅ Completed   : <b>{stats['completed']}</b>\n"
        f"⏸️ On Hold     : <b>{stats['on_hold']}</b>\n"
        f"❌ Dropped     : <b>{stats['dropped']}</b>\n"
        f"📋 Plan        : <b>{stats['plan']}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎌 Total Anime : <b>{stats['total_anime']}</b>\n"
        f"📺 Episodes    : <b>{stats['total_episodes']}</b> watched"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_menu_kb())

# ── /top command ───────────────────────────────────────────────────
async def cmd_top_rated(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = db.get_top_rated(update.effective_user.id)
    if not rows:
        await update.message.reply_text(
            "⭐ Abhi koi rated anime nahi hai!\nAnime rate karne ke liye /progress use karo.",
            reply_markup=main_menu_kb()
        ); return
    text = "🏆 <b>Your Top Rated Anime</b>\n\n"
    for i, r in enumerate(rows, 1):
        stars = "⭐" * int(r["score"])
        text += f"{i}. <b>{r['title']}</b>\n   {stars} {r['score']}/10\n\n"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_menu_kb())

async def show_top_rated(q, user_id):
    rows = db.get_top_rated(user_id)
    if not rows:
        await q.edit_message_text(
            "⭐ Abhi koi rated anime nahi hai!\n/progress se rate karo.",
            reply_markup=main_menu_kb()
        ); return
    text = "🏆 <b>Your Top Rated Anime</b>\n\n"
    for i, r in enumerate(rows, 1):
        stars = "⭐" * int(r["score"])
        text += f"{i}. <b>{r['title']}</b>\n   {stars} {r['score']}/10\n\n"
    await q.edit_message_text(text, parse_mode="HTML", reply_markup=main_menu_kb())

# ── Callback: wl_ buttons ─────────────────────────────────────────
async def cb_watchlist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    user = update.effective_user
    await q.answer()

    # ── Filter list ────────────────────────────────────────────────
    if data.startswith("wl_filter_"):
        filt = data.replace("wl_filter_", "")
        if filt == "all":
            rows = db.get_watchlist(user.id)
            heading = "📜 All Anime"
        else:
            rows = db.get_watchlist(user.id, filt)
            heading = STATUS_LABELS.get(filt, filt)

        if not rows:
            await q.edit_message_text(
                f"{heading}\n\n😅 Koi anime nahi mila! Pehle add karo.",
                parse_mode="HTML",
                reply_markup=watchlist_filter_kb()
            ); return

        text = f"<b>{heading}</b> — {len(rows)} anime\n\n"
        for r in rows[:20]:
            prog = f"{r['progress']}/{r['total_eps'] or '?'} eps"
            score = f" | ⭐{r['score']}" if r["score"] else ""
            text += f"🎌 <b>{r['title']}</b>\n   📺 {prog}{score}\n   🆔 ID: <code>{r['anime_id']}</code>\n\n"
        if len(rows) > 20:
            text += f"<i>+{len(rows)-20} more...</i>"

        await q.edit_message_text(text, parse_mode="HTML", reply_markup=watchlist_filter_kb())

    # ── Add anime ──────────────────────────────────────────────────
    elif data.startswith("wl_add_"):
        anime_id = int(data.replace("wl_add_", ""))
        # Store pending anime, ask for status
        ctx.user_data["pending_add"] = anime_id
        await q.edit_message_text(
            "➕ <b>Kahan add karein?</b>\nStatus choose karo:",
            parse_mode="HTML",
            reply_markup=add_status_kb(anime_id)
        )

    elif data.startswith("wl_addstatus_"):
        parts    = data.replace("wl_addstatus_", "").split("_")
        anime_id = int(parts[0])
        status   = parts[1]
        anime    = await get_anime_by_id(anime_id)
        if not anime:
            await q.edit_message_text("❌ Anime info nahi mila."); return
        title   = anime["title"].get("english") or anime["title"].get("romaji","?")
        romaji  = anime["title"].get("romaji","")
        cover   = anime.get("coverImage",{}).get("medium","")
        eps     = anime.get("episodes") or 0
        ok = db.add_anime(user.id, anime_id, title, romaji, cover, eps, status)
        label = STATUS_LABELS.get(status,"")
        if ok:
            await q.edit_message_text(
                f"✅ <b>{title}</b>\nadded to <b>{label}</b>!",
                parse_mode="HTML",
                reply_markup=main_menu_kb()
            )
        else:
            await q.edit_message_text(
                f"⚠️ <b>{title}</b> already hai tumhari list mein!",
                parse_mode="HTML",
                reply_markup=main_menu_kb()
            )

    # ── Remove anime ───────────────────────────────────────────────
    elif data.startswith("wl_remove_"):
        anime_id = int(data.replace("wl_remove_", ""))
        entry = db.get_anime_entry(user.id, anime_id)
        title = entry["title"] if entry else "Anime"
        ok = db.remove_anime(user.id, anime_id)
        if ok:
            await q.edit_message_text(
                f"🗑️ <b>{title}</b> removed from watchlist!",
                parse_mode="HTML",
                reply_markup=main_menu_kb()
            )
        else:
            await q.edit_message_text("❌ Remove nahi ho saka.", reply_markup=main_menu_kb())

    # ── Status picker ──────────────────────────────────────────────
    elif data.startswith("wl_status_"):
        anime_id = int(data.replace("wl_status_", ""))
        entry = db.get_anime_entry(user.id, anime_id)
        if not entry:
            await q.edit_message_text("❌ List mein nahi hai.", reply_markup=main_menu_kb()); return
        await q.edit_message_text(
            f"📝 <b>{entry['title']}</b>\nStatus choose karo:",
            parse_mode="HTML",
            reply_markup=status_picker_kb(anime_id)
        )

    # ── Progress update prompt ─────────────────────────────────────
    elif data.startswith("wl_progress_"):
        anime_id = int(data.replace("wl_progress_", ""))
        entry = db.get_anime_entry(user.id, anime_id)
        if not entry:
            await q.edit_message_text("❌ List mein nahi hai."); return
        db.set_state(user.id, f"progress_{anime_id}")
        await q.edit_message_text(
            f"🔢 <b>{entry['title']}</b>\n\nKitne episodes dekhe? Number type karo:\n"
            f"<i>(Current: {entry['progress']}/{entry['total_eps'] or '?'})</i>",
            parse_mode="HTML"
        )

    # ── Rate prompt ────────────────────────────────────────────────
    elif data.startswith("wl_rate_"):
        anime_id = int(data.replace("wl_rate_", ""))
        entry = db.get_anime_entry(user.id, anime_id)
        if not entry:
            await q.edit_message_text("❌ List mein nahi hai."); return
        db.set_state(user.id, f"rate_{anime_id}")
        await q.edit_message_text(
            f"⭐ <b>{entry['title']}</b>\n\n1-10 rating do (e.g. 8.5):",
            parse_mode="HTML"
        )

# ── Callback: status_ buttons ─────────────────────────────────────
async def cb_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data    # format: status_<status>_<anime_id>
    await q.answer()
    user = update.effective_user

    parts    = data.split("_", 2)   # ["status", "watching", "12345"]
    status   = parts[1]
    anime_id = int(parts[2])
    entry    = db.get_anime_entry(user.id, anime_id)
    if not entry:
        await q.edit_message_text("❌ List mein nahi hai."); return
    db.update_status(user.id, anime_id, status)
    label = STATUS_LABELS.get(status,"")
    await q.edit_message_text(
        f"✅ <b>{entry['title']}</b>\nStatus → <b>{label}</b>",
        parse_mode="HTML",
        reply_markup=entry_actions_kb(anime_id)
    )
