# telegram_bot/bot.py
import logging
from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID
from telegram_bot.handlers import (
    cmd_start,
    cmd_analyze,
    cmd_recommend,
    cmd_help,
    handle_callback,
    handle_text,
)

# ─────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
async def post_init(application: Application):
    """Setup sau khi bot khởi động."""
    await application.bot.set_my_commands([
        BotCommand("start",   "Menu chính"),
        BotCommand("analyze", "Phân tích coin"),
        BotCommand("recommend", "Khuyến nghị giao dịch"),
        BotCommand("help",    "Hướng dẫn"),
    ])
    logger.info("✅ Bot commands đã được setup.")

    # Thông báo admin bot đã online
    if TELEGRAM_ADMIN_ID:
        try:
            await application.bot.send_message(
                chat_id=TELEGRAM_ADMIN_ID,
                text="✅ *Binance Analyzer Bot* đã khởi động!",
                parse_mode="Markdown"
            )
        except Exception:
            pass


# ─────────────────────────────────────────
def run_bot():
    """Khởi chạy Telegram Bot."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "❌ Thiếu TELEGRAM_BOT_TOKEN trong .env\n"
            "   Lấy token từ @BotFather trên Telegram"
        )

    logger.info("🚀 Đang khởi động Binance Analyzer Bot...")

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ── Đăng ký handlers ─────────────────
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("recommend", cmd_recommend))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text
    ))

    logger.info("✅ Bot đang chạy. Nhấn Ctrl+C để dừng.")
    app.run_polling(drop_pending_updates=True)