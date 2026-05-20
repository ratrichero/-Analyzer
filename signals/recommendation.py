# signals/recommendation.py
from config import INDICATORS, RISK, SCORE


class RecommendationEngine:
    """
    Tổng hợp 5 nhóm → Khuyến nghị Long/Short/Neutral
    + Tính Entry, TP1, TP2, SL
    """

    # Trọng số từng nhóm
    WEIGHTS = {
        "Xu Hướng (Trend)":        0.30,
        "Động Lượng (Momentum)":   0.25,
        "Biến Động (Volatility)":  0.15,
        "Khối Lượng (Volume)":     0.20,
        "Hỗ Trợ/Kháng Cự (S/R)":  0.10,
    }

    def calculate(self, analyses: dict,
                  price: float,
                  atr: float) -> dict:

        # ── Weighted Score ────────────────────
        total_score = 0
        for tf_data in analyses.values():
            for group_result in tf_data.values():
                group_name = group_result["group"]
                weight     = self.WEIGHTS.get(group_name, 0.2)
                total_score += group_result["score"] * weight

        # Normalize về -100 → +100
        num_tfs = len(analyses)
        final_score = total_score / num_tfs

        # ── Direction ─────────────────────────
        if final_score >= SCORE["strong_threshold"]:
            direction = "LONG"
            strength  = "🟢 MẠNH"
        elif final_score >= 20:
            direction = "LONG"
            strength  = "🟡 YẾU"
        elif final_score <= -SCORE["strong_threshold"]:
            direction = "SHORT"
            strength  = "🔴 MẠNH"
        elif final_score <= -20:
            direction = "SHORT"
            strength  = "🟠 YẾU"
        else:
            direction = "NEUTRAL"
            strength  = "⚪ TRUNG TÍNH"

        # ── SL / TP ───────────────────────────
        sl_distance  = atr * RISK["sl_atr_mult"]
        tp1_distance = sl_distance * RISK["tp1_rr"]
        tp2_distance = sl_distance * RISK["tp2_rr"]

        if direction == "LONG":
            entry = price
            sl    = round(price - sl_distance, 4)
            tp1   = round(price + tp1_distance, 4)
            tp2   = round(price + tp2_distance, 4)
        elif direction == "SHORT":
            entry = price
            sl    = round(price + sl_distance, 4)
            tp1   = round(price - tp1_distance, 4)
            tp2   = round(price - tp2_distance, 4)
        else:
            entry = sl = tp1 = tp2 = price

        # ── Confidence ────────────────────────
        confidence = min(abs(final_score), 100)

        return {
            "direction":   direction,
            "strength":    strength,
            "score":       round(final_score, 1),
            "confidence":  round(confidence, 1),
            "entry":       entry,
            "sl":          sl,
            "tp1":         tp1,
            "tp2":         tp2,
            "sl_pct":      round(sl_distance / price * 100, 3),
            "tp1_pct":     round(tp1_distance / price * 100, 3),
            "atr":         round(atr, 4),
        }