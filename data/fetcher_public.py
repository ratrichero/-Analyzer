# data/fetcher_public.py
import requests
import pandas as pd
import time
from config import (BINANCE_BASE_URL, ENDPOINTS,
                    TIMEFRAMES, REQUEST)


class PublicFetcher:
    """
    Chế độ PUBLIC API
    ─────────────────
    ✅ Không cần API Key
    ✅ Dùng ngay, không cần cấu hình
    ✅ Phù hợp: Phân tích, xem tín hiệu
    ❌ Không đặt lệnh được
    ❌ Không xem số dư tài khoản
    """

    MODE = "public"

    def __init__(self):
        self.base_url = BINANCE_BASE_URL
        self.session  = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent":   "BinanceAnalyzer/1.0",
        })
        self._valid_symbols = set()

    # ─────────────────────────────────────
    def _get(self, endpoint: str,
             params: dict = None) -> dict | list:
        """GET request với retry."""
        url = self.base_url + endpoint

        for attempt in range(REQUEST["retry"]):
            try:
                resp = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST["timeout"]
                )
                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.Timeout:
                if attempt == REQUEST["retry"] - 1:
                    raise ConnectionError(
                        "❌ Timeout. Kiểm tra kết nối internet."
                    )
                time.sleep(1)

            except requests.exceptions.HTTPError as e:
                code = resp.status_code
                if code == 400:
                    raise ValueError(f"❌ Bad request: {e}")
                elif code == 429:
                    wait = int(resp.headers.get(
                        "Retry-After", 5
                    ))
                    print(f"⚠️  Rate limit, chờ {wait}s...")
                    time.sleep(wait)
                else:
                    raise ConnectionError(f"❌ HTTP {code}: {e}")

            except requests.exceptions.ConnectionError:
                raise ConnectionError(
                    "❌ Không thể kết nối Binance. "
                    "Kiểm tra internet hoặc thử VPN."
                )

    # ─────────────────────────────────────
    def validate_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().strip()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        if not self._valid_symbols:
            print("  🔄 Đang tải danh sách symbol...")
            info = self._get(ENDPOINTS["exchange_info"])
            self._valid_symbols = {
                s["symbol"]
                for s in info["symbols"]
                if s["status"] == "TRADING"
            }

        if symbol not in self._valid_symbols:
            raise ValueError(
                f"❌ '{symbol}' không tồn tại "
                f"trên Binance Futures."
            )
        return symbol

    # ─────────────────────────────────────
    def get_current_price(self, symbol: str) -> float:
        data = self._get(
            ENDPOINTS["ticker"],
            params={"symbol": symbol}
        )
        return float(data["price"])

    # ─────────────────────────────────────
    def fetch_ohlcv(self, symbol: str,
                    timeframe: str) -> pd.DataFrame:
        limit = TIMEFRAMES[timeframe]["limit"]

        raw = self._get(
            ENDPOINTS["klines"],
            params={
                "symbol":   symbol,
                "interval": timeframe,
                "limit":    limit,
            }
        )

        df = pd.DataFrame(raw, columns=[
            "timestamp", "open", "high", "low",
            "close", "volume", "close_time",
            "quote_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])

        df = df[["timestamp", "open", "high", "low",
                 "close", "volume",
                 "quote_volume", "trades"]].copy()

        df["timestamp"] = pd.to_datetime(
            df["timestamp"], unit="ms"
        )
        df.set_index("timestamp", inplace=True)

        for col in ["open", "high", "low", "close",
                    "volume", "quote_volume", "trades"]:
            df[col] = df[col].astype(float)

        # Tính VWAP reset theo ngày
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