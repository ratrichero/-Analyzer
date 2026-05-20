# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════
# CHẾ ĐỘ HOẠT ĐỘNG
# ═══════════════════════════════════════════════════════
# Đổi DATA_MODE để chuyển chế độ:
#   "public" → Dùng Binance Public REST API (Mặc định)
#              Không cần API Key, dùng ngay
#   "api"    → Dùng CCXT + API Key cá nhân
#              Cần điền BINANCE_API_KEY và SECRET trong .env
#              Hỗ trợ thêm: WebSocket, Order, Balance...
# ═══════════════════════════════════════════════════════
DATA_MODE = os.getenv("DATA_MODE", "public")   # "public" | "api"

# ═══════════════════════════════════════════════════════
# BINANCE API CREDENTIALS (Chỉ dùng khi DATA_MODE="api")
# ═══════════════════════════════════════════════════════
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY",    "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_TESTNET    = os.getenv("BINANCE_TESTNET", "false").lower() == "true"

# ═══════════════════════════════════════════════════════
# BINANCE PUBLIC API ENDPOINTS
# ═══════════════════════════════════════════════════════
BINANCE_BASE_URL = "https://fapi.binance.com"
ENDPOINTS = {
    "klines":        "/fapi/v1/klines",
    "ticker":        "/fapi/v1/ticker/price",
    "exchange_info": "/fapi/v1/exchangeInfo",
}



# ═══════════════════════════════════════════════════════
# KHUNG THỜI GIAN
# ═══════════════════════════════════════════════════════
TIMEFRAMES = {
    "15m": {"label": "15 Phút", "limit": 200},
    "1h":  {"label": "1 Giờ",   "limit": 200},
    "4h":  {"label": "4 Giờ",   "limit": 200},
    "1d":  {"label": "1 Ngày",  "limit": 200},
}

# ═══════════════════════════════════════════════════════
# THAM SỐ CHỈ BÁO
# ═══════════════════════════════════════════════════════
INDICATORS = {
    # Trend
    "ema_fast":    20,
    "ema_slow":    50,
    "ema_long":   200,
    "adx_period":  14,
    "adx_trend":   25,

    # Momentum
    "rsi_period":   14,
    "rsi_ob":       70,
    "rsi_os":       30,
    "macd_fast":    12,
    "macd_slow":    26,
    "macd_signal":   9,
    "stoch_k":      14,
    "stoch_d":       3,
    "stoch_ob":     80,
    "stoch_os":     20,

    # Volatility
    "atr_period":  14,
    "bb_period":   20,
    "bb_std":       2,

    # Volume
    "volume_ma":   20,

    # S/R
    "swing_period": 20,
    "fib_levels": [0.236, 0.382, 0.5, 0.618, 0.786],
}

# ═══════════════════════════════════════════════════════
# QUẢN LÝ RỦI RO
# ═══════════════════════════════════════════════════════
RISK = {
    "sl_atr_mult": 1.5,
    "tp1_rr":      1.5,
    "tp2_rr":      3.0,
}

# ═══════════════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════════════
SCORE = {
    "strong_threshold": 70,
    "neutral_threshold":   20,
}

# ═══════════════════════════════════════════════════════
# REQUEST SETTINGS
# ═══════════════════════════════════════════════════════
REQUEST = {
    "timeout": 10,
    "retry":    3,
    "delay":  0.3,
}

# ═══════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_ID  = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

# Danh sách coin phổ biến hiển thị trên menu
POPULAR_COINS = [
    "BTCUSDT",  "ETHUSDT",  "BNBUSDT",
    "SOLUSDT",  "ARBUSDT",  "OPUSDT",
    "AVAXUSDT", "MATICUSDT","DOGEUSDT",
    "XRPUSDT",  "ADAUSDT",  "LINKUSDT",
]

# Giới hạn request
RATE_LIMIT = {
    "max_requests_per_user": 5,   # Max request mỗi user
    "cooldown_seconds":      60,  # Cooldown giữa các lần
}