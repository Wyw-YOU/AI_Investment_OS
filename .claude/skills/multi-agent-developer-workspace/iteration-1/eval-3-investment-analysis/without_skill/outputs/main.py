"""
Main entry point for the Multi-Agent Investment Analysis System.

Usage:
    python main.py AAPL
    python main.py TSLA --horizon long-term --risk-tolerance aggressive
    python main.py MSFT --config config.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from config import AppConfig
from state import InvestmentState
from utils import logger, setup_logger
from workflow import run_analysis


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Investment Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python main.py AAPL
  python main.py TSLA --horizon long-term --risk-tolerance aggressive
  python main.py MSFT --output results.json
        """,
    )
    parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker symbol to analyse (e.g. AAPL, TSLA)",
    )
    parser.add_argument(
        "--horizon",
        type=str,
        default="medium-term",
        choices=["short-term", "medium-term", "long-term"],
        help="Investment time horizon (default: medium-term)",
    )
    parser.add_argument(
        "--risk-tolerance",
        type=str,
        default="moderate",
        choices=["conservative", "moderate", "aggressive"],
        help="Investor risk tolerance (default: moderate)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the JSON report (default: prints to stdout)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a JSON config file (optional)",
    )
    return parser.parse_args()


def load_config(config_path: str | None) -> AppConfig:
    """Load configuration from file or environment."""
    if config_path:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Build from dict — simplified for brevity
        cfg = AppConfig.from_env()
        logger.info("Loaded config from %s", config_path)
        return cfg
    return AppConfig.from_env()


def format_report_summary(state: InvestmentState) -> str:
    """
    Format a human-readable summary of the final investment report.
    """
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append(f"  INVESTMENT ANALYSIS REPORT — {state.get('ticker', 'N/A')}")
    lines.append(f"  Generated: {state.get('completed_at', 'N/A')}")
    lines.append("=" * 70)

    report = state.get("report_output")
    if report and isinstance(report, dict):
        lines.append("")
        lines.append(f"  RECOMMENDATION : {report.get('recommendation', 'N/A').upper()}")
        lines.append(f"  Composite Score: {report.get('composite_score', 'N/A')}/100")
        lines.append(f"  Conviction     : {report.get('conviction_level', 'N/A')}")
        lines.append(f"  Time Horizon   : {report.get('time_horizon', 'N/A')}")
        lines.append("")

        bull = report.get("price_target_bull")
        base = report.get("price_target_base")
        bear = report.get("price_target_bear")
        if any(t is not None for t in [bull, base, bear]):
            lines.append("  PRICE TARGETS:")
            if bull:
                lines.append(f"    Bull Case : ${bull:.2f}")
            if base:
                lines.append(f"    Base Case : ${base:.2f}")
            if bear:
                lines.append(f"    Bear Case : ${bear:.2f}")
            lines.append("")

        if cats := report.get("key_catalysts"):
            lines.append("  KEY CATALYSTS:")
            for c in cats:
                lines.append(f"    - {c}")
            lines.append("")

        if risks := report.get("key_risks"):
            lines.append("  KEY RISKS:")
            for r in risks:
                lines.append(f"    - {r}")
            lines.append("")

        lines.append("  ACTIONABLE SUMMARY:")
        lines.append(f"    {report.get('actionable_summary', 'N/A')}")
        lines.append("")

        if scores := report.get("agent_scores"):
            lines.append("  AGENT SCORES:")
            for agent, score in scores.items():
                lines.append(f"    {agent:20s} : {score:.1f}/100")
    else:
        lines.append("")
        lines.append("  [No report generated — all agents may have failed.]")
        lines.append("")
        if errors := state.get("errors"):
            lines.append("  ERRORS:")
            for e in errors:
                lines.append(f"    - {e}")

    lines.append("")
    lines.append("=" * 70)

    # Agent status summary
    statuses = state.get("agent_statuses", {})
    lines.append("  AGENT EXECUTION STATUS:")
    for agent_name, status in statuses.items():
        st = status.get("state", "unknown")
        err = status.get("error")
        line = f"    {agent_name:20s} : {st}"
        if err:
            line += f"  ({err})"
        lines.append(line)
    lines.append("=" * 70)

    return "\n".join(lines)


def save_report(state: InvestmentState, output_path: str) -> None:
    """Save the full state as a JSON file."""
    # Convert state to a JSON-serializable dict
    def _default(obj: Any) -> Any:
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(dict(state), f, indent=2, default=_default, ensure_ascii=False)

    logger.info("Report saved to %s", path)


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    setup_logger("investment_system", args.log_level)

    # Build analysis request from CLI args
    analysis_request: dict[str, Any] = {
        "time_horizon": args.horizon,
        "risk_tolerance": args.risk_tolerance,
    }

    config = load_config(args.config)

    # Run the analysis
    final_state = run_analysis(
        ticker=args.ticker,
        analysis_request=analysis_request,
        config=config,
    )

    # Display summary
    print(format_report_summary(final_state))

    # Save to file if requested
    if args.output:
        save_report(final_state, args.output)

    # Exit with appropriate code
    status = final_state.get("overall_status", "unknown")
    if status == "completed":
        sys.exit(0)
    elif status == "failed":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
