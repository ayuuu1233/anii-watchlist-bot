# ═══════════════════════════════════════════════
#   config.py  –  Bot Configuration
# ═══════════════════════════════════════════════

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # 👈 @BotFather se lo

DB_PATH   = "watchlist.db"

ADMIN_IDS = [123456789]             # 👈 Apna Telegram user ID dalo

# AniList GraphQL API (free, no key needed)
ANILIST_URL = "https://graphql.anilist.co"

# Status labels shown in UI
STATUS_LABELS = {
    "watching":   "👁️ Watching",
    "completed":  "✅ Completed",
    "on_hold":    "⏸️ On Hold",
    "dropped":    "❌ Dropped",
    "plan":       "📋 Plan to Watch",
}

# Max watchlist per user
MAX_WATCHLIST = 200
