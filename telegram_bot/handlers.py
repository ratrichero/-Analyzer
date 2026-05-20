# telegram_bot/handlers.py
import asyncio
import time

# ── Thêm đầy đủ import ở đây ──────────────
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from data.fetcher_factory         import create_fetcher
from analyzers.trend              import TrendAnalyzer
from analyzers.momentum           import MomentumAnalyzer
from analyzers.volatility         import VolatilityAnalyzer
from analyzers.volume             import VolumeAnalyzer
from analyzers.support_resistance import SRAnalyzer
from signals.recommendation       import RecommendationEngine
from telegram_bot.keyboards       import (
    main_menu_keyboard,
    popular_coins_keyboard,
    recommendation_coins_keyboard,
    timeframe_keyboard,
    back_to_menu_keyboard,
    back_from_rec_keyboard,
)
from telegram_bot.formatter       import TelegramFormatter
from config                       import TIMEFRAMES, RATE_LIMIT

# ─────────────────────────────────────────
# Rate Limiter
# ─────────────────────────────────────────
_user_requests: dict = {}


def _check_rate_limit(
        user_id: int) -> tuple[bool, int]:
    now      = time.time()
    cooldown = RATE_LIMIT["cooldown_seconds"]
    max_req  = RATE_LIMIT["max_requests_per_user"]

    if user_id not in _user_requests:
        _user_requests[user_id] = []

    _user_requests[user_id] = [
        t for t in _user_requests[user_id]
        if now - t < cooldown
    ]

    if len(_user_requests[user_id]) >= max_req:
        oldest   = _user_requests[user_id][0]
        wait_sec = int(cooldown - (now - oldest)) + 1
        return False, wait_sec

    _user_requests[user_id].append(now)
    return True, 0


# ─────────────────────────────────────────
# Core Analysis
# ─────────────────────────────────────────
async def run_analysis_async(symbol: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _run_analysis_sync, symbol
    )


def _run_analysis_sync(symbol: str) -> dict:
    fetcher  = create_fetcher()
    symbol   = fetcher.validate_symbol(symbol)
    price    = fetcher.get_current_price(symbol)
    data     = fetcher.fetch_all_timeframes(symbol)

    analyzers = {
        "trend":      TrendAnalyzer(),
        "momentum":   MomentumAnalyzer(),
        "volatility": VolatilityAnalyzer(),
        "volume":     VolumeAnalyzer(),
        "sr":         SRAnalyzer(),
    }

    all_analyses = {}
    for tf in TIMEFRAMES:
        df        = data[tf]
        tf_result = {}
        for name, analyzer in analyzers.items():
            tf_result[name] = analyzer.analyze(df, tf)
        all_analyses[tf] = tf_result

    atr_1h = (
        all_analyses["1h"]["volatility"]["values"]["atr"]
    )
    engine = RecommendationEngine()
    rec    = engine.calculate(all_analyses, price, atr_1h)

    return {
        "symbol":       symbol,
        "price":        price,
        "all_analyses": all_analyses,
        "rec":          rec,
    }


# ─────────────────────────────────────────
# Helper — Coin Action Keyboard
# ─────────────────────────────────────────
def _coin_action_keyboard(
        symbol: str) -> InlineKeyboardMarkup:
    """Chọn hành động với coin vừa nhập."""
    name     = symbol.replace("USDT", "")
    keyboard = [
        [
            InlineKeyboardButton(
                f"📊 Phân tích {name}",
                callback_data=f"full_{symbol}"
            ),
        ],
        [
            InlineKeyboardButton(
                f"🎯 Khuyến nghị {name}",
                callback_data=f"rec_{symbol}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Menu chính",
                callback_data="menu_main"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ═════════════════════════════════════════
# COMMAND HANDLERS
# ═════════════════════════════════════════

async def cmd_start(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 Xin chào *{user.first_name}*\\!\n\n"
        f"🤖 *Binance Futures Analyzer Bot*\n\n"
        f"Chọn chức năng bên dưới 👇"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=main_menu_keyboard()
    )


async def cmd_analyze(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📊 *Phân tích Coin*\n"
            "Cú pháp: `/analyze BTC`\n\n"
            "Hoặc chọn coin bên dưới:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=popular_coins_keyboard(
                mode="analyze"
            )
        )
        return
    symbol = context.args[0].upper()
    await _process_full_analysis(
        update, context, symbol
    )


async def cmd_recommend(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🎯 *Khuyến nghị Giao dịch*\n"
            "Cú pháp: `/recommend BTC`\n\n"
            "Hoặc chọn coin bên dưới:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=recommendation_coins_keyboard()
        )
        return
    symbol = context.args[0].upper()
    await _process_recommendation(
        update, context, symbol
    )


async def cmd_help(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *HƯỚNG DẪN SỬ DỤNG*\n\n"
        "*Lệnh:*\n"
        "`/start`         — Menu chính\n"
        "`/analyze BTC`   — Phân tích kỹ thuật\n"
        "`/recommend BTC` — Khuyến nghị giao dịch\n"
        "`/help`          — Hướng dẫn\n\n"
        "*Đọc kết quả:*\n"
        "🟢 Score > +70 → LONG mạnh\n"
        "🟡 Score +20→+70 → LONG yếu\n"
        "⚪ Score ±20 → Trung tính\n"
        "🟠 Score -20→-70 → SHORT yếu\n"
        "🔴 Score < -70 → SHORT mạnh\n\n"
        "⚠️ _Chỉ mang tính tham khảo kỹ thuật_"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard()
    )


# ═════════════════════════════════════════
# CALLBACK HANDLER CHÍNH
# ═════════════════════════════════════════

async def handle_callback(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data

    # ── Menu Navigation ───────────────────
    if data == "menu_main":
        await query.edit_message_text(
            "🏠 *Menu Chính*\nChọn chức năng:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_keyboard()
        )

    elif data == "menu_analyze":
        await query.edit_message_text(
            "📊 *Phân tích Coin*\n\n"
            "Phân tích kỹ thuật đầy đủ theo\n"
            "*5 nhóm chỉ báo × 4 khung TF*\n\n"
            "Chọn coin:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=popular_coins_keyboard(
                mode="analyze"
            )
        )

    elif data == "menu_recommendation":
        await query.edit_message_text(
            "🎯 *Khuyến nghị Giao dịch*\n\n"
            "Phân tích và đưa ra khuyến nghị:\n"
            "• Hướng: LONG / SHORT / NEUTRAL\n"
            "• Entry, SL, TP1, TP2\n"
            "• Lý do & Điều kiện vô hiệu hóa\n"
            "• Checklist trước khi vào lệnh\n\n"
            "Chọn coin:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=recommendation_coins_keyboard()
        )

    elif data == "menu_popular":
        await query.edit_message_text(
            "⭐ *Coin phổ biến*\nChọn để phân tích:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=popular_coins_keyboard(
                mode="analyze"
            )
        )

    elif data == "menu_help":
        await query.edit_message_text(
            "📖 *Hướng dẫn*\n\n"
            "📊 *Phân tích Coin*\n"
            "→ Chi tiết 5 nhóm × 4 khung TF\n\n"
            "🎯 *Khuyến nghị*\n"
            "→ Long/Short + Entry/SL/TP\n"
            "→ Lý do + Checklist vào lệnh\n\n"
            "🟢 Score > 70 → LONG mạnh\n"
            "🟡 Score > 20 → LONG yếu\n"
            "⚪ Score ±20  → Trung tính\n"
            "🟠 Score < -20 → SHORT yếu\n"
            "🔴 Score < -70 → SHORT mạnh",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_keyboard()
        )

    # ── Phân tích Coin ────────────────────
    elif data.startswith("analyze_"):
        symbol = data.replace("analyze_", "")
        if symbol == "custom":
            await query.edit_message_text(
                "✏️ *Nhập tên coin*\n\n"
                "Gửi lệnh: `/analyze <symbol>`\n\n"
                "Ví dụ: `/analyze BTC`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_to_menu_keyboard()
            )
        else:
            name = symbol.replace("USDT", "")
            await query.edit_message_text(
                f"📊 *{name}* — Chọn loại phân tích:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=timeframe_keyboard(symbol)
            )

    # ── Khuyến nghị Coin ─────────────────
    elif data.startswith("rec_"):
        symbol = data.replace("rec_", "")
        if symbol == "custom":
            await query.edit_message_text(
                "✏️ *Nhập tên coin*\n\n"
                "Gửi lệnh: `/recommend <symbol>`\n\n"
                "Ví dụ: `/recommend BTC`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_from_rec_keyboard()
            )
        else:
            await _process_recommendation_callback(
                query, context, symbol
            )

    # ── Phân tích đầy đủ ─────────────────
    elif data.startswith("full_"):
        symbol = data.replace("full_", "")
        await _process_full_analysis_callback(
            query, context, symbol
        )

    # ── Phân tích 1 TF ───────────────────
    elif data.startswith("tf_"):
        parts  = data.split("_", 2)
        tf     = parts[1]
        symbol = parts[2]
        await _process_single_tf_callback(
            query, context, symbol, tf
        )


# ═════════════════════════════════════════
# PROCESSING FUNCTIONS
# ═════════════════════════════════════════

async def _process_full_analysis(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        symbol: str):
    user_id       = update.effective_user.id
    allowed, wait = _check_rate_limit(user_id)

    if not allowed:
        await update.message.reply_text(
            f"⏳ Vui lòng chờ *{wait}* giây.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    msg = await update.message.reply_text(
        f"⏳ Đang phân tích *{symbol}*\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    try:
        result    = await run_analysis_async(symbol)
        formatter = TelegramFormatter()
        text      = formatter.format_full_report(
            result["symbol"],
            result["price"],
            result["all_analyses"],
            result["rec"]
        )
        await msg.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard()
        )
    except ValueError as e:
        await msg.edit_text(
            f"❌ *Lỗi*: {e}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        await msg.edit_text(
            f"❌ *Lỗi*: `{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard()
        )


async def _process_full_analysis_callback(
        query,
        context: ContextTypes.DEFAULT_TYPE,
        symbol: str):
    user_id       = query.from_user.id
    allowed, wait = _check_rate_limit(user_id)

    if not allowed:
        await query.edit_message_text(
            f"⏳ Vui lòng chờ *{wait}* giây.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    name = symbol.replace("USDT", "")
    await query.edit_message_text(
        f"⏳ Đang phân tích *{name}*\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    try:
        result    = await run_analysis_async(symbol)
        formatter = TelegramFormatter()
        text      = formatter.format_full_report(
            result["symbol"],
            result["price"],
            result["all_analyses"],
            result["rec"]
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        await query.edit_message_text(
            f"❌ *Lỗi*: `{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard()
        )


async def _process_recommendation(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        symbol: str):
    user_id       = update.effective_user.id
    allowed, wait = _check_rate_limit(user_id)

    if not allowed:
        await update.message.reply_text(
            f"⏳ Vui lòng chờ *{wait}* giây.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    msg = await update.message.reply_text(
        f"🎯 Đang tạo khuyến nghị "
        f"*{symbol}*\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    try:
        result    = await run_analysis_async(symbol)
        formatter = TelegramFormatter()
        text      = formatter.format_recommendation_only(
            result["symbol"],
            result["price"],
            result["rec"]
        )
        await msg.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_from_rec_keyboard()
        )
    except ValueError as e:
        await msg.edit_text(
            f"❌ *Lỗi*: {e}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_from_rec_keyboard()
        )
    except Exception as e:
        await msg.edit_text(
            f"❌ *Lỗi*: `{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_from_rec_keyboard()
        )


async def _process_recommendation_callback(
        query,
        context: ContextTypes.DEFAULT_TYPE,
        symbol: str):
    user_id       = query.from_user.id
    allowed, wait = _check_rate_limit(user_id)

    if not allowed:
        await query.edit_message_text(
            f"⏳ Vui lòng chờ *{wait}* giây.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    name = symbol.replace("USDT", "")
    await query.edit_message_text(
        f"🎯 Đang tạo khuyến nghị "
        f"*{name}*\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    try:
        result    = await run_analysis_async(symbol)
        formatter = TelegramFormatter()
        text      = formatter.format_recommendation_only(
            result["symbol"],
            result["price"],
            result["rec"]
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_from_rec_keyboard()
        )
    except Exception as e:
        await query.edit_message_text(
            f"❌ *Lỗi*: `{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_from_rec_keyboard()
        )


async def _process_single_tf_callback(
        query,
        context: ContextTypes.DEFAULT_TYPE,
        symbol: str,
        tf: str):
    user_id       = query.from_user.id
    allowed, wait = _check_rate_limit(user_id)

    if not allowed:
        await query.edit_message_text(
            f"⏳ Vui lòng chờ *{wait}* giây.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    tf_labels = {
        "15m": "15 Phút", "1h": "1 Giờ",
        "4h":  "4 Giờ",   "1d": "1 Ngày",
    }
    name = symbol.replace("USDT", "")
    await query.edit_message_text(
        f"⏳ Phân tích *{name}* "
        f"khung *{tf_labels.get(tf, tf)}*\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    try:
        result    = await run_analysis_async(symbol)
        formatter = TelegramFormatter()

        if tf in result["all_analyses"]:
            text = formatter.format_single_tf(
                result["symbol"],
                result["price"],
                tf,
                result["all_analyses"][tf]
            )
        else:
            text = "❌ Khung thời gian không hợp lệ."

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard()
        )
    except Exception as e:
        await query.edit_message_text(
            f"❌ *Lỗi*: `{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard()
        )


# ─────────────────────────────────────────
async def handle_text(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Xử lý text thường — tự detect coin."""
    text   = update.message.text.strip().upper()
    symbol = text.replace("USDT", "") + "USDT"

    if text.isalpha() and len(text) <= 10:
        await update.message.reply_text(
            f"📊 Bạn muốn làm gì với "
            f"*{text}*?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_coin_action_keyboard(symbol)
        )
    else:
        await update.message.reply_text(
            "🏠 Chọn chức năng:",
            reply_markup=main_menu_keyboard()
        )