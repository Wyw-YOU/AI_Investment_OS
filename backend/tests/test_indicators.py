"""Tests for technical indicators service."""
from app.services.indicators import (
    calculate_macd,
    calculate_rsi,
    calculate_kdj,
    calculate_bollinger,
    calculate_ma,
    calculate_all_indicators,
)


SAMPLE_PRICES = [
    100.0, 101.5, 99.8, 102.3, 103.1, 101.7, 104.2, 105.0, 103.8, 106.1,
    107.5, 105.9, 108.3, 109.0, 107.2, 110.1, 111.5, 109.8, 112.0, 113.3,
    111.7, 114.5, 115.2, 113.8, 116.0, 117.3, 115.9, 118.2, 119.0, 117.5,
    120.1, 121.3, 119.8, 122.5, 123.0, 121.7, 124.3, 125.0, 123.5, 126.0,
]


class TestMACD:
    def test_returns_three_keys(self):
        result = calculate_macd(SAMPLE_PRICES)
        assert "macd_line" in result
        assert "signal_line" in result
        assert "histogram" in result

    def test_returns_floats(self):
        result = calculate_macd(SAMPLE_PRICES)
        for val in result.values():
            assert isinstance(val, float)

    def test_insufficient_data(self):
        result = calculate_macd([1.0, 2.0, 3.0])
        assert result["macd_line"] == 0.0


class TestRSI:
    def test_rsi_range(self):
        result = calculate_rsi(SAMPLE_PRICES)
        assert 0 <= result["value"] <= 100

    def test_overbought_signal(self):
        rising = [float(i) for i in range(1, 50)]
        result = calculate_rsi(rising)
        assert result["signal"] == "overbought"

    def test_oversold_signal(self):
        falling = [float(50 - i) for i in range(50)]
        result = calculate_rsi(falling)
        assert result["signal"] == "oversold"

    def test_insufficient_data(self):
        result = calculate_rsi([1.0, 2.0])
        assert result["value"] == 50.0


class TestKDJ:
    def test_returns_k_d_j(self):
        highs = [p * 1.01 for p in SAMPLE_PRICES]
        lows = [p * 0.99 for p in SAMPLE_PRICES]
        result = calculate_kdj(highs, lows, SAMPLE_PRICES)
        assert "k" in result and "d" in result and "j" in result

    def test_insufficient_data(self):
        result = calculate_kdj([1.0], [1.0], [1.0])
        assert result["k"] == 50.0


class TestBollinger:
    def test_bands_ordered(self):
        result = calculate_bollinger(SAMPLE_PRICES)
        assert result["upper"] > result["middle"] > result["lower"]

    def test_signal_detection(self):
        rising = [float(i * 2) for i in range(1, 30)]
        result = calculate_bollinger(rising)
        assert result["signal"] in ("overbought", "neutral")


class TestMA:
    def test_default_periods(self):
        result = calculate_ma(SAMPLE_PRICES)
        assert "ma5" in result
        assert "ma20" in result

    def test_custom_periods(self):
        result = calculate_ma(SAMPLE_PRICES, periods=[3, 7])
        assert "ma3" in result
        assert "ma7" in result


class TestCalculateAll:
    def test_all_indicators_present(self):
        result = calculate_all_indicators(SAMPLE_PRICES)
        assert "macd" in result
        assert "rsi" in result
        assert "kdj" in result
        assert "bollinger" in result
        assert "ma" in result
