# analyzers/momentum.py
import pandas as pd
import pandas_ta as ta
from config import INDICATORS


class MomentumAnalyzer:
    """
    Nhóm 2 — ĐỘNG LƯỢNG
    Chỉ báo: RSI, MACD, Stochastic
    """

    def _get_macd_columns(self,
                           macd_df: pd.DataFrame) -> tuple:
        cols       = macd_df.columns.tolist()
        macd_col   = next((c for c in cols
                           if c.startswith("MACD_")),  None)
        signal_col = next((c for c in cols
                           if c.startswith("MACDs_")), None)
        hist_col   = next((c for c in cols
                           if c.startswith("MACDh_")), None)
        if not all([macd_col, signal_col, hist_col]):
            raise KeyError(
                f"❌ Không tìm thấy cột MACD: {cols}"
            )
        return macd_col, signal_col, hist_col

    def _get_stoch_columns(self,
                            stoch_df: pd.DataFrame) -> tuple:
        cols  = stoch_df.columns.tolist()
        k_col = next((c for c in cols
                      if c.startswith("STOCHk_")), None)
        d_col = next((c for c in cols
                      if c.startswith("STOCHd_")), None)
        if not all([k_col, d_col]):
            raise KeyError(
                f"❌ Không tìm thấy cột Stochastic: {cols}"
            )
        return k_col, d_col

    # ─────────────────────────────────────
    def analyze(self, df: pd.DataFrame, tf: str) -> dict:
        c = df["close"]
        h = df["high"]
        l = df["low"]

        # ── RSI ───────────────────────────────
        rsi   = ta.rsi(c, length=INDICATORS["rsi_period"])
        rsi_v = rsi.iloc[-1]
        rsi_p = rsi.iloc[-2]

        # ── MACD ──────────────────────────────
        macd_df = ta.macd(
            c,
            fast=INDICATORS["macd_fast"],
            slow=INDICATORS["macd_slow"],
            signal=INDICATORS["macd_signal"]
        )
        macd_col, signal_col, hist_col = \
            self._get_macd_columns(macd_df)

        macd_v   = macd_df[macd_col].iloc[-1]
        signal_v = macd_df[signal_col].iloc[-1]
        hist_v   = macd_df[hist_col].iloc[-1]
        hist_p   = macd_df[hist_col].iloc[-2]

        # ── Stochastic ────────────────────────
        stoch_df = ta.stoch(
            h, l, c,
            k=INDICATORS["stoch_k"],
            d=INDICATORS["stoch_d"]
        )
        k_col, d_col = self._get_stoch_columns(stoch_df)

        stoch_k = stoch_df[k_col].iloc[-1]
        stoch_d = stoch_df[d_col].iloc[-1]

        # ── Scoring ───────────────────────────
        score   = 0
        signals = []

        # RSI
        if rsi_v > INDICATORS["rsi_ob"]:
            score -= 20
            signals.append((
                "🔴",
                f"RSI={rsi_v:.1f} Quá mua",
                "Bearish"
            ))
        elif rsi_v < INDICATORS["rsi_os"]:
            score += 20
            signals.append((
                "✅",
                f"RSI={rsi_v:.1f} Quá bán",
                "Bullish"
            ))
        elif rsi_v > 55:
            score += 15
            signals.append((
                "✅",
                f"RSI={rsi_v:.1f} Bullish zone",
                "Bullish"
            ))
        elif rsi_v < 45:
            score -= 15
            signals.append((
                "🔴",
                f"RSI={rsi_v:.1f} Bearish zone",
                "Bearish"
            ))
        else:
            signals.append((
                "⚠️",
                f"RSI={rsi_v:.1f} Trung tính",
                "Neutral"
            ))

        # RSI Momentum
        if rsi_v > rsi_p:
            score += 10
            signals.append(("✅", "RSI đang tăng", "Bullish"))
        else:
            score -= 10
            signals.append(("🔴", "RSI đang giảm", "Bearish"))

        # MACD
        if macd_v > signal_v:
            score += 20
            signals.append(("✅", "MACD trên Signal", "Bullish"))
        else:
            score -= 20
            signals.append(("🔴", "MACD dưới Signal", "Bearish"))

        # MACD Histogram
        if hist_v > 0 and hist_v > hist_p:
            score += 15
            signals.append((
                "✅", "Histogram tăng dương", "Bullish"
            ))
        elif hist_v < 0 and hist_v < hist_p:
            score -= 15
            signals.append((
                "🔴", "Histogram giảm âm", "Bearish"
            ))

        # Stochastic
        if (stoch_k < INDICATORS["stoch_os"]
                and stoch_k > stoch_d):
            score += 20
            signals.append((
                "✅",
                f"Stoch={stoch_k:.1f} Quá bán + Cross lên",
                "Bullish"
            ))
        elif (stoch_k > INDICATORS["stoch_ob"]
              and stoch_k < stoch_d):
            score -= 20
            signals.append((
                "🔴",
                f"Stoch={stoch_k:.1f} Quá mua + Cross xuống",
                "Bearish"
            ))
        else:
            signals.append((
                "⚠️",
                f"Stoch={stoch_k:.1f} Trung tính",
                "Neutral"
            ))

        return {
            "group":   "Động Lượng (Momentum)",
            "score":   max(-100, min(100, score)),
            "signals": signals,
            "values": {
                "rsi":     round(rsi_v,   2),
                "macd":    round(macd_v,  4),
                "signal":  round(signal_v, 4),
                "hist":    round(hist_v,  4),
                "stoch_k": round(stoch_k, 2),
                "stoch_d": round(stoch_d, 2),
            },
        }