# data/fetcher_ccxt.py
try:
    import ccxt
except ImportError:
    raise ImportError(
        "❌ Thiếu thư viện ccxt.\n"
        "   Cài đặt: pip install ccxt\n"
        "   Hoặc đổi DATA_MODE=public trong .env"
    )

import pandas as pd
import time
from config import (BINANCE_API_KEY, BINANCE_API_SECRET,
                    BINANCE_TESTNET, TIMEFRAMES, REQUEST)


class CCXTFetcher:
    """
    Chế độ CCXT API
    ────────────────
    ✅ Hỗ trợ đầy đủ tính năng
    ✅ Xem số dư tài khoản
    ✅ Đặt/hủy lệnh (nếu cần mở rộng)
    ✅ WebSocket real-time
    ✅ Testnet support
    ❌ Cần API Key & Secret
    ❌ Cần cài thêm ccxt
    """

    MODE = "api"

    def __init__(self):
        self._validate_credentials()

        exchange_config = {
            "apiKey":          BINANCE_API_KEY,
            "secret":          BINANCE_API_SECRET,
            "options":         {"defaultType": "future"},
            "enableRateLimit": True,
        }

        if BINANCE_TESTNET:
            exchange_config["urls"] = {
                "api": {
                    "public":  "https://testnet.binancefuture.com",
                    "private": "https://testnet.binancefuture.com",
                }
            }
            print("  ⚠️  Đang dùng TESTNET Binance")

        self.exchange = ccxt.binanceusdm(exchange_config)
        self._markets = None

    # ─────────────────────────────────────
    def _validate_credentials(self):
        """Kiểm tra API credentials trước khi kết nối."""
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            raise ValueError(
                "❌ Thiếu API Key/Secret.\n"
                "   Điền BINANCE_API_KEY và "
                "BINANCE_API_SECRET vào file .env\n"
                "   Hoặc đổi DATA_MODE=public để "
                "không cần API Key."
            )

        if (BINANCE_API_KEY == "your_api_key_here" or
                BINANCE_API_SECRET == "your_api_secret_here"):
            raise ValueError(
                "❌ Vui lòng thay thế API Key/Secret "
                "thật vào file .env"
            )

    # ─────────────────────────────────────
    def validate_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().strip()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        if not self._markets:
            print("  🔄 Đang tải markets từ CCXT...")
            self._markets = self.exchange.load_markets()

        if symbol not in self._markets:
            raise ValueError(
                f"❌ '{symbol}' không tồn tại."
            )
        return symbol

    # ─────────────────────────────────────
    def get_current_price(self, symbol: str) -> float:
        ticker = self.exchange.fetch_ticker(symbol)
        return float(ticker["last"])

    # ─────────────────────────────────────
    def fetch_ohlcv(self, symbol: str,
                    timeframe: str) -> pd.DataFrame:
        limit = TIMEFRAMES[timeframe]["limit"]
        raw   = self.exchange.fetch_ohlcv(
            symbol, timeframe, limit=limit
        )

        df = pd.DataFrame(raw, columns=[
            "timestamp", "open", "high",
            "low", "close", "volume"
        ])
        df["timestamp"] = pd.to_datetime(
            df["timestamp"], unit="ms"
        )
        df.set_index("timestamp", inplace=True)
        df = df.astype(float)

        # Tính VWAP
        df["date"]          = df.index.date
        df["typical_price"] = (df["high"] + df["low"]
                               + df["close"]) / 3
        df["tp_vol"]        = df["typical_price"] * df["volume"]
        df["cum_tp_vol"]    = df.groupby("date")["tp_vol"].cumsum()
        df["cum_vol"]       = df.groupby("date")["volume"].cumsum()
        df["vwap"]          = df["cum_tp_vol"] / df["cum_vol"]
        df.drop(
            columns=["date", "tp_vol",
                     "cum_tp_vol", "cum_vol"],
            inplace=True
        )
        return df

    # ─────────────────────────────────────
    def fetch_all_timeframes(self, symbol: str) -> dict:
        result = {}
        for tf in TIMEFRAMES:
            print(f"  📥 Tải {tf}...", end=" ", flush=True)
            result[tf] = self.fetch_ohlcv(symbol, tf)
            print(f"✅ {len(result[tf])} nến")
            time.sleep(REQUEST["delay"])
        return result

    # ─────────────────────────────────────
    # Tính năng bổ sung chỉ có trong API mode
    # ─────────────────────────────────────
    def get_account_balance(self) -> dict:
        """Xem số dư tài khoản Futures."""
        balance = self.exchange.fetch_balance()
        usdt    = balance.get("USDT", {})
        return {
            "total": usdt.get("total", 0),
            "free":  usdt.get("free",  0),
            "used":  usdt.get("used",  0),
        }

    def get_open_positions(self) -> list:
        """Xem vị thế đang mở."""
        positions = self.exchange.fetch_positions()
        return [
            p for p in positions
            if float(p.get("contracts", 0)) != 0
        ]