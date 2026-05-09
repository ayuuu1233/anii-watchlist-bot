from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import STATUS_LABELS

# ── Main Menu ──────────────────────────────────────────────────────
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

# ── Watchlist filter ───────────────────────────────────────────────
def watchlist_filter_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👁️ Watching",      callback_data="wl_filter_watching"),
            InlineKeyboardButton("✅ Completed",      callback_data="wl_filter_completed"),
        ],
        [
            InlineKeyboardButton("⏸️ On Hold",        callback_data="wl_filter_on_hold"),
            InlineKeyboardButton("❌ Dropped",        callback_data="wl_filter_dropped"),
        ],
        [
            InlineKeyboardButton("📋 Plan to Watch",  callback_data="wl_filter_plan"),
            InlineKeyboardButton("📜 Show All",       callback_data="wl_filter_all"),
        ],
        [InlineKeyboardButton("🏠 Main Menu",         callback_data="menu_main")],
    ])

# ── Anime action (after search result) ────────────────────────────
def anime_action_kb(anime_id: int, in_list: bool = False):
    if in_list:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Update Status",  callback_data=f"wl_status_{anime_id}"),
                InlineKeyboardButton("🔢 Progress",       callback_data=f"wl_progress_{anime_id}"),
            ],
            [
                InlineKeyboardButton("⭐ Rate",           callback_data=f"wl_rate_{anime_id}"),
                InlineKeyboardButton("🗑️ Remove",         callback_data=f"wl_remove_{anime_id}"),
            ],
            [InlineKeyboardButton("⏰ Set Reminder",      callback_data=f"rem_set_{anime_id}")],
            [InlineKeyboardButton("🔙 Back",              callback_data="menu_search")],
        ])
    else:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add to List",   callback_data=f"wl_add_{anime_id}"),
                InlineKeyboardButton("⏰ Reminder",      callback_data=f"rem_set_{anime_id}"),
            ],
            [InlineKeyboardButton("🔙 Back",             callback_data="menu_search")],
        ])

# ── Status picker ──────────────────────────────────────────────────
def status_picker_kb(anime_id: int):
    buttons = []
    row = []
    for key, label in STATUS_LABELS.items():
        row.append(InlineKeyboardButton(label, callback_data=f"status_{key}_{anime_id}"))
        if len(row) == 2:
            buttons.append(row); row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data=f"srch_info_{anime_id}")])
    return InlineKeyboardMarkup(buttons)

# ── Add with status ────────────────────────────────────────────────
def add_status_kb(anime_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👁️ Watching",     callback_data=f"wl_addstatus_{anime_id}_watching"),
            InlineKeyboardButton("📋 Plan",          callback_data=f"wl_addstatus_{anime_id}_plan"),
        ],
        [
            InlineKeyboardButton("✅ Completed",     callback_data=f"wl_addstatus_{anime_id}_completed"),
            InlineKeyboardButton("❌ Dropped",       callback_data=f"wl_addstatus_{anime_id}_dropped"),
        ],
        [InlineKeyboardButton("🔙 Cancel",           callback_data=f"srch_info_{anime_id}")],
    ])

# ── Search results ─────────────────────────────────────────────────
def search_results_kb(results: list):
    buttons = []
    for anime in results:
        title = (anime["title"].get("english") or anime["title"].get("romaji","?"))[:35]
        eps   = anime.get("episodes") or "?"
        buttons.append([
            InlineKeyboardButton(
                f"🎌 {title} ({eps} eps)",
                callback_data=f"srch_info_{anime['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

# ── Reminder time picker ───────────────────────────────────────────
def reminder_time_kb(anime_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏰ 1 hour",    callback_data=f"rem_time_{anime_id}_1h"),
            InlineKeyboardButton("⏰ 3 hours",   callback_data=f"rem_time_{anime_id}_3h"),
        ],
        [
            InlineKeyboardButton("📅 Tomorrow",  callback_data=f"rem_time_{anime_id}_1d"),
            InlineKeyboardButton("📅 1 Week",    callback_data=f"rem_time_{anime_id}_7d"),
        ],
        [InlineKeyboardButton("🔙 Cancel",       callback_data=f"srch_info_{anime_id}")],
    ])

# ── Watchlist entry actions ────────────────────────────────────────
def entry_actions_kb(anime_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Status",    callback_data=f"wl_status_{anime_id}"),
            InlineKeyboardButton("🔢 Progress",  callback_data=f"wl_progress_{anime_id}"),
        ],
        [
            InlineKeyboardButton("⭐ Rate",      callback_data=f"wl_rate_{anime_id}"),
            InlineKeyboardButton("🗑️ Remove",    callback_data=f"wl_remove_{anime_id}"),
        ],
        [InlineKeyboardButton("🔙 My List",      callback_data="menu_watchlist")],
    ])
