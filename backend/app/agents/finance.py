"""FinanceAgent — fundamental analysis using financial data + LLM."""
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent, register_agent
from app.agents.state import InvestmentState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior financial analyst. Analyze the provided financial data "
    "and return a JSON object with: pe_ratio, pb_ratio, roe, revenue_growth, "
    "net_profit_growth, debt_ratio, verdict (undervalued/fairly_valued/overvalued), "
    "key_metrics (strengths list, weaknesses list)."
)


class FinanceAgent(BaseAgent):
    name = "finance"

    def __init__(self, llm=None):
        self.llm = llm

    def run(self, state: InvestmentState) -> Dict[str, Any]:
        stock = state.current_stock
        fin_data = state.financial_data

        if not fin_data or all(v == 0 for v in fin_data.values() if isinstance(v, (int, float))):
            return self._build_result(
                output={"verdict": "unknown", "pe_ratio": 0, "pb_ratio": 0, "roe": 0},
                confidence=0.1,
                evidence=["financial data is empty or all zeros"],
                reasoning="Insufficient financial data to perform analysis.",
            )

        if self.llm:
            return self._analyze_with_llm(stock, fin_data)
        return self._analyze_rule_based(stock, fin_data)

    def _analyze_with_llm(self, stock: str, fin_data: dict) -> dict:
        prompt = (
            f"Analyze stock {stock} with the following financial data:\n"
            f"{fin_data}\n\n"
            f"Return a JSON object with pe_ratio, pb_ratio, roe, revenue_growth, "
            f"net_profit_growth, debt_ratio, verdict, key_metrics."
        )
        llm_result = self.llm.generate_json(prompt, system_prompt=SYSTEM_PROMPT)
        if llm_result:
            confidence = self._calc_confidence(fin_data)
            evidence = self._extract_evidence(fin_data)
            result = self._build_result(
                output=llm_result,
                confidence=confidence,
                evidence=evidence,
                reasoning=f"LLM-based fundamental analysis for {stock}.",
            )
            self._log_run(
                type("_S", (), {"current_stock": stock})(),
                result,
            )
            return result
        return self._analyze_rule_based(stock, fin_data)

    def _analyze_rule_based(self, stock: str, fin_data: dict) -> dict:
        pe = fin_data.get("pe_ratio", 0)
        roe = fin_data.get("roe", 0)
        debt = fin_data.get("debt_ratio", 0)

        verdict = "fairly_valued"
        if pe > 0 and pe < 20 and roe > 0.15:
            verdict = "undervalued"
        elif pe > 50 or roe < 0.05:
            verdict = "overvalued"

        strengths = []
        weaknesses = []
        if roe > 0.15:
            strengths.append(f"High ROE: {roe:.1%}")
        if pe > 0 and pe < 25:
            strengths.append(f"Reasonable PE: {pe:.1f}")
        if debt > 0.6:
            weaknesses.append(f"High debt ratio: {debt:.1%}")
        if roe < 0.05:
            weaknesses.append(f"Low ROE: {roe:.1%}")

        output = {
            "pe_ratio": pe,
            "pb_ratio": fin_data.get("pb_ratio", 0),
            "roe": roe,
            "revenue_growth": fin_data.get("revenue_growth", 0),
            "net_profit_growth": fin_data.get("net_profit_growth", 0),
            "debt_ratio": debt,
            "verdict": verdict,
            "key_metrics": {"strengths": strengths, "weaknesses": weaknesses},
        }

        confidence = self._calc_confidence(fin_data)
        evidence = self._extract_evidence(fin_data)
        result = self._build_result(
            output=output,
            confidence=confidence,
            evidence=evidence,
            reasoning=f"Rule-based fundamental analysis: verdict={verdict}, "
                      f"PE={pe:.1f}, ROE={roe:.1%}, debt={debt:.1%}.",
        )
        return result

    def _calc_confidence(self, fin_data: dict) -> float:
        available = sum(1 for v in fin_data.values() if v and v != 0)
        total = max(len(fin_data), 1)
        return round(available / total, 2)

    def _extract_evidence(self, fin_data: dict) -> list[str]:
        evidence = []
        if fin_data.get("pe_ratio"):
            evidence.append(f"PE ratio: {fin_data['pe_ratio']:.1f}")
        if fin_data.get("roe"):
            evidence.append(f"ROE: {fin_data['roe']:.1%}")
        if fin_data.get("revenue_growth"):
            evidence.append(f"Revenue growth: {fin_data['revenue_growth']:.1%}")
        return evidence if evidence else ["limited financial data available"]


register_agent(FinanceAgent())
