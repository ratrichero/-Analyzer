# signals/recommendation.py
from config import RISK, SCORE


class RecommendationEngine:
    """
    Tổng hợp 5 nhóm × 4 khung → Khuyến nghị
    chi tiết có lý do, rủi ro, checklist
    """

    WEIGHTS = {
        "Xu Hướng (Trend)":        0.30,
        "Động Lượng (Momentum)":   0.25,
        "Biến Động (Volatility)":  0.15,
        "Khối Lượng (Volume)":     0.20,
        "Hỗ Trợ/Kháng Cự (S/R)":  0.10,
    }

    # Trọng số từng khung thời gian
    TF_WEIGHTS = {
        "15m": 0.15,
        "1h":  0.30,
        "4h":  0.35,
        "1d":  0.20,
    }

    # ─────────────────────────────────────
    def calculate(self,
                  analyses: dict,
                  price: float,
                  atr: float) -> dict:

        # ── 1. Score theo từng TF ─────────
        tf_scores    = self._calc_tf_scores(analyses)

        # ── 2. Score tổng hợp có trọng số ─
        final_score  = self._calc_final_score(tf_scores)

        # ── 3. MTF Alignment ──────────────
        mtf_alignment = self._calc_mtf_alignment(tf_scores)

        # ── 4. Score từng nhóm (dùng 1H) ──
        group_scores = self._calc_group_scores(analyses)

        # ── 5. Hướng & Sức mạnh ───────────
        direction, strength, signal_level = \
            self._determine_direction(
                final_score, mtf_alignment
            )

        # ── 6. SL / TP ────────────────────
        levels = self._calc_levels(
            price, atr, direction
        )

        # ── 7. Rủi ro ─────────────────────
        risk_info = self._calc_risk(
            price, atr, direction, mtf_alignment
        )

        # ── 8. Lý do khuyến nghị ──────────
        reasons = self._build_reasons(
            direction, group_scores,
            tf_scores, mtf_alignment
        )

        # ── 9. Điều kiện vô hiệu hóa ──────
        invalidation = self._build_invalidation(
            direction, price, levels, analyses
        )

        # ── 10. Checklist ─────────────────
        checklist = self._build_checklist(
            direction, mtf_alignment,
            group_scores, risk_info
        )

        return {
            # Core
            "direction":    direction,
            "strength":     strength,
            "signal_level": signal_level,
            "score":        round(final_score, 1),
            "confidence":   round(
                min(abs(final_score), 100), 1
            ),

            # Levels
            **levels,

            # MTF
            "tf_scores":     tf_scores,
            "mtf_alignment": mtf_alignment,
            "group_scores":  group_scores,

            # Chi tiết
            "risk_info":     risk_info,
            "reasons":       reasons,
            "invalidation":  invalidation,
            "checklist":     checklist,

            # ATR
            "atr": round(atr, 4),
        }

    # ═════════════════════════════════════
    # PRIVATE METHODS
    # ═════════════════════════════════════

    def _calc_tf_scores(self,
                         analyses: dict) -> dict:
        """Tính score trung bình từng khung TF."""
        tf_scores = {}
        for tf, tf_data in analyses.items():
            scores = []
            for group_result in tf_data.values():
                group   = group_result["group"]
                weight  = self.WEIGHTS.get(group, 0.2)
                scores.append(
                    group_result["score"] * weight
                )
            tf_scores[tf] = round(sum(scores), 1)
        return tf_scores

    # ─────────────────────────────────────
    def _calc_final_score(self,
                           tf_scores: dict) -> float:
        """Tính score tổng có trọng số TF."""
        total  = 0
        weight = 0
        for tf, score in tf_scores.items():
            w      = self.TF_WEIGHTS.get(tf, 0.25)
            total  += score * w
            weight += w
        return total / weight if weight > 0 else 0

    # ─────────────────────────────────────
    def _calc_mtf_alignment(self,
                             tf_scores: dict) -> dict:
        """
        Đo mức độ đồng thuận giữa các khung TF.
        """
        bullish = sum(
            1 for s in tf_scores.values() if s > 10
        )
        bearish = sum(
            1 for s in tf_scores.values() if s < -10
        )
        neutral = len(tf_scores) - bullish - bearish
        total   = len(tf_scores)

        # Tỷ lệ đồng thuận
        if bullish >= 3:
            consensus     = "BULLISH"
            consensus_pct = bullish / total * 100
        elif bearish >= 3:
            consensus     = "BEARISH"
            consensus_pct = bearish / total * 100
        elif bullish > bearish:
            consensus     = "BULLISH_WEAK"
            consensus_pct = bullish / total * 100
        elif bearish > bullish:
            consensus     = "BEARISH_WEAK"
            consensus_pct = bearish / total * 100
        else:
            consensus     = "MIXED"
            consensus_pct = 50.0

        return {
            "bullish":       bullish,
            "bearish":       bearish,
            "neutral":       neutral,
            "total":         total,
            "consensus":     consensus,
            "consensus_pct": round(consensus_pct, 1),
        }

    # ─────────────────────────────────────
    def _calc_group_scores(self,
                            analyses: dict) -> dict:
        """
        Tính score trung bình từng nhóm
        trên tất cả khung TF.
        """
        group_totals  = {}
        group_counts  = {}

        for tf_data in analyses.values():
            for group_result in tf_data.values():
                name  = group_result["group"]
                score = group_result["score"]
                group_totals[name] = (
                    group_totals.get(name, 0) + score
                )
                group_counts[name] = (
                    group_counts.get(name, 0) + 1
                )

        return {
            name: round(
                group_totals[name] / group_counts[name],
                1
            )
            for name in group_totals
        }

    # ─────────────────────────────────────
    def _determine_direction(
            self,
            final_score: float,
            mtf: dict) -> tuple:
        """
        Xác định hướng, sức mạnh, cấp tín hiệu.
        Kết hợp score + MTF consensus.
        """
        strong = SCORE.get(
            "strong_threshold",
            SCORE.get("strong", 70)
        )
        weak = SCORE.get(
            "neutral_threshold",
            SCORE.get("weak", 20)
        )

        consensus = mtf["consensus"]

        # LONG signals
        if (final_score >= strong
                and consensus in ["BULLISH"]):
            return "LONG", "🟢 LONG MẠNH", "A"

        elif (final_score >= weak
              and consensus in ["BULLISH",
                                "BULLISH_WEAK"]):
            return "LONG", "🟡 LONG YẾU", "B"

        # SHORT signals
        elif (final_score <= -strong
              and consensus in ["BEARISH"]):
            return "SHORT", "🔴 SHORT MẠNH", "A"

        elif (final_score <= -weak
              and consensus in ["BEARISH",
                                "BEARISH_WEAK"]):
            return "SHORT", "🟠 SHORT YẾU", "B"

        # NEUTRAL
        else:
            return "NEUTRAL", "⚪ TRUNG TÍNH", "C"

    # ─────────────────────────────────────
    def _calc_levels(self,
                      price: float,
                      atr: float,
                      direction: str) -> dict:
        """Tính Entry, SL, TP1, TP2."""
        sl_dist  = atr * RISK["sl_atr_mult"]
        tp1_dist = sl_dist * RISK["tp1_rr"]
        tp2_dist = sl_dist * RISK["tp2_rr"]

        if direction == "LONG":
            entry = price
            sl    = round(price - sl_dist,  4)
            tp1   = round(price + tp1_dist, 4)
            tp2   = round(price + tp2_dist, 4)
        elif direction == "SHORT":
            entry = price
            sl    = round(price + sl_dist,  4)
            tp1   = round(price - tp1_dist, 4)
            tp2   = round(price - tp2_dist, 4)
        else:
            entry = sl = tp1 = tp2 = price

        sl_pct  = round(sl_dist / price * 100, 3)
        tp1_pct = round(tp1_dist / price * 100, 3)
        tp2_pct = round(tp2_dist / price * 100, 3)
        rr      = round(RISK["tp1_rr"], 2)

        return {
            "entry":   entry,
            "sl":      sl,
            "tp1":     tp1,
            "tp2":     tp2,
            "sl_pct":  sl_pct,
            "tp1_pct": tp1_pct,
            "tp2_pct": tp2_pct,
            "rr":      rr,
        }

    # ─────────────────────────────────────
    def _calc_risk(self,
                    price: float,
                    atr: float,
                    direction: str,
                    mtf: dict) -> dict:
        """Đánh giá mức độ rủi ro."""
        atr_pct   = atr / price * 100
        consensus = mtf["consensus"]
        bullish   = mtf["bullish"]
        bearish   = mtf["bearish"]

        # Mức rủi ro
        if direction == "NEUTRAL":
            risk_level = "KHÔNG VÀO LỆNH"
            risk_icon  = "⛔"
            risk_note  = "Tín hiệu mâu thuẫn"

        elif consensus in ["BULLISH", "BEARISH"]:
            if atr_pct < 0.3:
                risk_level = "THẤP"
                risk_icon  = "🟢"
                risk_note  = "Biến động thấp, SL hẹp"
            elif atr_pct < 0.6:
                risk_level = "TRUNG BÌNH"
                risk_icon  = "🟡"
                risk_note  = "Biến động bình thường"
            else:
                risk_level = "CAO"
                risk_icon  = "🔴"
                risk_note  = "Biến động mạnh, SL rộng"

        else:
            risk_level = "CAO"
            risk_icon  = "🔴"
            risk_note  = "MTF chưa đồng thuận"

        # Số TF đồng thuận
        if direction == "LONG":
            aligned_tf = bullish
        elif direction == "SHORT":
            aligned_tf = bearish
        else:
            aligned_tf = 0

        return {
            "risk_level": risk_level,
            "risk_icon":  risk_icon,
            "risk_note":  risk_note,
            "aligned_tf": aligned_tf,
            "total_tf":   mtf["total"],
            "atr_pct":    round(atr_pct, 3),
        }

    # ─────────────────────────────────────
    def _build_reasons(self,
                        direction: str,
                        group_scores: dict,
                        tf_scores: dict,
                        mtf: dict) -> list:
        """
        Xây dựng danh sách lý do
        tại sao đưa ra khuyến nghị này.
        """
        reasons = []

        if direction == "NEUTRAL":
            reasons.append(
                "Các khung TF đang mâu thuẫn nhau"
            )
            reasons.append(
                "Score tổng hợp chưa đủ mạnh để xác định hướng"
            )
            return reasons

        is_long = direction == "LONG"

        # Lý do từ group scores
        for group, score in group_scores.items():
            short_name = group.split("(")[0].strip()

            if is_long and score >= 40:
                reasons.append(
                    f"{short_name} ủng hộ ({score:+.0f})"
                )
            elif not is_long and score <= -40:
                reasons.append(
                    f"{short_name} ủng hộ ({score:+.0f})"
                )

        # Lý do từ MTF
        bullish = mtf["bullish"]
        bearish = mtf["bearish"]
        total   = mtf["total"]

        if is_long and bullish >= 3:
            reasons.append(
                f"{bullish}/{total} khung TF đang Bullish"
            )
        elif not is_long and bearish >= 3:
            reasons.append(
                f"{bearish}/{total} khung TF đang Bearish"
            )

        # Lý do từ TF scores
        strong_tfs = [
            tf for tf, score in tf_scores.items()
            if (is_long and score >= 30)
            or (not is_long and score <= -30)
        ]
        tf_labels = {
            "15m": "15M", "1h": "1H",
            "4h":  "4H",  "1d": "1D"
        }
        if strong_tfs:
            tfs_str = ", ".join(
                tf_labels.get(tf, tf)
                for tf in strong_tfs
            )
            reasons.append(
                f"Tín hiệu mạnh trên khung: {tfs_str}"
            )

        return reasons if reasons else [
            "Tín hiệu kỹ thuật hội tụ nhẹ"
        ]

    # ─────────────────────────────────────
    def _build_invalidation(self,
                             direction: str,
                             price: float,
                             levels: dict,
                             analyses: dict) -> list:
        """
        Điều kiện vô hiệu hóa —
        Khi nào tín hiệu không còn hợp lệ.
        """
        inv = []

        if direction == "LONG":
            inv.append(
                f"Giá đóng nến 1H dưới "
                f"{levels['sl']:,.4f} (SL)"
            )
            # Lấy VWAP từ 1H nếu có
            try:
                vwap_1h = (
                    analyses["1h"]["trend"]
                    ["values"]["vwap"]
                )
                inv.append(
                    f"Giá đóng nến dưới VWAP 1H "
                    f"({vwap_1h:,.4f})"
                )
            except (KeyError, TypeError):
                pass

            inv.append(
                "RSI 1H giảm xuống dưới 40"
            )
            inv.append(
                "Xuất hiện nến đảo chiều mạnh "
                "(Bearish Engulfing) tại kháng cự"
            )

        elif direction == "SHORT":
            inv.append(
                f"Giá đóng nến 1H trên "
                f"{levels['sl']:,.4f} (SL)"
            )
            try:
                vwap_1h = (
                    analyses["1h"]["trend"]
                    ["values"]["vwap"]
                )
                inv.append(
                    f"Giá đóng nến trên VWAP 1H "
                    f"({vwap_1h:,.4f})"
                )
            except (KeyError, TypeError):
                pass

            inv.append(
                "RSI 1H tăng lên trên 60"
            )
            inv.append(
                "Xuất hiện nến đảo chiều mạnh "
                "(Bullish Engulfing) tại hỗ trợ"
            )

        else:
            inv.append(
                "Chờ tín hiệu rõ ràng hơn từ "
                "ít nhất 3/4 khung TF"
            )

        return inv

    # ─────────────────────────────────────
    def _build_checklist(self,
                          direction: str,
                          mtf: dict,
                          group_scores: dict,
                          risk_info: dict) -> list:
        """
        Checklist trước khi vào lệnh.
        Trả về list (text, is_checked).
        """
        if direction == "NEUTRAL":
            return [
                ("Chờ tín hiệu rõ ràng hơn", False),
                ("Không vào lệnh lúc này",    False),
            ]

        checklist = []
        is_long   = direction == "LONG"

        # MTF alignment
        aligned = (mtf["bullish"] if is_long
                   else mtf["bearish"])
        total   = mtf["total"]
        check   = aligned >= 3
        checklist.append((
            f"MTF đồng thuận: {aligned}/{total} khung",
            check
        ))

        # Trend score
        trend_score = group_scores.get(
            "Xu Hướng (Trend)", 0
        )
        trend_ok = (trend_score > 20 if is_long
                    else trend_score < -20)
        checklist.append((
            f"Xu hướng hỗ trợ "
            f"(Score: {trend_score:+.0f})",
            trend_ok
        ))

        # Momentum score
        mom_score = group_scores.get(
            "Động Lượng (Momentum)", 0
        )
        mom_ok = (mom_score > 10 if is_long
                  else mom_score < -10)
        checklist.append((
            f"Momentum xác nhận "
            f"(Score: {mom_score:+.0f})",
            mom_ok
        ))

        # Volume score
        vol_score = group_scores.get(
            "Khối Lượng (Volume)", 0
        )
        vol_ok = vol_score > 0
        checklist.append((
            f"Volume ủng hộ "
            f"(Score: {vol_score:+.0f})",
            vol_ok
        ))

        # Rủi ro
        risk_ok = risk_info["risk_level"] != "CAO"
        checklist.append((
            f"Rủi ro chấp nhận được "
            f"({risk_info['risk_level']})",
            risk_ok
        ))

        # ATR
        atr_ok = risk_info["atr_pct"] < 0.8
        checklist.append((
            f"Biến động hợp lý "
            f"(ATR={risk_info['atr_pct']:.3f}%)",
            atr_ok
        ))

        return checklist