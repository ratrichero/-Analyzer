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