# analyzers/volatility.py
import pandas_ta as ta
import pandas as pd
import numpy as np
from config import INDICATORS


class VolatilityAnalyzer:
    """
    Nhóm 3 — BIẾN ĐỘNG
    Chỉ báo: ATR, Bollinger Bands
    """

    def _get_bb_columns(self, bb: pd.DataFrame) -> tuple:
        """
        Tự động tìm tên cột BB đúng
        Xử lý cả 2 trường hợp:
        - BBU_20_2.0  (pandas_ta cũ)
        - BBU_20_2    (pandas_ta mới)
        """
        cols = bb.columns.tolist()

        # Tìm cột Upper
        bb_upper_col = next(
            (c for c in cols if c.startswith("BBU_")), None
        )
        # Tìm cột Middle
        bb_mid_col = next(
            (c for c in cols if c.startswith("BBM_")), None
        )
        # Tìm cột Lower
        bb_lower_col = next(
            (c for c in cols if c.startswith("BBL_")), None
        )

        if not all([bb_upper_col, bb_mid_col, bb_lower_col]):
            raise KeyError(
                f"❌ Không tìm thấy cột Bollinger Bands.\n"
                f"   Các cột hiện có: {cols}"
            )

        return bb_upper_col, bb_mid_col, bb_lower_col

    # ─────────────────────────────────────
    def analyze(self, df: pd.DataFrame, tf: str) -> dict:
        c = df["close"]
        h = df["high"]
        l = df["low"]

        # ── ATR ───────────────────────────────
        atr     = ta.atr(h, l, c,
                         length=INDICATORS["atr_period"])
        atr_v   = atr.iloc[-1]
        atr_ma  = atr.rolling(50).mean().iloc[-1]
        atr_pct = (atr_v / c.iloc[-1]) * 100

        # ── Bollinger Bands ───────────────────
        bb = ta.bbands(
            c,
            length=INDICATORS["bb_period"],
            std=INDICATORS["bb_std"]
        )

        # Debug: In tên cột nếu cần
        # print(f"BB columns: {bb.columns.tolist()}")

        # Tự động detect tên cột
        bb_upper_col, bb_mid_col, bb_lower_col = \
            self._get_bb_columns(bb)

        bb_upper = bb[bb_upper_col].iloc[-1]
        bb_mid   = bb[bb_mid_col].iloc[-1]
        bb_lower = bb[bb_lower_col].iloc[-1]

        price    = c.iloc[-1]
        bb_range = bb_upper - bb_lower

        # Tránh chia cho 0
        bb_width = (bb_range / bb_mid * 100
                    ) if bb_mid != 0 else 0
        bb_pct   = ((price - bb_lower) / bb_range * 100
                    ) if bb_range != 0 else 50

        # BB Width MA (để detect Squeeze)
        bb_width_series = (
            (bb[bb_upper_col] - bb[bb_lower_col])
            / bb[bb_mid_col] * 100
        )
        bb_width_ma = bb_width_series.rolling(20).mean().iloc[-1]

        # ── Scoring ───────────────────────────
        score   = 0
        signals = []

        # ATR vs MA
        if not np.isnan(atr_ma) and atr_v > atr_ma:
            score += 10
            signals.append((
                "✅",
                f"ATR={atr_v:.4f} > MA → Biến động tốt",
                "Bullish"
            ))
        else:
            score -= 10
            signals.append((
                "⚠️",
                f"ATR={atr_v:.4f} < MA → Thị trường lịm",
                "Neutral"
            ))

        # Bollinger %B
        if bb_pct > 80:
            score -= 20
            signals.append((
                "🔴",
                f"BB%={bb_pct:.0f}% → Giá sát dải trên",
                "Bearish"
            ))
        elif bb_pct < 20:
            score += 20
            signals.append((
                "✅",
                f"BB%={bb_pct:.0f}% → Giá sát dải dưới",
                "Bullish"
            ))
        else:
            signals.append((
                "⚠️",
                f"BB%={bb_pct:.0f}% → Giá giữa dải",
                "Neutral"
            ))

        # BB Squeeze
        if (not np.isnan(bb_width_ma)
                and bb_width < bb_width_ma * 0.8):
            signals.append((
                "⚠️",
                "BB Squeeze → Sắp có Breakout mạnh",
                "Neutral"
            ))

        return {
            "group":   "Biến Động (Volatility)",
            "score":   max(-100, min(100, score)),
            "signals": signals,
            "values": {
                "atr":       round(atr_v,   4),
                "atr_pct":   round(atr_pct, 3),
                "bb_upper":  round(bb_upper, 4),
                "bb_mid":    round(bb_mid,   4),
                "bb_lower":  round(bb_lower, 4),
                "bb_pct":    round(bb_pct,   1),
                "bb_width":  round(bb_width, 2),
            },
        }