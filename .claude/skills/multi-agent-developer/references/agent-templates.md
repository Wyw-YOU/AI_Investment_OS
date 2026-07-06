# Agent Templates Reference

Complete implementation templates for building multi-agent systems.

---

## Table of Contents

1. [BaseAgent Framework](#1-baseagent-framework)
2. [LLM-Powered Agent Template](#2-llm-powered-agent-template)
3. [Specialized Agent Examples](#3-specialized-agent-examples)
   - News Agent
   - Financial Agent
   - Technical Agent
   - Risk Agent
   - Report Agent
4. [Agent with Tool Usage](#4-agent-with-tool-usage)
5. [Agent with Memory](#5-agent-with-memory)
6. [Testing Agents](#6-testing-agents)

---

## 1. BaseAgent Framework

### Core BaseAgent Class

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, validator
from typing import Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AgentOutput(BaseModel):
    """Standard output format for all agents."""
    agent_name: str
    result: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[str] = []
    metadata: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v

    @validator('citations')
    def validate_citations(cls, v):
        if not v:
            logger.warning("No citations provided - results may not be verifiable")
        return v

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.

    All agents must implement:
    - name: str - Agent identifier
    - description: str - What the agent does
    - run(state: dict) -> AgentOutput - Main execution method
    """

    name: str
    description: str

    def __init__(self):
        self.logger = logging.getLogger(f"agent.{self.name}")

    @abstractmethod
    def run(self, state: dict) -> AgentOutput:
        """
        Execute agent logic and return structured output.

        Args:
            state: Current workflow state containing all context

        Returns:
            AgentOutput with results, confidence score, and citations

        Raises:
            AgentExecutionError: If agent fails to execute
        """
        pass

    def build_prompt(self, state: dict) -> str:
        """
        Construct prompt from current state.

        Override this method for custom prompt engineering.
        Default implementation provides a basic structure.
        """
        return f"""
[ROLE]
You are {self.name}: {self.description}

[CONTEXT]
{self._format_context(state)}

[TASK]
{self._get_task_description()}

[OUTPUT FORMAT]
{self._get_output_format()}

[CONSTRAINTS]
{self._get_constraints()}
"""

    def parse_response(self, response: str) -> dict:
        """
        Parse LLM response into structured output.

        Override this method for custom parsing logic.
        Default implementation attempts JSON parsing.
        """
        import json

        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Return raw text wrapped in dict
                return {"raw_output": response, "parsed": False}

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON: {e}")
            return {"raw_output": response, "parse_error": str(e)}

    def _format_context(self, state: dict) -> str:
        """Format state context for prompt injection."""
        context_parts = []
        for key, value in state.items():
            if key not in ['agent_outputs', 'final_result']:
                context_parts.append(f"{key}: {value}")
        return "\n".join(context_parts) if context_parts else "No additional context"

    def _get_task_description(self) -> str:
        """Override to provide specific task description."""
        return f"Perform {self.name} analysis"

    def _get_output_format(self) -> str:
        """Override to specify expected output format."""
        return '{"result": {}, "confidence": 0.0}'

    def _get_constraints(self) -> str:
        """Override to specify constraints."""
        return "- Be accurate and cite sources\n- Provide confidence score"

    def _create_output(
        self,
        result: dict,
        confidence: float,
        citations: list[str] = None,
        metadata: dict = None
    ) -> AgentOutput:
        """Helper to create standardized output."""
        return AgentOutput(
            agent_name=self.name,
            result=result,
            confidence=confidence,
            citations=citations or [],
            metadata=metadata or {}
        )
```

### Agent Error Types

```python
class AgentExecutionError(Exception):
    """Raised when an agent fails to execute properly."""
    def __init__(self, agent_name: str, message: str, original_error: Exception = None):
        self.agent_name = agent_name
        self.original_error = original_error
        super().__init__(f"Agent '{agent_name}' execution failed: {message}")

class AgentTimeoutError(AgentExecutionError):
    """Raised when an agent exceeds execution time limit."""
    pass

class AgentValidationError(AgentExecutionError):
    """Raised when agent output fails validation."""
    pass
```

---

## 2. LLM-Powered Agent Template

Template for agents that use LLM for analysis:

```python
from typing import Optional
import openai  # or anthropic, etc.

class LLMAgent(BaseAgent):
    """
    Base class for LLM-powered agents.

    Provides:
    - LLM client initialization
    - Prompt construction
    - Response parsing
    - Error handling
    - Token counting
    """

    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        api_key: Optional[str] = None
    ):
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = openai.OpenAI(api_key=api_key)

    def run(self, state: dict) -> AgentOutput:
        """Execute LLM-powered analysis."""
        try:
            # Build prompt
            prompt = self.build_prompt(state)

            # Call LLM
            response = self._call_llm(prompt)

            # Parse response
            parsed_result = self.parse_response(response)

            # Validate and create output
            confidence = self._calculate_confidence(parsed_result, state)
            citations = self._extract_citations(parsed_result, state)

            return self._create_output(
                result=parsed_result,
                confidence=confidence,
                citations=citations,
                metadata={
                    "model": self.model,
                    "prompt_tokens": self._count_tokens(prompt),
                    "response_tokens": self._count_tokens(response)
                }
            )

        except Exception as e:
            self.logger.error(f"LLM execution failed: {e}")
            raise AgentExecutionError(self.name, str(e), e)

    def _call_llm(self, prompt: str) -> str:
        """Call LLM API with retry logic."""
        import time

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    def _get_system_prompt(self) -> str:
        """Override to provide system-level instructions."""
        return f"You are {self.name}, {self.description}. Provide accurate, well-sourced analysis."

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """
        Calculate confidence score based on result quality.

        Override for custom confidence calculation logic.
        """
        # Default: use LLM-provided confidence or calculate from result completeness
        if "confidence" in result:
            return float(result["confidence"])

        # Calculate based on result completeness
        expected_keys = self._get_expected_output_keys()
        if expected_keys:
            present_keys = sum(1 for k in expected_keys if k in result)
            return present_keys / len(expected_keys)

        return 0.5  # Default moderate confidence

    def _extract_citations(self, result: dict, state: dict) -> list[str]:
        """
        Extract citations/sources from result.

        Override for custom citation extraction.
        """
        citations = []

        # Extract from result if present
        if "citations" in result:
            citations.extend(result["citations"])
        if "sources" in result:
            citations.extend(result["sources"])

        # Add state sources
        if "data_sources" in state:
            citations.extend(state["data_sources"])

        return list(set(citations))  # Deduplicate

    def _get_expected_output_keys(self) -> list[str]:
        """Override to specify expected keys in output."""
        return []

    def _count_tokens(self, text: str) -> int:
        """Estimate token count (simplified)."""
        return len(text.split()) * 1.3  # Rough estimate
```

---

## 3. Specialized Agent Examples

### News Agent

```python
class NewsAgent(LLMAgent):
    """Analyzes news sentiment and extracts key events."""

    name = "news_agent"
    description = "Expert in news analysis, sentiment detection, and event extraction"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _get_task_description(self) -> str:
        return """
Analyze the provided news data and extract:
1. Overall sentiment (bullish/bearish/neutral)
2. Key events and their impact
3. Affected stocks and sectors
4. Risk factors identified
5. Timeline of events
"""

    def _get_output_format(self) -> str:
        return """{
    "sentiment": "bullish|bearish|neutral",
    "sentiment_score": 0.0-1.0,
    "events": [
        {
            "title": "Event title",
            "impact": "positive|negative|neutral",
            "affected_stocks": ["AAPL", "MSFT"],
            "summary": "Brief summary"
        }
    ],
    "risk_factors": ["risk1", "risk2"],
    "key_quotes": ["quote1", "quote2"],
    "citations": ["source1", "source2"]
}"""

    def _get_expected_output_keys(self) -> list[str]:
        return ["sentiment", "sentiment_score", "events", "risk_factors"]
```

### Financial Agent

```python
class FinancialAgent(LLMAgent):
    """Analyzes financial statements and fundamentals."""

    name = "financial_agent"
    description = "Expert in financial analysis, valuation, and fundamental metrics"

    def _get_task_description(self) -> str:
        return """
Analyze the financial data and provide:
1. Profitability analysis (ROE, ROA, margins)
2. Growth analysis (revenue, earnings growth)
3. Valuation assessment (PE, PB, DCF if applicable)
4. Balance sheet health (debt, liquidity)
5. Competitive position
6. Investment thesis
"""

    def _get_output_format(self) -> str:
        return """{
    "profitability": {
        "roe": 0.15,
        "roa": 0.08,
        "gross_margin": 0.45,
        "net_margin": 0.12
    },
    "growth": {
        "revenue_growth": 0.20,
        "earnings_growth": 0.25,
        "growth_trend": "accelerating|stable|decelerating"
    },
    "valuation": {
        "pe_ratio": 25.5,
        "pb_ratio": 3.2,
        "peg_ratio": 1.2,
        "assessment": "undervalued|fairly_valued|overvalued"
    },
    "health": {
        "debt_to_equity": 0.5,
        "current_ratio": 2.1,
        "health_score": 85
    },
    "thesis": "Investment thesis summary",
    "confidence": 0.85,
    "citations": ["10-K filing", "earnings call"]
}"""

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """Higher confidence when more financial data is available."""
        base_confidence = super()._calculate_confidence(result, state)

        # Boost confidence if comprehensive data available
        financial_data = state.get("financials", {})
        data_completeness = len(financial_data) / 10  # Expected 10 data points

        return min(base_confidence * (0.7 + 0.3 * data_completeness), 1.0)
```

### Technical Agent

```python
class TechnicalAgent(LLMAgent):
    """Analyzes technical indicators and price patterns."""

    name = "technical_agent"
    description = "Expert in technical analysis, chart patterns, and trading signals"

    def _get_task_description(self) -> str:
        return """
Analyze the technical data and provide:
1. Trend analysis (short, medium, long-term)
2. Support and resistance levels
3. Momentum indicators (RSI, MACD, Stochastic)
4. Volume analysis
5. Chart patterns identified
6. Trading signals and recommendations
"""

    def _get_output_format(self) -> str:
        return """{
    "trend": {
        "short_term": "bullish|bearish|neutral",
        "medium_term": "bullish|bearish|neutral",
        "long_term": "bullish|bearish|neutral"
    },
    "levels": {
        "support": [150.0, 145.0, 140.0],
        "resistance": [160.0, 165.0, 170.0]
    },
    "indicators": {
        "rsi": 65,
        "rsi_signal": "overbought|oversold|neutral",
        "macd": "bullish_crossover|bearish_crossover|neutral",
        "macd_histogram": 0.5
    },
    "volume": {
        "trend": "increasing|decreasing|stable",
        "relative_volume": 1.2,
        "analysis": "Volume supports price movement"
    },
    "patterns": ["ascending_triangle", "golden_cross"],
    "signals": {
        "action": "buy|sell|hold",
        "entry_price": 155.0,
        "stop_loss": 148.0,
        "target_price": 170.0,
        "risk_reward_ratio": 2.1
    },
    "confidence": 0.78,
    "citations": ["price data", "volume data"]
}"""
```

### Risk Agent

```python
class RiskAgent(LLMAgent):
    """Assesses investment risks and provides risk scoring."""

    name = "risk_agent"
    description = "Expert in risk assessment, risk management, and portfolio risk"

    def _get_task_description(self) -> str:
        return """
Assess the investment risks and provide:
1. Overall risk level (low/medium/high/very_high)
2. Risk factors categorized by type
3. Risk score (0-100, higher = riskier)
4. Risk mitigation suggestions
5. Worst-case scenario analysis
6. Position sizing recommendation
"""

    def _get_output_format(self) -> str:
        return """{
    "overall_risk": "low|medium|high|very_high",
    "risk_score": 45,
    "risk_factors": {
        "market_risk": {
            "level": "medium",
            "factors": ["market volatility", "sector rotation"]
        },
        "company_risk": {
            "level": "low",
            "factors": ["strong balance sheet", "diversified revenue"]
        },
        "valuation_risk": {
            "level": "high",
            "factors": ["high PE ratio", "priced for perfection"]
        },
        "liquidity_risk": {
            "level": "low",
            "factors": ["high trading volume", "large market cap"]
        }
    },
    "worst_case": {
        "scenario": "Market correction + earnings miss",
        "potential_loss": -0.25,
        "probability": 0.15
    },
    "mitigation": [
        "Set stop loss at 10% below entry",
        "Position size limited to 5% of portfolio"
    ],
    "position_sizing": {
        "conservative": 0.03,
        "moderate": 0.05,
        "aggressive": 0.08
    },
    "confidence": 0.82,
    "citations": ["risk model", "historical data"]
}"""

    def run(self, state: dict) -> AgentOutput:
        """Enhanced run with risk aggregation from other agents."""
        # Gather risk signals from other agent outputs
        agent_outputs = state.get("agent_outputs", {})
        risk_signals = self._aggregate_risk_signals(agent_outputs)

        # Add to state for prompt context
        enhanced_state = {
            **state,
            "risk_signals": risk_signals
        }

        return super().run(enhanced_state)

    def _aggregate_risk_signals(self, agent_outputs: dict) -> dict:
        """Collect risk signals from other agents."""
        signals = {
            "news_sentiment": None,
            "technical_signals": None,
            "financial_health": None
        }

        if "news_agent" in agent_outputs:
            news_result = agent_outputs["news_agent"].result
            signals["news_sentiment"] = news_result.get("sentiment")

        if "technical_agent" in agent_outputs:
            tech_result = agent_outputs["technical_agent"].result
            signals["technical_signals"] = tech_result.get("signals", {}).get("action")

        if "financial_agent" in agent_outputs:
            fin_result = agent_outputs["financial_agent"].result
            signals["financial_health"] = fin_result.get("health", {}).get("health_score")

        return signals
```

### Report Agent

```python
class ReportAgent(LLMAgent):
    """Synthesizes all agent outputs into a final report."""

    name = "report_agent"
    description = "Expert in investment report writing and analysis synthesis"

    def _get_task_description(self) -> str:
        return """
Synthesize all analysis results into a comprehensive investment report:
1. Executive summary (2-3 sentences)
2. Key findings from each analysis area
3. Investment recommendation (buy/hold/sell)
4. Price target and time horizon
5. Risk-reward assessment
6. Action items and next steps
"""

    def _get_output_format(self) -> str:
        return """{
    "executive_summary": "Brief 2-3 sentence overview",
    "recommendation": "buy|hold|sell",
    "confidence": 0.85,
    "price_target": {
        "target": 180.0,
        "time_horizon": "12 months",
        "upside": 0.15
    },
    "key_findings": {
        "sentiment": "Bullish based on positive news flow",
        "fundamentals": "Strong financials with growing margins",
        "technicals": "Uptrend with good momentum",
        "risks": "Valuation somewhat stretched"
    },
    "risk_reward": {
        "risk_score": 45,
        "reward_potential": 0.15,
        "risk_reward_ratio": 2.1
    },
    "action_items": [
        "Consider entry at current levels",
        "Set stop loss at $145",
        "Monitor Q4 earnings closely"
    ],
    "sources": ["News analysis", "Financial statements", "Technical data"],
    "disclaimer": "This is AI-generated analysis, not financial advice"
}"""

    def run(self, state: dict) -> AgentOutput:
        """Synthesize all agent outputs into final report."""
        # Collect all agent results
        agent_outputs = state.get("agent_outputs", {})

        # Build comprehensive context
        synthesis_context = self._build_synthesis_context(agent_outputs)

        enhanced_state = {
            **state,
            "synthesis_context": synthesis_context
        }

        return super().run(enhanced_state)

    def _build_synthesis_context(self, agent_outputs: dict) -> str:
        """Build context string from all agent outputs."""
        context_parts = []

        for agent_name, output in agent_outputs.items():
            context_parts.append(f"""
=== {agent_name.upper()} ANALYSIS ===
Confidence: {output.confidence}
Result: {output.result}
Citations: {', '.join(output.citations)}
""")

        return "\n".join(context_parts)

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """Report confidence based on contributing agent confidences."""
        agent_outputs = state.get("agent_outputs", {})

        if not agent_outputs:
            return 0.5

        # Weighted average of agent confidences
        total_confidence = sum(
            output.confidence for output in agent_outputs.values()
        )

        return total_confidence / len(agent_outputs)
```

---

## 4. Agent with Tool Usage

Template for agents that need to use external tools:

```python
from typing import Callable, Any

class ToolUsingAgent(LLMAgent):
    """Agent that can use external tools for data retrieval and actions."""

    def __init__(self, tools: dict[str, Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.tools = tools or {}

    def run(self, state: dict) -> AgentOutput:
        """Execute with tool usage capability."""
        # Determine which tools to use based on task
        required_tools = self._identify_required_tools(state)

        # Gather data using tools
        tool_results = {}
        for tool_name in required_tools:
            if tool_name in self.tools:
                try:
                    result = self._execute_tool(tool_name, state)
                    tool_results[tool_name] = result
                except Exception as e:
                    self.logger.warning(f"Tool {tool_name} failed: {e}")
                    tool_results[tool_name] = {"error": str(e)}

        # Add tool results to state for LLM context
        enhanced_state = {
            **state,
            "tool_results": tool_results
        }

        # Run LLM analysis with tool data
        return super().run(enhanced_state)

    def _identify_required_tools(self, state: dict) -> list[str]:
        """Identify which tools are needed for this task."""
        # Override for custom tool selection logic
        return list(self.tools.keys())

    def _execute_tool(self, tool_name: str, state: dict) -> Any:
        """Execute a specific tool with state context."""
        tool_func = self.tools[tool_name]

        # Extract relevant parameters from state
        params = self._extract_tool_params(tool_name, state)

        return tool_func(**params)

    def _extract_tool_params(self, tool_name: str, state: dict) -> dict:
        """Extract tool parameters from state."""
        # Override for custom parameter extraction
        return {"state": state}

# Example usage
def fetch_stock_price(symbol: str) -> dict:
    # API call to fetch price
    return {"price": 150.0, "change": 2.5}

def fetch_news(symbol: str) -> list:
    # API call to fetch news
    return [{"title": "News article", "sentiment": "positive"}]

# Create agent with tools
news_agent = ToolUsingAgent(
    tools={
        "fetch_price": fetch_stock_price,
        "fetch_news": fetch_news
    },
    model="gpt-4"
)
```

---

## 5. Agent with Memory

Template for agents that maintain context across executions:

```python
from typing import Optional
from datetime import datetime

class MemoryAgent(LLMAgent):
    """Agent with persistent memory for learning and context retention."""

    def __init__(self, memory_store: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.memory = memory_store or {
            "short_term": {},  # Current session
            "long_term": {},   # Persistent across sessions
            "episodic": []     # Past interactions
        }

    def run(self, state: dict) -> AgentOutput:
        """Execute with memory context."""
        # Retrieve relevant memories
        relevant_memories = self._retrieve_memories(state)

        # Add memories to context
        enhanced_state = {
            **state,
            "relevant_memories": relevant_memories,
            "memory_context": self._format_memories(relevant_memories)
        }

        # Run analysis
        result = super().run(enhanced_state)

        # Store new memories
        self._store_memories(state, result)

        return result

    def _retrieve_memories(self, state: dict) -> list[dict]:
        """Retrieve memories relevant to current state."""
        relevant = []

        # Search long-term memory
        stock_code = state.get("stock_code")
        if stock_code and stock_code in self.memory["long_term"]:
            relevant.append({
                "type": "long_term",
                "content": self.memory["long_term"][stock_code]
            })

        # Search episodic memory (recent interactions)
        for episode in self.memory["episodic"][-5:]:  # Last 5 episodes
            if self._is_relevant(episode, state):
                relevant.append({
                    "type": "episodic",
                    "content": episode
                })

        return relevant

    def _store_memories(self, state: dict, result: AgentOutput):
        """Store new memories from this interaction."""
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "stock_code": state.get("stock_code"),
            "analysis": result.result,
            "confidence": result.confidence
        }

        # Store in episodic memory
        self.memory["episodic"].append(memory_entry)

        # Keep only recent episodes
        if len(self.memory["episodic"]) > 100:
            self.memory["episodic"] = self.memory["episodic"][-100:]

        # Store key insights in long-term memory
        stock_code = state.get("stock_code")
        if stock_code and result.confidence > 0.8:
            if stock_code not in self.memory["long_term"]:
                self.memory["long_term"][stock_code] = []

            self.memory["long_term"][stock_code].append({
                "timestamp": datetime.now().isoformat(),
                "insight": result.result.get("thesis", ""),
                "confidence": result.confidence
            })

    def _is_relevant(self, episode: dict, state: dict) -> bool:
        """Check if a memory is relevant to current state."""
        # Same stock
        if episode.get("stock_code") == state.get("stock_code"):
            return True

        # Similar analysis type
        if episode.get("analysis_type") == state.get("analysis_type"):
            return True

        return False

    def _format_memories(self, memories: list[dict]) -> str:
        """Format memories for prompt injection."""
        if not memories:
            return "No relevant memories found."

        formatted = []
        for mem in memories:
            formatted.append(f"[{mem['type'].upper()}] {mem['content']}")

        return "\n---\n".join(formatted)
```

---

## 6. Testing Agents

### Unit Test Template

```python
import pytest
from unittest.mock import Mock, patch

class TestNewsAgent:
    @pytest.fixture
    def agent(self):
        return NewsAgent()

    @pytest.fixture
    def sample_state(self):
        return {
            "stock_code": "AAPL",
            "news_data": [
                {"title": "Apple reports record earnings", "sentiment": "positive"},
                {"title": "iPhone sales surge", "sentiment": "positive"}
            ]
        }

    def test_agent_initialization(self, agent):
        assert agent.name == "news_agent"
        assert agent.description is not None

    def test_run_returns_agent_output(self, agent, sample_state):
        result = agent.run(sample_state)

        assert isinstance(result, AgentOutput)
        assert result.agent_name == "news_agent"
        assert 0 <= result.confidence <= 1
        assert isinstance(result.citations, list)

    def test_output_contains_sentiment(self, agent, sample_state):
        result = agent.run(sample_state)

        assert "sentiment" in result.result
        assert result.result["sentiment"] in ["bullish", "bearish", "neutral"]

    def test_confidence_calculation(self, agent, sample_state):
        result = agent.run(sample_state)

        # Positive news should yield bullish sentiment with high confidence
        if result.result["sentiment"] == "bullish":
            assert result.confidence > 0.5

    @patch('agents.news_agent.openai.ChatCompletion.create')
    def test_llm_call(self, mock_openai, agent, sample_state):
        mock_openai.return_value = Mock(
            choices=[Mock(message=Mock(content='{"sentiment": "bullish", "confidence": 0.9}'))]
        )

        result = agent.run(sample_state)

        assert result.result["sentiment"] == "bullish"
        mock_openai.assert_called_once()
```

### Integration Test Template

```python
class TestInvestmentWorkflow:
    @pytest.fixture
    def workflow(self):
        """Create complete investment analysis workflow."""
        workflow = StateGraph(InvestmentState)

        workflow.add_node("news", NewsAgent().run)
        workflow.add_node("financial", FinancialAgent().run)
        workflow.add_node("technical", TechnicalAgent().run)
        workflow.add_node("risk", RiskAgent().run)
        workflow.add_node("report", ReportAgent().run)

        workflow.add_edge("news", "risk")
        workflow.add_edge("financial", "risk")
        workflow.add_edge("technical", "risk")
        workflow.add_edge("risk", "report")

        workflow.set_entry_point("news")
        workflow.set_finish_point("report")

        return workflow.compile()

    def test_workflow_execution(self, workflow):
        initial_state = {
            "stock_code": "AAPL",
            "market_data": {...},
            "news_data": [...],
            "agent_outputs": {},
            "errors": []
        }

        result = workflow.invoke(initial_state)

        assert "final_report" in result
        assert result["final_report"]["recommendation"] in ["buy", "hold", "sell"]
        assert len(result.get("errors", [])) == 0

    def test_parallel_execution(self, workflow):
        """Verify that independent agents execute in parallel."""
        import time

        start_time = time.time()
        result = workflow.invoke({...})
        end_time = time.time()

        # Parallel execution should be faster than sequential
        # Sequential would take ~6s (2s per agent), parallel should take ~2-3s
        assert end_time - start_time < 4.0

    def test_error_handling(self, workflow):
        """Test workflow handles agent failures gracefully."""
        initial_state = {
            "stock_code": "INVALID",
            "market_data": {},
            "news_data": [],  # Empty data should cause issues
            "agent_outputs": {},
            "errors": []
        }

        # Should not raise exception
        result = workflow.invoke(initial_state)

        # Should have error information
        assert "errors" in result or "error" in result.get("final_report", {})
```

---

## Summary

These templates provide a solid foundation for building multi-agent systems:

1. **BaseAgent** - Standard interface and utilities
2. **LLMAgent** - LLM integration with prompt engineering
3. **Specialized Agents** - Domain-specific implementations
4. **Tool-Using Agents** - External tool integration
5. **Memory Agents** - Context retention across executions
6. **Testing** - Unit and integration test patterns

Adapt these templates to your specific domain and requirements.
