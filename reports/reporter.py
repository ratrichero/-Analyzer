# reports/reporter.py
from colorama import Fore, Style, init
from datetime import datetime

init(autoreset=True)


class Reporter:

    # ─────────────────────────────────────
    def print_header(self,
                     symbol: str,
                     price: float,
                     mode: str = "public"):   # ← THÊM mode vào đây
        
        mode_icon = "🌐" if mode == "public" else "🔑"
        mode_text = "Public API" if mode == "public" else "CCXT API"

        print("\n" + "═" * 60)
        print(f"  📊 PHÂN TÍCH FUTURES: "
              f"{Fore.CYAN}{symbol}{Style.RESET_ALL}")
        print(f"  💰 Giá hiện tại: "
              f"{Fore.YELLOW}{price:,.4f} USDT{Style.RESET_ALL}")
        print(f"  🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  {mode_icon} Chế độ: {mode_text}")
        print("═" * 60)

    # ─────────────────────────────────────
    def print_account_info(self,
                           balance: dict,
                           positions: list):
        """Chỉ hiện trong API mode."""
        print("\n" + "─" * 60)
        print("  💼 TÀI KHOẢN FUTURES")
        print("─" * 60)
        print(f"  Số dư:      "
              f"{Fore.GREEN}{balance['total']:,.2f} USDT"
              f"{Style.RESET_ALL}")
        print(f"  Khả dụng:   "
              f"{balance['free']:,.2f} USDT")
        print(f"  Đang dùng:  "
              f"{balance['used']:,.2f} USDT")

        if positions:
            print(f"\n  📌 Vị thế đang mở: {len(positions)}")
            for p in positions:
                side  = p.get("side", "")
                color = (Fore.GREEN if side == "long"
                         else Fore.RED)
                pnl   = p.get("unrealizedPnl", 0)
                print(f"  ├── {p['symbol']} "
                      f"{color}{side.upper()}{Style.RESET_ALL} "
                      f"| PnL: {float(pnl):.2f} USDT")
        else:
            print("  📌 Không có vị thế đang mở.")

    # ─────────────────────────────────────
    def print_timeframe_analysis(self,
                                  tf: str,
                                  tf_label: str,
                                  analyses: dict):
        print(f"\n{'─' * 60}")
        print(f"  ⏱️  KHUNG {tf_label.upper()} ({tf})")
        print(f"{'─' * 60}")

        for group_result in analyses.values():
            score = group_result["score"]
            color = (Fore.GREEN  if score > 20
                     else Fore.RED    if score < -20
                     else Fore.YELLOW)

            print(f"\n  📌 {group_result['group']}")
            print(f"     Score: "
                  f"{color}{score:+.0f}/100{Style.RESET_ALL}")

            for icon, desc, bias in group_result["signals"]:
                bias_color = (Fore.GREEN  if bias == "Bullish"
                              else Fore.RED    if bias == "Bearish"
                              else Fore.YELLOW)
                print(f"     {icon} {desc} "
                      f"[{bias_color}{bias}{Style.RESET_ALL}]")

    # ─────────────────────────────────────
    def print_recommendation(self, rec: dict):
        direction = rec["direction"]
        color     = (Fore.GREEN if direction == "LONG"
                     else Fore.RED   if direction == "SHORT"
                     else Fore.WHITE)

        print("\n" + "═" * 60)
        print("  🎯 KHUYẾN NGHỊ TỔNG HỢP")
        print("═" * 60)
        print(f"\n  Hướng:      "
              f"{color}{rec['strength']}{Style.RESET_ALL}")
        print(f"  Điểm:       {rec['score']:+.1f} / 100")
        print(f"  Tin cậy:    {rec['confidence']:.1f}%")

        if direction != "NEUTRAL":
            print(f"\n  📍 THIẾT LẬP LỆNH:")
            print(f"  ├── Entry : "
                  f"{Fore.CYAN}{rec['entry']:>12,.4f}"
                  f"{Style.RESET_ALL}")
            print(f"  ├── SL    : "
                  f"{Fore.RED}{rec['sl']:>12,.4f}  "
                  f"(-{rec['sl_pct']:.3f}%){Style.RESET_ALL}")
            print(f"  ├── TP1   : "
                  f"{Fore.GREEN}{rec['tp1']:>12,.4f}  "
                  f"(+{rec['tp1_pct']:.3f}%){Style.RESET_ALL}")
            print(f"  └── TP2   : "
                  f"{Fore.GREEN}{rec['tp2']:>12,.4f}"
                  f"{Style.RESET_ALL}")
            print(f"\n  📐 ATR 1H : {rec['atr']:,.4f}")
        else:
            print(f"\n  ⚪ Tín hiệu chưa rõ ràng, "
                  f"chờ xác nhận thêm.")

        print("\n" + "═" * 60)
        print("  ⚠️  Chỉ mang tính tham khảo, "
              "không phải lời khuyên đầu tư.")
        print("═" * 60 + "\n")
    
    # Thêm method này vào class Reporter
    # (Giữ nguyên tất cả method cũ)

    def print_recommendation_full(self, rec: dict):
        """
        In báo cáo khuyến nghị đầy đủ cho CLI.
        Thay thế print_recommendation() cũ.
        """
        direction = rec["direction"]
        color     = (Fore.GREEN if direction == "LONG"
                     else Fore.RED   if direction == "SHORT"
                     else Fore.WHITE)

        # ── Header ────────────────────────
        print("\n" + "═" * 60)
        print("  🎯 KHUYẾN NGHỊ GIAO DỊCH")
        print("═" * 60)

        # ── MTF Summary ───────────────────
        print(f"\n  📈 TỔNG HỢP ĐA KHUNG (MTF)")
        tf_labels = {
            "15m": "15M", "1h": "1H",
            "4h":  "4H",  "1d": "1D",
        }
        for tf, score in rec["tf_scores"].items():
            label     = tf_labels.get(tf, tf)
            score_clr = (Fore.GREEN if score > 20
                         else Fore.RED if score < -20
                         else Fore.YELLOW)
            bar = self._cli_bar(score)
            print(f"  {label:4} {bar} "
                  f"{score_clr}{score:+.0f}{Style.RESET_ALL}")

        mtf = rec["mtf_alignment"]
        print(
            f"\n  🔀 Đồng thuận: "
            f"{Fore.CYAN}{mtf['consensus']}{Style.RESET_ALL} "
            f"({mtf['consensus_pct']:.0f}%) | "
            f"Bull: {mtf['bullish']}/{mtf['total']} | "
            f"Bear: {mtf['bearish']}/{mtf['total']}"
        )

        # ── Group Scores ──────────────────
        print(f"\n  📌 ĐIỂM 5 NHÓM CHỈ BÁO (TB 4 TF)")
        short_names = {
            "Xu Hướng (Trend)":        "Xu Hướng   ",
            "Động Lượng (Momentum)":   "Động Lượng ",
            "Biến Động (Volatility)":  "Biến Động  ",
            "Khối Lượng (Volume)":     "Khối Lượng ",
            "Hỗ Trợ/Kháng Cự (S/R)":  "Hỗ Trợ/KCự",
        }
        for group, score in rec["group_scores"].items():
            name      = short_names.get(group, group)
            score_clr = (Fore.GREEN if score > 20
                         else Fore.RED if score < -20
                         else Fore.YELLOW)
            bar = self._cli_bar(score)
            print(f"  {name} {bar} "
                  f"{score_clr}{score:+.0f}{Style.RESET_ALL}")

        # ── Khuyến nghị chính ─────────────
        print("\n" + "═" * 60)
        print(
            f"  {color}{rec['strength']}{Style.RESET_ALL}"
        )
        print(f"  Điểm tổng : {rec['score']:+.1f} / 100")
        print(f"  Tin cậy   : {rec['confidence']:.0f}%")

        risk = rec["risk_info"]
        print(
            f"  Rủi ro    : {risk['risk_icon']} "
            f"{risk['risk_level']} — {risk['risk_note']}"
        )

        # ── Levels ────────────────────────
        if direction != "NEUTRAL":
            print(f"\n  💹 THIẾT LẬP LỆNH")
            print(f"  ┌ Entry : "
                  f"{Fore.CYAN}{rec['entry']:>14,.4f}"
                  f"{Style.RESET_ALL}")
            print(f"  ├ SL    : "
                  f"{Fore.RED}{rec['sl']:>14,.4f}  "
                  f"(-{rec['sl_pct']:.2f}%){Style.RESET_ALL}")
            print(f"  ├ TP1   : "
                  f"{Fore.GREEN}{rec['tp1']:>14,.4f}  "
                  f"(+{rec['tp1_pct']:.2f}%){Style.RESET_ALL}")
            print(f"  └ TP2   : "
                  f"{Fore.GREEN}{rec['tp2']:>14,.4f}  "
                  f"(+{rec['tp2_pct']:.2f}%){Style.RESET_ALL}")
            print(f"\n  RR: 1:{rec['rr']} | "
                  f"ATR 1H: {rec['atr']:,.4f}")

        # ── Lý do ─────────────────────────
        if rec.get("reasons"):
            print(f"\n  💡 LÝ DO KHUYẾN NGHỊ")
            for r in rec["reasons"]:
                print(f"  ▸ {r}")

        # ── Vô hiệu hóa ───────────────────
        if rec.get("invalidation"):
            print(f"\n  🚫 VÔ HIỆU HÓA KHI")
            for item in rec["invalidation"]:
                print(f"  ✗ {item}")

        # ── Checklist ─────────────────────
        if rec.get("checklist"):
            print(f"\n  ✅ CHECKLIST VÀO LỆNH")
            pass_cnt = 0
            total    = len(rec["checklist"])

            for text, ok in rec["checklist"]:
                icon = (f"{Fore.GREEN}✅"
                        if ok
                        else f"{Fore.RED}❌")
                print(f"  {icon} {text}{Style.RESET_ALL}")
                if ok:
                    pass_cnt += 1

            # Kết luận checklist
            print()
            if pass_cnt == total:
                print(
                    f"  {Fore.GREEN}● {pass_cnt}/{total} "
                    f"ĐỦ ĐIỀU KIỆN → CÓ THỂ VÀO LỆNH"
                    f"{Style.RESET_ALL}"
                )
            elif pass_cnt >= total * 0.7:
                print(
                    f"  {Fore.YELLOW}● {pass_cnt}/{total} "
                    f"→ CÂN NHẮC KỸ TRƯỚC KHI VÀO"
                    f"{Style.RESET_ALL}"
                )
            else:
                print(
                    f"  {Fore.RED}● {pass_cnt}/{total} "
                    f"→ CHƯA ĐỦ ĐIỀU KIỆN, CHỜ THÊM"
                    f"{Style.RESET_ALL}"
                )

        # ── Footer ────────────────────────
        print("\n" + "═" * 60)
        print("  ⚠️  Chỉ mang tính tham khảo kỹ thuật.")
        print("      Không phải lời khuyên đầu tư.")
        print("═" * 60 + "\n")

    # ─────────────────────────────────────
    def _cli_bar(self, score: float,
                  width: int = 8) -> str:
        """Visual bar cho CLI."""
        filled = int(min(abs(score), 100) / 100 * width)
        empty  = width - filled
        if score >= 0:
            bar = f"[{'█' * filled}{'░' * empty}]"
        else:
            bar = f"[{'░' * empty}{'█' * filled}]"
        return bar