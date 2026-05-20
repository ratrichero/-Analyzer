# analyzers/support_resistance.py
import numpy as np
import pandas as pd
from config import INDICATORS


class SRAnalyzer:
    """
    Nhóm 5 — HỖ TRỢ / KHÁNG CỰ
    Pivot Points, Fibonacci, Swing High/Low
    """

    def analyze(self, df, tf):
        c  = df["close"]
        h  = df["high"]
        l  = df["low"]
        price = c.iloc[-1]

        # ── Pivot Points (Previous candle) ────
        ph = h.iloc[-2]
        pl = l.iloc[-2]
        pc = c.iloc[-2]

        pp = (ph + pl + pc) / 3
        r1 = 2 * pp - pl
        r2 = pp + (ph - pl)
        r3 = ph + 2 * (pp - pl)
        s1 = 2 * pp - ph
        s2 = pp - (ph - pl)
        s3 = pl - 2 * (ph - pp)

        # ── Fibonacci ─────────────────────────
        period = INDICATORS["swing_period"]
        swing_high = h.iloc[-period:].max()
        swing_low  = l.iloc[-period:].min()
        fib_range  = swing_high - swing_low

        fib_levels = {}
        for level in INDICATORS["fib_levels"]:
            fib_levels[level] = swing_high - fib_range * level

        # ── Nearest S/R ───────────────────────
        all_levels = sorted([pp, r1, r2, s1, s2,
                             *fib_levels.values()])
        resistance_levels = [x for x in all_levels if x > price]
        support_levels    = [x for x in all_levels if x < price]

        nearest_resistance = min(resistance_levels) if resistance_levels else None
        nearest_support    = max(support_levels)    if support_levels    else None

        # ── Distance to S/R ───────────────────
        dist_resistance = ((nearest_resistance - price) / price * 100
                          ) if nearest_resistance else None
        dist_support    = ((price - nearest_support) / price * 100
                          ) if nearest_support else None

        score   = 0
        signals = []

        # Giá gần Support
        if dist_support and dist_support < 0.5:
            score += 30
            signals.append(("✅", f"Giá sát Support ({nearest_support:.2f})", "Bullish"))
        elif dist_resistance and dist_resistance < 0.5:
            score -= 30
            signals.append(("🔴", f"Giá sát Resistance ({nearest_resistance:.2f})", "Bearish"))

        # Giá vs Pivot
        if price > pp:
            score += 20
            signals.append(("✅", f"Giá trên Pivot ({pp:.2f})", "Bullish"))
        else:
            score -= 20
            signals.append(("🔴", f"Giá dưới Pivot ({pp:.2f})", "Bearish"))

        # Fibo Zone
        golden_high = fib_levels[0.5]
        golden_low  = fib_levels[0.618]
        if golden_low <= price <= golden_high:
            score += 25
            signals.append(("✅", "Giá trong Golden Zone Fibo (0.5-0.618)", "Bullish"))

        return {
            "group":   "Hỗ Trợ/Kháng Cự (S/R)",
            "score":   max(-100, min(100, score)),
            "signals": signals,
            "values": {
                "pivot":              round(pp, 4),
                "r1": round(r1, 4),  "r2": round(r2, 4),
                "s1": round(s1, 4),  "s2": round(s2, 4),
                "nearest_resistance": round(nearest_resistance, 4) if nearest_resistance else "N/A",
                "nearest_support":    round(nearest_support, 4)    if nearest_support    else "N/A",
                "fib_618":            round(fib_levels[0.618], 4),
                "fib_382":            round(fib_levels[0.382], 4),
            },
        }