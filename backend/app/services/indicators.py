import numpy as np
import pandas as pd


class IndicatorsService:
    def calculate_all(self, history: list[dict]) -> dict:
        if not history or len(history) < 20:
            return {"error": "Insufficient data"}

        closes = pd.Series([h["close"] for h in history])
        highs = pd.Series([h["high"] for h in history])
        lows = pd.Series([h["low"] for h in history])
        volumes = pd.Series([h["volume"] for h in history])

        return {
            "ma5": self._ma(closes, 5),
            "ma10": self._ma(closes, 10),
            "ma20": self._ma(closes, 20),
            "ma60": self._ma(closes, 60) if len(closes) >= 60 else [],
            "rsi": self._rsi(closes),
            "macd": self._macd(closes),
            "bollinger": self._bollinger(closes),
            "kdj": self._kdj(closes, highs, lows),
            "volume_ma5": self._ma(volumes, 5),
        }

    def _ma(self, series: pd.Series, period: int) -> list[float]:
        return series.rolling(window=period).mean().round(2).tolist()

    def _rsi(self, closes: pd.Series, period: int = 14) -> float:
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        return round(float(val), 2) if pd.notna(val) else 50.0

    def _macd(self, closes: pd.Series) -> dict:
        ema12 = closes.ewm(span=12, adjust=False).mean()
        ema26 = closes.ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        macd_bar = (dif - dea) * 2
        return {
            "dif": round(float(dif.iloc[-1]), 4),
            "dea": round(float(dea.iloc[-1]), 4),
            "macd": round(float(macd_bar.iloc[-1]), 4),
            "dif_list": dif.round(4).tolist(),
            "dea_list": dea.round(4).tolist(),
            "macd_list": macd_bar.round(4).tolist(),
        }

    def _bollinger(self, closes: pd.Series, period: int = 20) -> dict:
        mid = closes.rolling(window=period).mean()
        std = closes.rolling(window=period).std()
        return {
            "upper": round(float((mid + 2 * std).iloc[-1]), 2),
            "mid": round(float(mid.iloc[-1]), 2),
            "lower": round(float((mid - 2 * std).iloc[-1]), 2),
        }

    def _kdj(self, closes: pd.Series, highs: pd.Series, lows: pd.Series, period: int = 9) -> dict:
        low_min = lows.rolling(window=period).min()
        high_max = highs.rolling(window=period).max()
        rsv = (closes - low_min) / (high_max - low_min).replace(0, np.nan) * 100
        k = rsv.ewm(com=2, adjust=False).mean()
        d = k.ewm(com=2, adjust=False).mean()
        j = 3 * k - 2 * d
        return {
            "k": round(float(k.iloc[-1]), 2) if pd.notna(k.iloc[-1]) else 50,
            "d": round(float(d.iloc[-1]), 2) if pd.notna(d.iloc[-1]) else 50,
            "j": round(float(j.iloc[-1]), 2) if pd.notna(j.iloc[-1]) else 50,
        }


indicators_service = IndicatorsService()
