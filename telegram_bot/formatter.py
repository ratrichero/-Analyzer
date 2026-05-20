# telegram_bot/formatter.py


class TelegramFormatter:

    # ─────────────────────────────────────
    def format_full_report(self,
                           symbol: str,
                           price: float,
                           all_analyses: dict,
                           rec: dict) -> str:
        parts = [
            self._section_header(symbol, price),
            self._section_mtf_summary(
                rec["tf_scores"],
                rec["mtf_alignment"]
            ),
            self._section_group_scores(
                rec["group_scores"]
            ),
            self._section_recommendation(rec),
            self._section_levels(rec),
            self._section_reasons(rec),
            self._section_invalidation(rec),
            self._section_checklist(rec),
            self._section_footer(),
        ]
        return "\n".join(parts)

    # ═════════════════════════════════════
    # CÁC SECTION
    # ═════════════════════════════════════

    def _section_header(self,
                         symbol: str,
                         price: float) -> str:
        return (
            f"📊 *PHÂN TÍCH FUTURES*\n"
            f"*{symbol}* — `{price:,.4f} USDT`\n"
            f"{'─' * 28}"
        )

    # ─────────────────────────────────────
    def _section_mtf_summary(self,
                               tf_scores: dict,
                               mtf: dict) -> str:
        tf_labels = {
            "15m": "15M", "1h": "1H",
            "4h":  "4H",  "1d": "1D",
        }
        lines = ["\n📈 *TỔNG HỢP ĐA KHUNG (MTF)*"]

        for tf, score in tf_scores.items():
            label = tf_labels.get(tf, tf)
            bar   = self._mini_bar(score)
            icon  = self._score_icon(score)
            lines.append(
                f"  {icon} `{label}` {bar} `{score:+.0f}`"
            )

        # MTF Consensus
        consensus_map = {
            "BULLISH":      "🟢 Đồng thuận TĂNG",
            "BEARISH":      "🔴 Đồng thuận GIẢM",
            "BULLISH_WEAK": "🟡 Nghiêng về TĂNG",
            "BEARISH_WEAK": "🟠 Nghiêng về GIẢM",
            "MIXED":        "⚪ Mâu thuẫn",
        }
        consensus_text = consensus_map.get(
            mtf["consensus"], "⚪ Không rõ"
        )

        lines.append(
            f"\n  🔀 MTF: {consensus_text} "
            f"`({mtf['consensus_pct']:.0f}%)`"
        )
        lines.append(
            f"  ▸ Bullish: {mtf['bullish']}/{mtf['total']} "
            f"khung | Bearish: {mtf['bearish']}/{mtf['total']} khung"
        )

        return "\n".join(lines)

    # ─────────────────────────────────────
    def _section_group_scores(self,
                               group_scores: dict) -> str:
        short_names = {
            "Xu Hướng (Trend)":        "Xu Hướng",
            "Động Lượng (Momentum)":   "Động Lượng",
            "Biến Động (Volatility)":  "Biến Động",
            "Khối Lượng (Volume)":     "Khối Lượng",
            "Hỗ Trợ/Kháng Cự (S/R)":  "Hỗ Trợ/KCự",
        }
        lines = ["\n📌 *ĐIỂM 5 NHÓM CHỈ BÁO* _(TB 4 TF)_"]

        for group, score in group_scores.items():
            name = short_names.get(group, group)
            icon = self._score_icon(score)
            bar  = self._mini_bar(score)
            lines.append(
                f"  {icon} `{name:12}` "
                f"{bar} `{score:+.0f}`"
            )

        return "\n".join(lines)

    # ─────────────────────────────────────
    def _section_recommendation(self,
                                  rec: dict) -> str:
        direction    = rec["direction"]
        signal_icons = {"A": "⚡", "B": "✳️", "C": "💤"}
        sig_icon     = signal_icons.get(
            rec["signal_level"], ""
        )

        lines = [
            f"\n{'═' * 28}",
            f"🎯 *KHUYẾN NGHỊ*",
            f"{'═' * 28}",
            f"\n{sig_icon} {rec['strength']}",
            f"📊 Điểm tổng: `{rec['score']:+.1f}/100`",
            f"🎯 Tin cậy:   `{rec['confidence']:.0f}%`",
        ]

        # Risk
        risk = rec["risk_info"]
        lines.append(
            f"{risk['risk_icon']} Rủi ro: "
            f"`{risk['risk_level']}`"
            f" — _{risk['risk_note']}_"
        )

        return "\n".join(lines)

    # ─────────────────────────────────────
    def _section_levels(self, rec: dict) -> str:
        direction = rec["direction"]

        if direction == "NEUTRAL":
            return (
                "\n⚪ _Không có tín hiệu rõ ràng._\n"
                "_Chờ thêm xác nhận từ thị trường._"
            )

        lines = [
            f"\n💹 *THIẾT LẬP LỆNH*",
            f"┌ Entry  : `{rec['entry']:>14,.4f}`",
            f"├ SL     : `{rec['sl']:>14,.4f}`"
            f"  _(-{rec['sl_pct']:.2f}%)_",
            f"├ TP1    : `{rec['tp1']:>14,.4f}`"
            f"  _(+{rec['tp1_pct']:.2f}%)_",
            f"└ TP2    : `{rec['tp2']:>14,.4f}`"
            f"  _(+{rec['tp2_pct']:.2f}%)_",
            f"\n  RR: `1:{rec['rr']}` "
            f"| ATR: `{rec['atr']:,.4f}`",
        ]
        return "\n".join(lines)

    # ─────────────────────────────────────
    def _section_reasons(self, rec: dict) -> str:
        reasons = rec.get("reasons", [])
        if not reasons:
            return ""

        lines = ["\n💡 *LÝ DO KHUYẾN NGHỊ*"]
        for r in reasons:
            lines.append(f"  ▸ _{r}_")

        return "\n".join(lines)

    # ─────────────────────────────────────
    def _section_invalidation(self, rec: dict) -> str:
        inv = rec.get("invalidation", [])
        if not inv:
            return ""

        lines = ["\n🚫 *VÔ HIỆU HÓA KHI*"]
        for item in inv:
            lines.append(f"  ✗ _{item}_")

        return "\n".join(lines)

    # ─────────────────────────────────────
    def _section_checklist(self, rec: dict) -> str:
        checklist = rec.get("checklist", [])
        if not checklist:
            return ""

        lines = ["\n✅ *CHECKLIST VÀO LỆNH*"]

        all_ok   = all(ok for _, ok in checklist)
        pass_cnt = sum(1 for _, ok in checklist if ok)
        total    = len(checklist)

        for text, ok in checklist:
            icon = "✅" if ok else "❌"
            lines.append(f"  {icon} _{text}_")

        # Tổng kết checklist
        if all_ok:
            lines.append(
                f"\n  🟢 *{pass_cnt}/{total} ĐỦ ĐIỀU KIỆN "
                f"→ CÓ THỂ VÀO LỆNH*"
            )
        elif pass_cnt >= total * 0.7:
            lines.append(
                f"\n  🟡 *{pass_cnt}/{total} → "
                f"CÂN NHẮC KỸ TRƯỚC KHI VÀO*"
            )
        else:
            lines.append(
                f"\n  🔴 *{pass_cnt}/{total} → "
                f"CHƯA ĐỦ ĐIỀU KIỆN, CHỜ THÊM*"
            )

        return "\n".join(lines)

    # ─────────────────────────────────────
    def _section_footer(self) -> str:
        return (
            f"\n{'─' * 28}\n"
            f"⚠️ _Chỉ mang tính tham khảo kỹ thuật._\n"
            f"_Không phải lời khuyên đầu tư._"
        )

    # ─────────────────────────────────────
    def format_single_tf(self,
                          symbol: str,
                          price: float,
                          tf: str,
                          tf_data: dict) -> str:
        tf_labels = {
            "15m": "15 Phút", "1h": "1 Giờ",
            "4h":  "4 Giờ",   "1d": "1 Ngày",
        }
        lines = [
            f"📊 *{symbol}* — "
            f"Khung `{tf_labels.get(tf, tf)}`",
            f"💰 Giá: `{price:,.4f} USDT`",
            f"{'─' * 28}",
        ]

        for group_data in tf_data.values():
            group = group_data["group"]
            score = group_data["score"]
            icon  = self._score_icon(score)

            lines.append(
                f"\n{icon} *{group}* `{score:+.0f}/100`"
            )
            for sig_icon, desc, _ in \
                    group_data["signals"]:
                lines.append(
                    f"  {sig_icon} _{desc}_"
                )

        lines.append(
            f"\n{'─' * 28}\n"
            f"⚠️ _Chỉ mang tính tham khảo._"
        )
        return "\n".join(lines)

    # ─────────────────────────────────────
    def format_error(self, error_msg: str) -> str:
        return (
            f"❌ *Lỗi xử lý*\n\n"
            f"`{error_msg}`\n\n"
            f"_Vui lòng thử lại._"
        )

    # ═════════════════════════════════════
    # HELPERS
    # ═════════════════════════════════════

    def _mini_bar(self, score: float) -> str:
        """Bar 5 ký tự theo score."""
        filled = int(min(abs(score), 100) / 100 * 5)
        empty  = 5 - filled
        if score > 0:
            return f"`[{'█' * filled}{'░' * empty}]`"
        else:
            return f"`[{'░' * empty}{'█' * filled}]`"

    def _score_icon(self, score: float) -> str:
        if score >= 60:   return "🟢"
        elif score >= 20: return "🟡"
        elif score >= -20: return "⚪"
        elif score >= -60: return "🟠"
        else:              return "🔴"
    
    def format_recommendation_only(self,
                                    symbol: str,
                                    price: float,
                                    rec: dict) -> str:
        """
        Format RIÊNG phần Khuyến nghị
        Dùng cho tính năng 🎯 Khuyến nghị
        """
        parts = [
            # Header
            f"🎯 *KHUYẾN NGHỊ GIAO DỊCH*\n"
            f"*{symbol}* — `{price:,.4f} USDT`\n"
            f"{'═' * 28}",

            # MTF Summary ngắn gọn
            self._section_mtf_summary(
                rec["tf_scores"],
                rec["mtf_alignment"]
            ),

            # Khuyến nghị chính
            self._section_recommendation(rec),

            # Levels
            self._section_levels(rec),

            # Lý do
            self._section_reasons(rec),

            # Vô hiệu hóa
            self._section_invalidation(rec),

            # Checklist
            self._section_checklist(rec),

            # Footer
            self._section_footer(),
        ]
        return "\n".join(parts)