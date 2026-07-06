"""
Investment Analysis System - Main Entry Point

Usage examples and demo runner for the multi-agent investment
analysis pipeline.

Examples
--------
Run with real LLM calls (requires OPENAI_API_KEY):

    $ python main.py

Run demo mode (no LLM calls, uses mock data):

    $ python main.py --demo

Run analysis for a specific stock:

    $ python main.py --stock AAPL --name "Apple Inc." --query "Should I buy Apple stock?"

Run with custom data files:

    $ python main.py --stock TSLA --news-file news.json --financial-file financials.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the investment analysis system."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Sample / Mock Data
# ---------------------------------------------------------------------------

def get_sample_market_data(stock_code: str = "AAPL") -> Dict[str, Any]:
    """Generate realistic sample market data for demo mode."""
    return {
        "symbol": stock_code,
        "company_name": "Apple Inc.",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "current_price": 175.50,
        "previous_close": 173.25,
        "day_change": 2.25,
        "day_change_pct": 1.30,
        "market_cap": "2.8T",
        "volume": 45_200_000,
        "avg_volume_20d": 38_000_000,
        "52w_high": 199.62,
        "52w_low": 124.17,
        "pe_ratio": 28.6,
        "dividend_yield": 0.55,
    }


def get_sample_news_data() -> List[Dict[str, Any]]:
    """Generate realistic sample news articles for demo mode."""
    return [
        {
            "title": "Apple Reports Record Q4 Revenue of $89.5B, Beating Estimates",
            "source": "Reuters",
            "published_at": "2024-01-15",
            "sentiment": "positive",
            "snippet": (
                "Apple Inc. reported quarterly revenue of $89.5 billion, "
                "beating Wall Street estimates of $88.1 billion. iPhone revenue "
                "came in at $43.8 billion, driven by strong demand for iPhone 15."
            ),
        },
        {
            "title": "iPhone 15 Sales Exceed Expectations in China Market",
            "source": "Bloomberg",
            "published_at": "2024-01-14",
            "sentiment": "positive",
            "snippet": (
                "Apple's iPhone 15 lineup saw unexpectedly strong sales in China "
                "during the holiday quarter, with unit sales up 12% year-over-year "
                "despite increased competition from Huawei."
            ),
        },
        {
            "title": "Apple Vision Pro Launch Set for February 2, Priced at $3,499",
            "source": "TechCrunch",
            "published_at": "2024-01-13",
            "sentiment": "neutral",
            "snippet": (
                "Apple announced that Vision Pro will be available starting February 2 "
                "at $3,499. Analysts are watching closely to gauge consumer adoption "
                "at this premium price point."
            ),
        },
        {
            "title": "EU Regulators May Force Apple to Open NFC to Competitors",
            "source": "Financial Times",
            "published_at": "2024-01-12",
            "sentiment": "negative",
            "snippet": (
                "European regulators are finalizing rules that would require Apple "
                "to open its NFC chip to rival payment services, potentially impacting "
                "Apple Pay's competitive advantage in Europe."
            ),
        },
        {
            "title": "Services Revenue Hits All-Time High of $22.3B",
            "source": "CNBC",
            "published_at": "2024-01-15",
            "sentiment": "positive",
            "snippet": (
                "Apple's Services segment, which includes App Store, Apple Music, "
                "iCloud, and Apple TV+, reported record revenue of $22.3 billion, "
                "up 11% year-over-year."
            ),
        },
    ]


def get_sample_financial_data() -> Dict[str, Any]:
    """Generate realistic sample financial data for demo mode."""
    return {
        "income_statement": {
            "revenue_ttm": 383_300_000_000,
            "gross_profit": 169_100_000_000,
            "operating_income": 114_300_000_000,
            "net_income": 97_000_000_000,
            "eps_ttm": 6.13,
        },
        "balance_sheet": {
            "total_assets": 352_760_000_000,
            "total_liabilities": 290_440_000_000,
            "shareholders_equity": 62_320_000_000,
            "cash_and_equivalents": 29_970_000_000,
            "long_term_debt": 95_280_000_000,
        },
        "key_ratios": {
            "roe": 1.72,
            "roa": 0.289,
            "gross_margin": 0.441,
            "net_margin": 0.253,
            "debt_to_equity": 1.53,
            "current_ratio": 1.27,
            "pe_ratio": 28.6,
            "pb_ratio": 43.2,
            "peg_ratio": 2.14,
        },
        "growth": {
            "revenue_growth_yoy": 0.027,
            "earnings_growth_yoy": 0.051,
            "revenue_growth_3yr_cagr": 0.082,
        },
    }


def get_sample_price_history(days: int = 30) -> List[Dict[str, Any]]:
    """Generate realistic OHLCV price history for demo mode."""
    import random

    random.seed(42)  # Reproducible
    prices: List[Dict[str, Any]] = []
    base_price = 165.0

    for i in range(days):
        day_change = random.gauss(0.3, 1.5)  # Slight upward bias
        base_price += day_change
        base_price = max(base_price, 150.0)

        high = base_price + abs(random.gauss(0, 1.0))
        low = base_price - abs(random.gauss(0, 1.0))
        open_price = base_price + random.gauss(0, 0.5)
        volume = int(random.gauss(38_000_000, 8_000_000))

        date_str = f"2024-01-{max(1, 30 - i):02d}"
        prices.append({
            "date": date_str,
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(base_price, 2),
            "volume": max(volume, 10_000_000),
        })

    # Reverse so oldest is first
    prices.reverse()
    return prices


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------

def format_analysis_result(result: dict) -> str:
    """Format the final workflow result into a readable report."""
    lines: List[str] = []

    lines.append("=" * 70)
    lines.append("  INVESTMENT ANALYSIS REPORT")
    lines.append("=" * 70)

    stock_code = result.get("stock_code", "N/A")
    stock_name = result.get("stock_name", stock_code)
    lines.append(f"  Stock: {stock_name} ({stock_code})")
    lines.append(f"  Task ID: {result.get('task_id', 'N/A')}")
    lines.append(f"  Phase: {result.get('phase', 'N/A')}")
    lines.append(f"  Timestamp: {result.get('updated_at', 'N/A')}")
    lines.append("")

    # --- Final Report ---
    final_report = result.get("final_report", {})
    if final_report and isinstance(final_report, dict):
        rec = final_report.get("recommendation", "N/A").upper()
        conf = final_report.get("confidence", 0)
        summary = final_report.get("executive_summary", "N/A")

        lines.append("-" * 70)
        lines.append(f"  RECOMMENDATION: {rec}  |  CONFIDENCE: {conf:.0%}")
        lines.append("-" * 70)
        lines.append("")
        lines.append("  EXECUTIVE SUMMARY")
        lines.append(f"  {summary}")
        lines.append("")

        # Price target
        pt = final_report.get("price_target", {})
        if pt:
            target = pt.get("target", "N/A")
            horizon = pt.get("time_horizon", "N/A")
            upside = pt.get("upside")
            upside_str = f"{upside:+.1%}" if upside is not None else "N/A"
            lines.append(f"  PRICE TARGET: ${target}  |  Horizon: {horizon}  |  Upside: {upside_str}")
            lines.append("")

        # Key findings
        findings = final_report.get("key_findings", {})
        if findings:
            lines.append("  KEY FINDINGS")
            for area, finding in findings.items():
                lines.append(f"    [{area.upper()}] {finding}")
            lines.append("")

        # Risk-reward
        rr = final_report.get("risk_reward", {})
        if rr:
            lines.append(
                f"  RISK-REWARD: Score={rr.get('risk_score', 'N/A')}  |  "
                f"Reward={rr.get('reward_potential', 'N/A')}  |  "
                f"R/R Ratio={rr.get('risk_reward_ratio', 'N/A')}"
            )
            lines.append("")

        # Action items
        actions = final_report.get("action_items", [])
        if actions:
            lines.append("  ACTION ITEMS")
            for i, action in enumerate(actions, 1):
                lines.append(f"    {i}. {action}")
            lines.append("")

        # Disclaimer
        disclaimer = final_report.get("disclaimer", "")
        if disclaimer:
            lines.append(f"  DISCLAIMER: {disclaimer}")
            lines.append("")

    # --- Agent Outputs Summary ---
    agent_outputs = result.get("agent_outputs", {})
    if agent_outputs:
        lines.append("-" * 70)
        lines.append("  AGENT PERFORMANCE SUMMARY")
        lines.append("-" * 70)
        for name, output in agent_outputs.items():
            if isinstance(output, dict):
                status = output.get("status", "unknown")
                conf = output.get("confidence", 0)
                elapsed = output.get("elapsed_seconds")
                elapsed_str = f"  ({elapsed:.1f}s)" if elapsed else ""
                lines.append(f"    {name:20s} | Status: {status:8s} | Confidence: {conf:.0%}{elapsed_str}")
        lines.append("")

    # --- Errors ---
    errors = result.get("errors", [])
    if errors:
        lines.append("-" * 70)
        lines.append("  ERRORS")
        lines.append("-" * 70)
        for err in errors:
            lines.append(f"    - {err}")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo runner (no LLM calls)
# ---------------------------------------------------------------------------

def run_demo() -> dict:
    """
    Run the workflow with sample data in mock/demo mode.

    Uses mock LLM responses to demonstrate the full pipeline without
    requiring an API key.
    """
    from unittest.mock import MagicMock, patch

    # Import workflow components
    from workflow import build_investment_workflow, WorkflowState
    from models import create_initial_state

    # Create initial state with sample data
    initial_state = create_initial_state(
        task_id="demo_aapl_001",
        stock_code="AAPL",
        stock_name="Apple Inc.",
        query="Comprehensive investment analysis for potential entry at current levels",
        user_id="demo_user",
        market_data=get_sample_market_data("AAPL"),
        news_data=get_sample_news_data(),
        financial_data=get_sample_financial_data(),
        price_history=get_sample_price_history(30),
        time_horizon="12 months",
        risk_tolerance="moderate",
    )

    # Build the workflow
    workflow = build_investment_workflow()

    # Mock LLM responses for each agent
    mock_responses = {
        "news_agent": json.dumps({
            "sentiment": "bullish",
            "sentiment_score": 0.78,
            "events": [
                {
                    "title": "Apple Reports Record Q4 Revenue of $89.5B",
                    "impact": "positive",
                    "affected_stocks": ["AAPL"],
                    "summary": "Record quarterly revenue driven by strong iPhone and Services growth",
                    "source": "Reuters",
                },
                {
                    "title": "EU Regulators May Force NFC Opening",
                    "impact": "negative",
                    "affected_stocks": ["AAPL"],
                    "summary": "Potential regulatory headwind for Apple Pay in Europe",
                    "source": "Financial Times",
                },
            ],
            "risk_factors": [
                "EU regulatory pressure on Apple Pay",
                "China market competition from Huawei",
                "Vision Pro adoption uncertainty at $3,499 price",
            ],
            "key_quotes": [
                "Services revenue hit all-time high of $22.3 billion, up 11% year-over-year",
            ],
            "citations": ["Reuters", "Bloomberg", "Financial Times", "TechCrunch", "CNBC"],
            "confidence": 0.80,
        }),
        "financial_agent": json.dumps({
            "profitability": {
                "roe": 1.72,
                "roa": 0.289,
                "gross_margin": 0.441,
                "net_margin": 0.253,
            },
            "growth": {
                "revenue_growth": 0.027,
                "earnings_growth": 0.051,
                "growth_trend": "stable",
            },
            "valuation": {
                "pe_ratio": 28.6,
                "pb_ratio": 43.2,
                "peg_ratio": 2.14,
                "assessment": "fairly_valued",
            },
            "health": {
                "debt_to_equity": 1.53,
                "current_ratio": 1.27,
                "health_score": 72,
            },
            "thesis": (
                "Apple demonstrates strong profitability with best-in-class margins. "
                "Services growth provides recurring revenue stability. However, "
                "hardware growth has slowed and the stock trades at a premium valuation. "
                "The investment case rests on continued Services expansion and new product categories."
            ),
            "citations": ["10-K Filing 2023", "Q4 2023 Earnings Release", "Apple Investor Relations"],
            "confidence": 0.82,
        }),
        "technical_agent": json.dumps({
            "trend": {
                "short_term": "bullish",
                "medium_term": "bullish",
                "long_term": "neutral",
            },
            "levels": {
                "support": [170.0, 165.0, 160.0],
                "resistance": [180.0, 185.0, 190.0],
            },
            "indicators": {
                "rsi": 58,
                "rsi_signal": "neutral",
                "macd": "bullish_crossover",
                "macd_histogram": 0.8,
            },
            "volume": {
                "trend": "increasing",
                "relative_volume": 1.19,
                "analysis": "Above-average volume confirms the recent upward price movement",
            },
            "patterns": ["ascending_channel"],
            "signals": {
                "action": "buy",
                "entry_price": 175.50,
                "stop_loss": 168.00,
                "target_price": 188.00,
                "risk_reward_ratio": 1.67,
            },
            "citations": ["OHLCV price data", "Technical indicators calculated from price data"],
            "confidence": 0.72,
        }),
        "risk_agent": json.dumps({
            "overall_risk": "medium",
            "risk_score": 42,
            "risk_factors": {
                "market_risk": {
                    "level": "medium",
                    "factors": ["Market near all-time highs", "Interest rate uncertainty"],
                },
                "company_risk": {
                    "level": "low",
                    "factors": ["Dominant ecosystem", "Strong brand moat", "Massive cash generation"],
                },
                "valuation_risk": {
                    "level": "medium",
                    "factors": ["P/E of 28.6 above 5-year average", "PEG of 2.14 suggests premium"],
                },
                "liquidity_risk": {
                    "level": "low",
                    "factors": ["Extremely high daily volume", "$2.8T market cap"],
                },
            },
            "worst_case": {
                "scenario": "Global recession + China demand collapse + regulatory crackdown",
                "potential_loss": -0.30,
                "probability": 0.08,
            },
            "mitigation": [
                "Set stop loss at $168 (-4.3% from current)",
                "Limit initial position to 5% of portfolio",
                "Scale in over 2-3 tranches",
                "Monitor China iPhone sales data quarterly",
            ],
            "position_sizing": {
                "conservative": 0.03,
                "moderate": 0.05,
                "aggressive": 0.08,
            },
            "citations": ["Agent synthesis", "Historical volatility data"],
            "confidence": 0.75,
        }),
        "report_agent": json.dumps({
            "executive_summary": (
                "Apple presents a solid investment opportunity with strong fundamentals, "
                "bullish near-term technicals, and manageable risk profile. The stock "
                "is fairly valued relative to its growth trajectory, with Services "
                "revenue providing a durable competitive advantage. We recommend BUYING "
                "with moderate conviction for a 12-month horizon."
            ),
            "recommendation": "buy",
            "confidence": 0.77,
            "price_target": {
                "target": 188.00,
                "time_horizon": "12 months",
                "upside": 0.071,
            },
            "key_findings": {
                "sentiment": "Bullish sentiment (0.78) driven by record Q4 revenue and strong Services growth, partially offset by EU regulatory headwinds",
                "fundamentals": "Best-in-class profitability with 44% gross margins and growing Services revenue; fairly valued at P/E 28.6",
                "technicals": "Short-term bullish momentum with MACD crossover and above-average volume; support at $170",
                "risks": "Medium overall risk (42/100); main concerns are premium valuation and regulatory uncertainty in Europe",
            },
            "risk_reward": {
                "risk_score": 42,
                "reward_potential": 0.071,
                "risk_reward_ratio": 1.67,
            },
            "action_items": [
                "Consider entry at current price of $175.50 with a 5% portfolio allocation",
                "Set stop loss at $168.00 (-4.3%) to limit downside risk",
                "Take initial profit at $185.00 and trail stop to $178.00",
                "Monitor Q1 2024 earnings in late April for Services growth trajectory",
                "Watch for EU NFC regulation outcome in Q2 2024",
            ],
            "sources": [
                "News Analysis (5 articles from Reuters, Bloomberg, FT, TechCrunch, CNBC)",
                "Financial Analysis (10-K Filing, Q4 Earnings Release)",
                "Technical Analysis (30-day OHLCV price data)",
                "Risk Model (multi-factor risk assessment)",
            ],
            "disclaimer": (
                "This is AI-generated analysis, not financial advice. Past performance "
                "does not guarantee future results. Always conduct your own due diligence "
                "before making investment decisions."
            ),
        }),
    }

    # Patch the LLM calls at the OpenAI client level
    mock_choice = MagicMock()
    mock_choice.message.content = ""  # Will be set per agent

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    # Track which agent is calling to return the right mock response
    call_count = {"value": 0}
    agent_order = ["news_agent", "financial_agent", "technical_agent",
                   "risk_agent", "report_agent"]

    def mock_create(**kwargs):
        # Determine agent from system prompt
        system_msg = kwargs.get("messages", [{}])[0].get("content", "")
        for agent_name, response in mock_responses.items():
            if agent_name.replace("_", " ") in system_msg.lower() or agent_name in system_msg:
                mock_choice.message.content = response
                return mock_response

        # Fallback: use sequential order
        idx = min(call_count["value"], len(agent_order) - 1)
        call_count["value"] += 1
        mock_choice.message.content = mock_responses[agent_order[idx]]
        return mock_response

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        mock_openai_class.return_value = mock_client

        # Run the workflow
        try:
            result = workflow.invoke(initial_state)
        except Exception as e:
            logging.error("Workflow invocation failed: %s", e, exc_info=True)
            result = {**initial_state, "phase": "failed", "errors": [str(e)]}

    return result


# ---------------------------------------------------------------------------
# Live runner (real LLM calls)
# ---------------------------------------------------------------------------

def run_live(
    stock_code: str,
    stock_name: str = "",
    query: str = "",
    news_data: Optional[List] = None,
    financial_data: Optional[Dict] = None,
    price_history: Optional[List] = None,
    market_data: Optional[Dict] = None,
    time_horizon: str = "12 months",
    risk_tolerance: str = "moderate",
) -> dict:
    """
    Run the full investment analysis with real LLM calls.

    Requires OPENAI_API_KEY to be set (or pass api_key to agents).
    """
    from workflow import run_investment_analysis

    return run_investment_analysis(
        stock_code=stock_code,
        stock_name=stock_name,
        query=query,
        market_data=market_data or get_sample_market_data(stock_code),
        news_data=news_data or get_sample_news_data(),
        financial_data=financial_data or get_sample_financial_data(),
        price_history=price_history or get_sample_price_history(30),
        time_horizon=time_horizon,
        risk_tolerance=risk_tolerance,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AI Investment Analysis System - Multi-Agent Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run in demo mode with mock data (no LLM calls required)",
    )
    parser.add_argument(
        "--stock", type=str, default="AAPL",
        help="Stock ticker symbol (default: AAPL)",
    )
    parser.add_argument(
        "--name", type=str, default="Apple Inc.",
        help="Stock company name (default: Apple Inc.)",
    )
    parser.add_argument(
        "--query", type=str, default="Comprehensive investment analysis",
        help="Analysis query from the user",
    )
    parser.add_argument(
        "--time-horizon", type=str, default="12 months",
        help="Investment time horizon (default: 12 months)",
    )
    parser.add_argument(
        "--risk-tolerance", type=str, default="moderate",
        choices=["conservative", "moderate", "aggressive"],
        help="User risk tolerance (default: moderate)",
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Path to save the JSON result file",
    )

    args = parser.parse_args()
    setup_logging(args.log_level)

    logger = logging.getLogger(__name__)

    if args.demo:
        logger.info("Running in DEMO mode (mock LLM responses)")
        result = run_demo()
    else:
        logger.info("Running in LIVE mode (real LLM calls)")
        result = run_live(
            stock_code=args.stock,
            stock_name=args.name,
            query=args.query,
            time_horizon=args.time_horizon,
            risk_tolerance=args.risk_tolerance,
        )

    # Print formatted report
    report = format_analysis_result(result)
    print(report)

    # Save result if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str, ensure_ascii=False)
        logger.info("Result saved to %s", output_path)

    return result


if __name__ == "__main__":
    main()
