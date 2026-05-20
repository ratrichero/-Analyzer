# main.py
import sys
from colorama import Fore, Style, init

from data.fetcher_factory         import create_fetcher, get_mode_info
from analyzers.trend              import TrendAnalyzer
from analyzers.momentum           import MomentumAnalyzer
from analyzers.volatility         import VolatilityAnalyzer
from analyzers.volume             import VolumeAnalyzer
from analyzers.support_resistance import SRAnalyzer
from signals.recommendation       import RecommendationEngine
from reports.reporter             import Reporter
from config                       import TIMEFRAMES

init(autoreset=True)


# ─────────────────────────────────────────
def print_banner(mode_info: dict):
    """In banner khởi động."""
    print("\n" + "═" * 60)
    print("  🤖 BINANCE FUTURES ANALYZER")
    print("═" * 60)
    print(
        f"\n  Chế độ: {mode_info['icon']} "
        f"{Fore.CYAN}{mode_info['name']}{Style.RESET_ALL}"
        f" — {mode_info['description']}"
    )
    print(f"\n  Tính năng:")
    for feature in mode_info["features"]:
        print(f"    {feature}")
    print()


# ─────────────────────────────────────────
def print_divider():
    print("\n" + "─" * 60)


# ─────────────────────────────────────────
def ask_next_action() -> str:
    """
    Hỏi người dùng muốn làm gì tiếp theo.
    Trả về: symbol | 'quit' | 'menu'
    """
    print("\n" + "─" * 60)
    print(f"  {Fore.CYAN}Bạn muốn làm gì tiếp theo?{Style.RESET_ALL}")
    print(f"  {'─' * 40}")
    print(f"  {Fore.GREEN}[1]{Style.RESET_ALL} Phân tích coin khác")
    print(f"  {Fore.GREEN}[2]{Style.RESET_ALL} Phân tích lại coin vừa xong")
    print(f"  {Fore.GREEN}[3]{Style.RESET_ALL} Xem danh sách coin gợi ý")
    print(f"  {Fore.RED}[0]{Style.RESET_ALL} Thoát chương trình")
    print(f"  {'─' * 40}")

    choice = input(
        f"  Nhập lựa chọn hoặc tên coin "
        f"(VD: ETH, SOL): "
    ).strip()

    return choice


# ─────────────────────────────────────────
def print_suggested_coins():
    """In danh sách coin gợi ý."""
    from config import POPULAR_COINS

    print(f"\n  {Fore.CYAN}⭐ COIN PHỔ BIẾN{Style.RESET_ALL}")
    print(f"  {'─' * 40}")

    row = []
    for coin in POPULAR_COINS:
        name = coin.replace("USDT", "")
        row.append(f"{name:8}")
        if len(row) == 4:
            print("  " + "  ".join(row))
            row = []
    if row:
        print("  " + "  ".join(row))

    print(f"  {'─' * 40}")
    print(
        f"  💡 Nhập tên coin để phân tích "
        f"(VD: BTC, ETH, SOL)"
    )


# ─────────────────────────────────────────
def run_analysis(
        symbol: str,
        fetcher,
        reporter: Reporter) -> bool:
    """
    Chạy phân tích 1 coin.
    Trả về True nếu thành công, False nếu lỗi.
    """
    try:
        # ── Validate ──────────────────────
        print(
            f"\n  🔍 Kiểm tra symbol "
            f"'{Fore.YELLOW}{symbol}{Style.RESET_ALL}'..."
        )
        symbol = fetcher.validate_symbol(symbol)
        print(
            f"  ✅ Hợp lệ: "
            f"{Fore.CYAN}{symbol}{Style.RESET_ALL}"
        )

        # ── Giá hiện tại ──────────────────
        price = fetcher.get_current_price(symbol)

        # ── Lấy dữ liệu ──────────────────
        print(f"\n  📡 Đang tải dữ liệu...")
        data = fetcher.fetch_all_timeframes(symbol)

        # ── Header ────────────────────────
        reporter.print_header(
            symbol, price, fetcher.MODE
        )

        # ── Phân tích 5 nhóm × 4 TF ──────
        analyzers = {
            "trend":      TrendAnalyzer(),
            "momentum":   MomentumAnalyzer(),
            "volatility": VolatilityAnalyzer(),
            "volume":     VolumeAnalyzer(),
            "sr":         SRAnalyzer(),
        }

        all_analyses = {}
        for tf, tf_config in TIMEFRAMES.items():
            df        = data[tf]
            tf_result = {}
            for name, analyzer in analyzers.items():
                tf_result[name] = analyzer.analyze(
                    df, tf
                )
            all_analyses[tf] = tf_result

            reporter.print_timeframe_analysis(
                tf,
                tf_config["label"],
                tf_result
            )

        # ── Khuyến nghị ───────────────────
        atr_1h = (
            all_analyses["1h"]["volatility"]
            ["values"]["atr"]
        )
        engine = RecommendationEngine()
        rec    = engine.calculate(
            all_analyses, price, atr_1h
        )

        reporter.print_recommendation_full(rec)
        return True

    except ValueError as e:
        print(f"\n  {Fore.RED}❌ {e}{Style.RESET_ALL}")
        print(
            f"  💡 Thử lại với: BTC, ETH, SOL, BNB..."
        )
        return False

    except ConnectionError as e:
        print(f"\n  {Fore.RED}❌ {e}{Style.RESET_ALL}")
        return False

    except Exception as e:
        print(
            f"\n  {Fore.RED}❌ Lỗi: {e}{Style.RESET_ALL}"
        )
        import traceback
        traceback.print_exc()
        return False


# ─────────────────────────────────────────
def get_first_symbol() -> str:
    """Lấy symbol đầu tiên từ argument hoặc input."""
    if len(sys.argv) > 1:
        return sys.argv[1]

    print(
        f"  {Fore.CYAN}Nhập cặp giao dịch để bắt đầu"
        f"{Style.RESET_ALL}"
    )
    print(
        "  (VD: BTC / ETH / SOL / BTCUSDT)"
    )
    return input("\n  Coin: ").strip()


# ─────────────────────────────────────────
def main():
    """
    Vòng lặp chính CLI.
    Cho phép phân tích nhiều coin liên tiếp.
    """
    # ── Banner ────────────────────────────
    mode_info = get_mode_info()
    print_banner(mode_info)

    # ── Khởi tạo fetcher & reporter ───────
    try:
        fetcher  = create_fetcher()
        reporter = Reporter()
    except ValueError as e:
        print(f"\n{Fore.RED}❌ {e}{Style.RESET_ALL}")
        return
    except ImportError as e:
        print(f"\n{Fore.RED}❌ {e}{Style.RESET_ALL}")
        return

    # ── Symbol đầu tiên ───────────────────
    symbol = get_first_symbol()
    if not symbol:
        print(
            f"{Fore.RED}❌ Vui lòng nhập symbol."
            f"{Style.RESET_ALL}"
        )
        return

    last_symbol = symbol.upper()

    # ══════════════════════════════════════
    # VÒNG LẶP CHÍNH
    # ══════════════════════════════════════
    while True:
        try:
            # ── Chạy phân tích ────────────
            run_analysis(last_symbol, fetcher, reporter)

            # ── Hỏi tiếp theo ─────────────
            while True:
                choice = ask_next_action()

                # Thoát
                if choice in ("0", "q", "quit",
                              "exit", "thoát"):
                    print(
                        f"\n  {Fore.CYAN}👋 Tạm biệt!"
                        f"{Style.RESET_ALL}\n"
                    )
                    return

                # Phân tích lại
                elif choice in ("2", ""):
                    print(
                        f"\n  🔄 Phân tích lại "
                        f"{Fore.CYAN}{last_symbol}"
                        f"{Style.RESET_ALL}..."
                    )
                    break   # Quay lại vòng while ngoài

                # Xem danh sách coin
                elif choice == "3":
                    print_suggested_coins()
                    coin_input = input(
                        "\n  Nhập coin: "
                    ).strip()
                    if coin_input:
                        last_symbol = (
                            coin_input.upper()
                        )
                        break

                # Nhập coin mới
                elif choice == "1":
                    coin_input = input(
                        f"\n  Nhập tên coin "
                        f"(VD: ETH, SOL, BNB): "
                    ).strip()
                    if coin_input:
                        last_symbol = (
                            coin_input.upper()
                        )
                        break
                    else:
                        print(
                            f"  {Fore.YELLOW}⚠️  "
                            f"Vui lòng nhập tên coin."
                            f"{Style.RESET_ALL}"
                        )

                # Nhập trực tiếp tên coin
                elif (choice.isalpha()
                      and len(choice) <= 10):
                    last_symbol = choice.upper()
                    break

                # Input không hợp lệ
                else:
                    print(
                        f"  {Fore.YELLOW}⚠️  "
                        f"Không hợp lệ. "
                        f"Nhập 0/1/2/3 "
                        f"hoặc tên coin."
                        f"{Style.RESET_ALL}"
                    )

        except KeyboardInterrupt:
            print(
                f"\n\n  {Fore.CYAN}👋 Đã dừng."
                f"{Style.RESET_ALL}\n"
            )
            return


# ─────────────────────────────────────────
if __name__ == "__main__":
    main()