# main.py
import sys
from colorama import Fore, Style, init

from data.fetcher_factory       import create_fetcher, get_mode_info
from analyzers.trend            import TrendAnalyzer
from analyzers.momentum         import MomentumAnalyzer
from analyzers.volatility       import VolatilityAnalyzer
from analyzers.volume           import VolumeAnalyzer
from analyzers.support_resistance import SRAnalyzer
from signals.recommendation     import RecommendationEngine
from reports.reporter           import Reporter
from config                     import TIMEFRAMES

init(autoreset=True)


# ─────────────────────────────────────────
def print_banner():
    """In banner khởi động với thông tin mode."""
    mode_info = get_mode_info()

    print("\n" + "═" * 60)
    print(f"  🤖 BINANCE FUTURES ANALYZER")
    print("═" * 60)
    print(f"\n  Chế độ: {mode_info['icon']} "
          f"{Fore.CYAN}{mode_info['name']}{Style.RESET_ALL} "
          f"— {mode_info['description']}")
    print(f"\n  Tính năng:")
    for feature in mode_info["features"]:
        print(f"    {feature}")

    if mode_info["need_key"]:
        print(f"\n  {Fore.YELLOW}⚠️  Đang dùng API Key "
              f"cá nhân{Style.RESET_ALL}")

    print()


# ─────────────────────────────────────────
def run_analysis(symbol: str, fetcher):
    reporter = Reporter()

    # ── Validate ──────────────────────────
    print(f"  🔍 Kiểm tra symbol '{symbol}'...")
    symbol = fetcher.validate_symbol(symbol)
    print(f"  ✅ Hợp lệ: {Fore.CYAN}{symbol}{Style.RESET_ALL}")

    # ── Giá hiện tại ──────────────────────
    price = fetcher.get_current_price(symbol)

    # ── Lấy dữ liệu ──────────────────────
    print(f"\n  📡 Đang tải dữ liệu...")
    data = fetcher.fetch_all_timeframes(symbol)

    # ── Thông tin tài khoản (API mode) ───
    if fetcher.MODE == "api":
        try:
            balance   = fetcher.get_account_balance()
            positions = fetcher.get_open_positions()
            reporter.print_account_info(balance, positions)
        except Exception:
            pass  # Bỏ qua nếu không lấy được

    # ── In Header ─────────────────────────
    reporter.print_header(symbol, price, fetcher.MODE)

    # ── Phân tích ─────────────────────────
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
            tf_result[name] = analyzer.analyze(df, tf)

        all_analyses[tf] = tf_result
        reporter.print_timeframe_analysis(
            tf, tf_config["label"], tf_result
        )

    # ── Khuyến nghị ───────────────────────
    atr_1h = all_analyses["1h"]["volatility"]["values"]["atr"]
    engine  = RecommendationEngine()
    rec     = engine.calculate(all_analyses, price, atr_1h)
    reporter.print_recommendation(rec)


# ─────────────────────────────────────────
def main():
    print_banner()

    # Symbol từ argument hoặc input
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    else:
        symbol = input(
            "  Nhập cặp giao dịch "
            "(VD: BTC / ETH / SOL): "
        ).strip()

    if not symbol:
        print("❌ Vui lòng nhập symbol.")
        return

    try:
        # Factory tự động chọn fetcher đúng mode
        fetcher = create_fetcher()
        run_analysis(symbol, fetcher)

    except ValueError as e:
        print(f"\n{e}")

    except ConnectionError as e:
        print(f"\n{e}")

    except ImportError as e:
        print(f"\n{e}")

    except KeyboardInterrupt:
        print("\n\n  👋 Đã hủy.")

    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()