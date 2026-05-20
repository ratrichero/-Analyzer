# data/fetcher_factory.py
from config import DATA_MODE


def create_fetcher():
    """
    Factory tự động chọn Fetcher phù hợp
    dựa trên DATA_MODE trong config/env.

    ┌─────────────────────────────────────────────┐
    │  DATA_MODE = "public" (Mặc định)           │
    │  → PublicFetcher                           │
    │  → Không cần API Key                       │
    │  → Chạy ngay lập tức                       │
    ├─────────────────────────────────────────────┤
    │  DATA_MODE = "api"                          │
    │  → CCXTFetcher                             │
    │  → Cần API Key trong .env                  │
    │  → Thêm tính năng: balance, orders...      │
    └─────────────────────────────────────────────┘
    """
    mode = DATA_MODE.lower().strip()

    if mode == "public":
        from data.fetcher_public import PublicFetcher
        return PublicFetcher()

    elif mode == "api":
        from data.fetcher_ccxt import CCXTFetcher
        return CCXTFetcher()

    else:
        raise ValueError(
            f"❌ DATA_MODE không hợp lệ: '{mode}'\n"
            f"   Chỉ chấp nhận: 'public' hoặc 'api'\n"
            f"   Kiểm tra file .env"
        )


def get_mode_info() -> dict:
    """Trả về thông tin chế độ hiện tại."""
    mode = DATA_MODE.lower().strip()

    info = {
        "public": {
            "name":        "Public API",
            "icon":        "🌐",
            "description": "Binance Public REST API",
            "need_key":    False,
            "features": [
                "✅ Không cần API Key",
                "✅ Phân tích kỹ thuật đầy đủ",
                "✅ Dữ liệu OHLCV real-time",
                "❌ Không xem số dư",
                "❌ Không đặt lệnh",
            ],
        },
        "api": {
            "name":        "CCXT API",
            "icon":        "🔑",
            "description": "CCXT + Binance API Key",
            "need_key":    True,
            "features": [
                "✅ Đầy đủ tính năng Public",
                "✅ Xem số dư tài khoản",
                "✅ Xem vị thế đang mở",
                "✅ Hỗ trợ Testnet",
                "⚠️  Cần API Key & Secret",
            ],
        },
    }

    return info.get(mode, info["public"])