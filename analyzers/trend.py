# analyzers/trend.py
import pandas as pd
import pandas_ta as ta
from config import INDICATORS


class TrendAnalyzer:
    """
    Nhóm 1 — XU HƯỚNG
    Chỉ báo: EMA 20/50/200, VWAP, ADX
    """

    def _get_adx_columns(self,
                          adx_df: pd.DataFrame) -> tuple:
        cols    = adx_df.columns.tolist()
        adx_col = next((c for c in cols
                        if c.startswith("ADX_")), None)
        dmp_col = next((c for c in cols
                        if c.startswith("DMP_")), None)
        dmn_col = next((c for c in cols
                        if c.startswith("DMN_")), None)

        if not all([adx_col, dmp_col, dmn_col]):
            raise KeyError(
                f"❌ Không tìm thấy cột ADX: {cols}"
            )
        return adx_col, dmp_col, dmn_col

    # ─────────────────────────────────────
    def analyze(self, df: pd.DataFrame, tf: str) -> dict:
        c = df["close"]
        h = df["high"]
        l = df["low"]

        # ── EMA ───────────────────────────────
        ema20  = ta.ema(c, length=INDICATORS["ema_fast"])
        ema50  = ta.ema(c, length=INDICATORS["ema_slow"])
        ema200 = ta.ema(c, length=INDICATORS["ema_long"])

        price = c.iloc[-1]
        e20   = ema20.iloc[-1]
        e50   = ema50.iloc[-1]
        e200  = ema200.iloc[-1]
        vwap  = df["vwap"].iloc[-1]

        # ── ADX ───────────────────────────────
        adx_df          = ta.adx(
            h, l, c,
            length=INDICATORS["adx_period"]
        )
        adx_col, dmp_col, dmn_col = \
            self._get_adx_columns(adx_df)

        adx_v = adx_df[adx_col].iloc[-1]
        dmp   = adx_df[dmp_col].iloc[-1]
        dmn   = adx_df[dmn_col].iloc[-1]

        # ── EMA Slope ─────────────────────────
        ema50_slope = (
            (ema50.iloc[-1] - ema50.iloc[-5])
            / ema50.iloc[-5] * 100
        )

        # ── Scoring ───────────────────────────
        score   = 0
        signals = []

        # Price vs EMA 20
        if price > e20:
            score += 15
            signals.append(("✅", "Giá > EMA20", "Bullish"))
        else:
            score -= 15
            signals.append(("🔴", "Giá < EMA20", "Bearish"))

        # Price vs EMA 50
        if price > e50:
            score += 20
            signals.append(("✅", "Giá > EMA50", "Bullish"))
        else:
            score -= 20
            signals.append(("🔴", "Giá < EMA50", "Bearish"))

        # Price vs EMA 200
        if price > e200:
            score += 20
            signals.append(("✅", "Giá > EMA200", "Bullish"))
        else:
            score -= 20
            signals.append(("🔴", "Giá < EMA200", "Bearish"))

        # VWAP
        if price > vwap:
            score += 20
            signals.append(("✅", "Giá > VWAP", "Bullish"))
        else:
            score -= 20
            signals.append(("🔴", "Giá < VWAP", "Bearish"))

        # ADX
        if adx_v > INDICATORS["adx_trend"]:
            if dmp > dmn:
                score += 15
                signals.append((
                    "✅",
                    f"ADX={adx_v:.1f} Trend tăng mạnh",
                    "Bullish"
                ))
            else:
                score -= 15
                signals.append((
                    "🔴",
                    f"ADX={adx_v:.1f} Trend giảm mạnh",
                    "Bearish"
                ))
        else:
            signals.append((
                "⚠️",
                f"ADX={adx_v:.1f} Sideway/Yếu",
                "Neutral"
            ))

        # EMA Slope
        if ema50_slope > 0.1:
            score += 10
            signals.append((
                "✅",
                f"EMA50 dốc lên ({ema50_slope:.2f}%)",
                "Bullish"
            ))
        elif ema50_slope < -0.1:
            score -= 10
            signals.append((
                "🔴",
                f"EMA50 dốc xuống ({ema50_slope:.2f}%)",
                "Bearish"
            ))

        return {
            "group":   "Xu Hướng (Trend)",
            "score":   max(-100, min(100, score)),
            "signals": signals,
            "values": {
                "price":  round(price, 4),
                "ema20":  round(e20,   4),
                "ema50":  round(e50,   4),
                "ema200": round(e200,  4),
                "vwap":   round(vwap,  4),
                "adx":    round(adx_v, 2),
            },
        }