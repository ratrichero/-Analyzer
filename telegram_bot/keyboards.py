# telegram_bot/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import POPULAR_COINS


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu chính — 4 tính năng ngang cấp."""
    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Phân tích Coin",
                callback_data="menu_analyze"
            ),
            InlineKeyboardButton(
                "🎯 Khuyến nghị",
                callback_data="menu_recommendation"
            ),
        ],
        [
            InlineKeyboardButton(
                "⭐ Coin phổ biến",
                callback_data="menu_popular"
            ),
            InlineKeyboardButton(
                "❓ Hướng dẫn",
                callback_data="menu_help"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
def popular_coins_keyboard(
        mode: str = "analyze"
) -> InlineKeyboardMarkup:
    """
    Grid coin phổ biến.
    mode: "analyze" | "recommend"
    → Quyết định callback khi chọn coin
    """
    keyboard = []
    row      = []

    for i, coin in enumerate(POPULAR_COINS):
        label    = coin.replace("USDT", "")
        callback = (f"rec_{coin}"
                    if mode == "recommend"
                    else f"analyze_{coin}")

        row.append(
            InlineKeyboardButton(
                label,
                callback_data=callback
            )
        )
        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Nút nhập thủ công
    custom_cb = ("rec_custom"
                 if mode == "recommend"
                 else "analyze_custom")
    keyboard.append([
        InlineKeyboardButton(
            "✏️ Nhập coin khác",
            callback_data=custom_cb
        )
    ])

    # Back
    back_cb = ("menu_recommendation"
               if mode == "recommend"
               else "menu_analyze")
    keyboard.append([
        InlineKeyboardButton(
            "🔙 Quay lại",
            callback_data=back_cb
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
def recommendation_coins_keyboard() -> InlineKeyboardMarkup:
    """Grid coin cho tính năng Khuyến nghị."""
    return popular_coins_keyboard(mode="recommend")


# ─────────────────────────────────────────
def timeframe_keyboard(
        symbol: str
) -> InlineKeyboardMarkup:
    """Chọn khung TF cho Phân tích."""
    keyboard = [
        [
            InlineKeyboardButton(
                "⚡ Phân tích đầy đủ (15m→1D)",
                callback_data=f"full_{symbol}"
            ),
        ],
        [
            InlineKeyboardButton(
                "15m", callback_data=f"tf_15m_{symbol}"
            ),
            InlineKeyboardButton(
                "1H", callback_data=f"tf_1h_{symbol}"
            ),
            InlineKeyboardButton(
                "4H", callback_data=f"tf_4h_{symbol}"
            ),
            InlineKeyboardButton(
                "1D", callback_data=f"tf_1d_{symbol}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 Quay lại",
                callback_data="menu_popular"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Nút sau khi xem kết quả."""
    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Phân tích lại",
                callback_data="menu_popular"
            ),
            InlineKeyboardButton(
                "🎯 Khuyến nghị mới",
                callback_data="menu_recommendation"
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


# ─────────────────────────────────────────
def back_from_rec_keyboard() -> InlineKeyboardMarkup:
    """Nút sau khi xem Khuyến nghị."""
    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Khuyến nghị coin khác",
                callback_data="menu_recommendation"
            ),
        ],
        [
            InlineKeyboardButton(
                "📊 Phân tích chi tiết",
                callback_data="menu_analyze"
            ),
            InlineKeyboardButton(
                "🏠 Menu chính",
                callback_data="menu_main"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)