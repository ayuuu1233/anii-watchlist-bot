import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from database.db import init_db
from handlers import start, watchlist, search, reminder, admin
from config import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # ── Commands ──────────────────────────────────────────
    app.add_handler(CommandHandler("start",   start.cmd_start))
    app.add_handler(CommandHandler("help",    start.cmd_help))
    app.add_handler(CommandHandler("add",     watchlist.cmd_add))
    app.add_handler(CommandHandler("remove",  watchlist.cmd_remove))
    app.add_handler(CommandHandler("list",    watchlist.cmd_list))
    app.add_handler(CommandHandler("search",  search.cmd_search))
    app.add_handler(CommandHandler("status",  watchlist.cmd_status))
    app.add_handler(CommandHandler("progress",watchlist.cmd_progress))
    app.add_handler(CommandHandler("remind",  reminder.cmd_remind))
    app.add_handler(CommandHandler("stats",   watchlist.cmd_stats))
    app.add_handler(CommandHandler("top",     watchlist.cmd_top_rated))
    app.add_handler(CommandHandler("admin",   admin.cmd_admin))

    # ── Callback Queries (button clicks) ──────────────────
    app.add_handler(CallbackQueryHandler(start.cb_menu,            pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(watchlist.cb_watchlist,   pattern="^wl_"))
    app.add_handler(CallbackQueryHandler(watchlist.cb_status,      pattern="^status_"))
    app.add_handler(CallbackQueryHandler(search.cb_search,         pattern="^srch_"))
    app.add_handler(CallbackQueryHandler(reminder.cb_reminder,     pattern="^rem_"))
    app.add_handler(CallbackQueryHandler(admin.cb_admin,           pattern="^adm_"))

    # ── Text Messages (search mode) ────────────────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search.handle_text))

    logger.info("🚀 Anime Watchlist Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
