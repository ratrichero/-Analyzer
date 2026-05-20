# analyzers/volume.py
import pandas_ta as ta
import numpy as np
from config import INDICATORS


class VolumeAnalyzer:
    """
    Nhóm 4 — KHỐI LƯỢNG
    Chỉ báo: Volume MA, OBV, Volume Trend
    """

    def analyze(self, df, tf):
        c  = df["close"]
        v  = df["volume"]

        # ── Volume MA ─────────────────────────
        vol_ma  = v.rolling(INDICATORS["volume_ma"]).mean()
        vol_v   = v.iloc[-1]
        vol_ma_v = vol_ma.iloc[-1]
        vol_ratio = vol_v / vol_ma_v

        # ── OBV ───────────────────────────────
        obv     = ta.obv(c, v)
        obv_ma  = obv.rolling(20).mean()
        obv_v   = obv.iloc[-1]
        obv_ma_v = obv_ma.iloc[-1]
        obv_slope = (obv.iloc[-1] - obv.iloc[-5]) / abs(obv.iloc[-5]) * 100

        # ── Volume Trend ──────────────────────
        # So sánh giá tăng/giảm với volume
        price_up   = c.iloc[-1] > c.iloc[-2]
        vol_rising = vol_v > vol_ma_v

        score   = 0
        signals = []

        # Volume vs MA
        if vol_ratio > 1.5:
            score += 25
            signals.append(("✅", f"Volume {vol_ratio:.1f}x MA → Lực mạnh", "Bullish"))
        elif vol_ratio > 1.0:
            score += 10
            signals.append(("✅", f"Volume {vol_ratio:.1f}x MA → Trên TB", "Bullish"))
        else:
            score -= 15
            signals.append(("⚠️", f"Volume {vol_ratio:.1f}x MA → Yếu", "Neutral"))

        # Price + Volume confirmation
        if price_up and vol_rising:
            score += 25
            signals.append(("✅", "Giá tăng + Volume tăng → Xác nhận", "Bullish"))
        elif not price_up and vol_rising:
            score -= 25
            signals.append(("🔴", "Giá giảm + Volume tăng → Bán mạnh", "Bearish"))
        elif price_up and not vol_rising:
            score -= 10
            signals.append(("⚠️", "Giá tăng + Volume yếu → Thiếu xác nhận", "Neutral"))

        # OBV
        if obv_slope > 0:
            score += 20
            signals.append(("✅", f"OBV tăng (+{obv_slope:.1f}%) → Dòng tiền vào", "Bullish"))
        else:
            score -= 20
            signals.append(("🔴", f"OBV giảm ({obv_slope:.1f}%) → Dòng tiền ra", "Bearish"))

        return {
            "group":   "Khối Lượng (Volume)",
            "score":   max(-100, min(100, score)),
            "signals": signals,
            "values": {
                "volume":     round(vol_v, 2),
                "volume_ma":  round(vol_ma_v, 2),
                "vol_ratio":  round(vol_ratio, 2),
                "obv":        round(obv_v, 0),
                "obv_slope":  round(obv_slope, 2),
            },
        }