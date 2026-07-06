# Workflow Patterns Reference

This document provides common workflow DAG patterns for multi-agent systems with complete code examples.

---

## Table of Contents

1. [Parallel Fan-Out/Fan-In Pattern](#1-parallel-fan-outfan-in-pattern)
2. [Sequential Pipeline Pattern](#2-sequential-pipeline-pattern)
3. [Conditional Routing Pattern](#3-conditional-routing-pattern)
4. [Iterative Refinement Pattern](#4-iterative-refinement-pattern)
5. [Supervisor Pattern](#5-supervisor-pattern)
6. [Map-Reduce Pattern](#6-map-reduce-pattern)
7. [Error Handling Patterns](#7-error-handling-patterns)

---

## 1. Parallel Fan-Out/Fan-In Pattern

Execute multiple independent agents simultaneously, then aggregate results.

**Use Case:** Multiple specialized analyses on the same data (e.g., financial, technical, and news analysis of a stock).

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AnalysisState(TypedDict):
    stock_code: str
    market_data: dict
    news_data: list
    # Parallel results collected via operator.add
    agent_results: Annotated[list, operator.add]
    final_report: dict

# Agent implementations
class NewsAgent:
    def run(self, state: AnalysisState) -> dict:
        # Analyze news sentiment
        return {"agent": "news", "sentiment": "bullish", "confidence": 0.8}

class FinancialAgent:
    def run(self, state: AnalysisState) -> dict:
        # Analyze financials
        return {"agent": "financial", "score": 85, "confidence": 0.9}

class TechnicalAgent:
    def run(self, state: AnalysisState) -> dict:
        # Analyze technical indicators
        return {"agent": "technical", "signal": "buy", "confidence": 0.75}

class AggregatorAgent:
    def run(self, state: AnalysisState) -> dict:
        # Combine all results
        results = state["agent_results"]
        return {
            "overall_score": sum(r.get("score", 0) for r in results) / len(results),
            "recommendation": "buy",
            "reasoning": [r for r in results]
        }

# Build workflow
workflow = StateGraph(AnalysisState)

# Add nodes
workflow.add_node("news", lambda s: {"agent_results": [NewsAgent().run(s)]})
workflow.add_node("financial", lambda s: {"agent_results": [FinancialAgent().run(s)]})
workflow.add_node("technical", lambda s: {"agent_results": [TechnicalAgent().run(s)]})
workflow.add_node("aggregator", lambda s: {"final_report": AggregatorAgent().run(s)})

# Parallel edges (fan-out)
workflow.add_edge("news", "aggregator")
workflow.add_edge("financial", "aggregator")
workflow.add_edge("technical", "aggregator")

# Entry and exit
workflow.set_entry_point("news")  # All three start in parallel
workflow.set_finish_point("aggregator")

# Compile and run
app = workflow.compile()
result = app.invoke({
    "stock_code": "AAPL",
    "market_data": {...},
    "news_data": [...],
    "agent_results": []
})
```

**Key Points:**
- Use `Annotated[list, operator.add]` to collect parallel results
- All parallel agents feed into a single aggregator
- Entry point triggers all parallel branches

---

## 2. Sequential Pipeline Pattern

Execute agents in strict sequence where each depends on the previous result.

**Use Case:** Data collection → Analysis → Validation → Report generation.

```python
class PipelineState(TypedDict):
    input_data: dict
    collected_data: dict
    analysis_result: dict
    validation_result: dict
    final_report: dict

# Sequential agents
class DataCollector:
    def run(self, state: PipelineState) -> dict:
        return {"collected_data": {"prices": [100, 101, 102], "volume": [1000, 1200, 1100]}}

class Analyzer:
    def run(self, state: PipelineState) -> dict:
        data = state["collected_data"]
        return {"analysis_result": {"trend": "upward", "volatility": "low"}}

class Validator:
    def run(self, state: PipelineState) -> dict:
        analysis = state["analysis_result"]
        return {"validation_result": {"valid": True, "confidence": 0.92}}

class Reporter:
    def run(self, state: PipelineState) -> dict:
        return {"final_report": {"summary": "Stock shows upward trend", "risk": "low"}}

# Build pipeline
workflow = StateGraph(PipelineState)

workflow.add_node("collector", lambda s: DataCollector().run(s))
workflow.add_node("analyzer", lambda s: Analyzer().run(s))
workflow.add_node("validator", lambda s: Validator().run(s))
workflow.add_node("reporter", lambda s: Reporter().run(s))

# Sequential edges
workflow.add_edge("collector", "analyzer")
workflow.add_edge("analyzer", "validator")
workflow.add_edge("validator", "reporter")

workflow.set_entry_point("collector")
workflow.set_finish_point("reporter")

app = workflow.compile()
```

---

## 3. Conditional Routing Pattern

Route to different agents based on runtime conditions.

**Use Case:** Different analysis depth based on complexity or user tier.

```python
from langgraph.graph import END

class RouterState(TypedDict):
    query: str
    complexity_score: float
    user_tier: str
    result: dict

def route_by_complexity(state: RouterState) -> str:
    """Route to appropriate analyzer based on complexity."""
    if state.get("complexity_score", 0) > 0.7:
        return "deep_analyzer"
    elif state.get("user_tier") == "pro":
        return "advanced_analyzer"
    else:
        return "fast_analyzer"

class ClassifierAgent:
    def run(self, state: RouterState) -> dict:
        # Classify query complexity
        return {"complexity_score": 0.8, "user_tier": "pro"}

class FastAnalyzer:
    def run(self, state: RouterState) -> dict:
        return {"result": {"analysis": "basic", "time": "0.5s"}}

class AdvancedAnalyzer:
    def run(self, state: RouterState) -> dict:
        return {"result": {"analysis": "advanced", "time": "2s"}}

class DeepAnalyzer:
    def run(self, state: RouterState) -> dict:
        return {"result": {"analysis": "comprehensive", "time": "5s"}}

# Build workflow
workflow = StateGraph(RouterState)

workflow.add_node("classifier", lambda s: ClassifierAgent().run(s))
workflow.add_node("fast_analyzer", lambda s: FastAnalyzer().run(s))
workflow.add_node("advanced_analyzer", lambda s: AdvancedAnalyzer().run(s))
workflow.add_node("deep_analyzer", lambda s: DeepAnalyzer().run(s))

# Conditional routing
workflow.add_conditional_edges(
    "classifier",
    route_by_complexity,
    {
        "fast_analyzer": "fast_analyzer",
        "advanced_analyzer": "advanced_analyzer",
        "deep_analyzer": "deep_analyzer"
    }
)

# All routes lead to END
workflow.add_edge("fast_analyzer", END)
workflow.add_edge("advanced_analyzer", END)
workflow.add_edge("deep_analyzer", END)

workflow.set_entry_point("classifier")
```

---

## 4. Iterative Refinement Pattern

Iteratively improve output until quality threshold is met.

**Use Case:** Content generation that needs multiple refinement passes.

```python
import operator

class RefinementState(TypedDict):
    initial_prompt: str
    current_draft: str
    quality_score: float
    iteration: int
    feedback_history: Annotated[list, operator.add]

MAX_ITERATIONS = 3
QUALITY_THRESHOLD = 0.9

class DrafterAgent:
    def run(self, state: RefinementState) -> dict:
        if state.get("iteration", 0) == 0:
            # Initial draft
            return {"current_draft": "Initial draft based on prompt..."}
        else:
            # Refine based on feedback
            feedback = state.get("feedback_history", [])[-1] if state.get("feedback_history") else ""
            return {"current_draft": f"Refined draft incorporating: {feedback}"}

class CriticAgent:
    def run(self, state: RefinementState) -> dict:
        draft = state["current_draft"]
        # Evaluate quality
        score = 0.7 + (state.get("iteration", 0) * 0.1)  # Improves with iterations
        feedback = f"Iteration {state.get('iteration', 0)}: Needs more detail on..."
        return {
            "quality_score": min(score, 1.0),
            "feedback_history": [feedback]
        }

def should_continue(state: RefinementState) -> str:
    """Decide whether to continue refining or finish."""
    if state.get("quality_score", 0) >= QUALITY_THRESHOLD:
        return "finalizer"
    if state.get("iteration", 0) >= MAX_ITERATIONS:
        return "finalizer"
    return "drafter"

class FinalizerAgent:
    def run(self, state: RefinementState) -> dict:
        return {"final_output": state["current_draft"]}

# Build workflow
workflow = StateGraph(RefinementState)

workflow.add_node("drafter", lambda s: {**s, **DrafterAgent().run(s), "iteration": s.get("iteration", 0) + 1})
workflow.add_node("critic", lambda s: {**s, **CriticAgent().run(s)})
workflow.add_node("finalizer", lambda s: FinalizerAgent().run(s))

# Iterative loop
workflow.add_edge("drafter", "critic")
workflow.add_conditional_edges("critic", should_continue, {
    "drafter": "drafter",
    "finalizer": "finalizer"
})

workflow.set_entry_point("drafter")
workflow.set_finish_point("finalizer")
```

---

## 5. Supervisor Pattern

A supervisor agent dynamically routes tasks to specialized workers.

**Use Case:** Flexible task routing where the supervisor decides which agent handles each task.

```python
class SupervisorState(TypedDict):
    task: str
    available_agents: list[str]
    selected_agent: str
    agent_result: dict
    final_result: dict

class SupervisorAgent:
    def run(self, state: SupervisorState) -> dict:
        task = state["task"]
        # Analyze task and select appropriate agent
        if "news" in task.lower() or "sentiment" in task.lower():
            return {"selected_agent": "news_agent"}
        elif "financial" in task.lower() or "fundamental" in task.lower():
            return {"selected_agent": "financial_agent"}
        else:
            return {"selected_agent": "general_agent"}

def route_to_agent(state: SupervisorState) -> str:
    return state.get("selected_agent", "general_agent")

class NewsAgent:
    def run(self, state: SupervisorState) -> dict:
        return {"agent_result": {"sentiment": "positive", "sources": ["reuters", "bloomberg"]}}

class FinancialAgent:
    def run(self, state: SupervisorState) -> dict:
        return {"agent_result": {"pe_ratio": 25.5, "roe": 0.18}}

class GeneralAgent:
    def run(self, state: SupervisorState) -> dict:
        return {"agent_result": {"analysis": "general analysis"}}

class ReporterAgent:
    def run(self, state: SupervisorState) -> dict:
        return {"final_result": {"summary": "Analysis complete", "data": state["agent_result"]}}

# Build workflow
workflow = StateGraph(SupervisorState)

workflow.add_node("supervisor", lambda s: SupervisorAgent().run(s))
workflow.add_node("news_agent", lambda s: NewsAgent().run(s))
workflow.add_node("financial_agent", lambda s: FinancialAgent().run(s))
workflow.add_node("general_agent", lambda s: GeneralAgent().run(s))
workflow.add_node("reporter", lambda s: ReporterAgent().run(s))

# Supervisor routes to appropriate agent
workflow.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "news_agent": "news_agent",
        "financial_agent": "financial_agent",
        "general_agent": "general_agent"
    }
)

# All agents feed into reporter
workflow.add_edge("news_agent", "reporter")
workflow.add_edge("financial_agent", "reporter")
workflow.add_edge("general_agent", "reporter")

workflow.set_entry_point("supervisor")
workflow.set_finish_point("reporter")
```

---

## 6. Map-Reduce Pattern

Process multiple items in parallel, then reduce/aggregate results.

**Use Case:** Analyzing multiple stocks simultaneously, then generating a summary report.

```python
class MapReduceState(TypedDict):
    stock_codes: list[str]
    individual_results: Annotated[list, operator.add]
    summary_report: dict

class StockAnalyzer:
    def run(self, stock_code: str) -> dict:
        # Analyze individual stock
        return {
            "stock": stock_code,
            "score": 85,
            "recommendation": "buy"
        }

class SummaryAgent:
    def run(self, state: MapReduceState) -> dict:
        results = state["individual_results"]
        # Aggregate results
        return {
            "summary_report": {
                "total_stocks": len(results),
                "buy_count": sum(1 for r in results if r.get("recommendation") == "buy"),
                "average_score": sum(r.get("score", 0) for r in results) / len(results) if results else 0,
                "top_picks": [r["stock"] for r in sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:5]]
            }
        }

# Map function: analyze each stock in parallel
def analyze_stock(state: MapReduceState) -> dict:
    # This would be called for each stock in parallel
    # In practice, use a map operation or parallel execution
    results = []
    for stock in state.get("stock_codes", []):
        result = StockAnalyzer().run(stock)
        results.append(result)
    return {"individual_results": results}

# Build workflow
workflow = StateGraph(MapReduceState)

workflow.add_node("mapper", analyze_stock)
workflow.add_node("reducer", lambda s: SummaryAgent().run(s))

workflow.add_edge("mapper", "reducer")

workflow.set_entry_point("mapper")
workflow.set_finish_point("reducer")
```

---

## 7. Error Handling Patterns

### Pattern A: Try-Catch with Fallback

```python
def safe_agent_execution(state, agent, fallback_result=None):
    """Execute agent with error handling and fallback."""
    try:
        result = agent.run(state)
        return {
            **result,
            "status": "success",
            "error": None
        }
    except Exception as e:
        logger.error(f"Agent {agent.name} failed: {e}")
        return {
            "result": fallback_result or {},
            "status": "failed",
            "error": str(e),
            "confidence": 0.0
        }

# Usage in workflow
workflow.add_node("news", lambda s: safe_agent_execution(s, NewsAgent(), {"sentiment": "unknown"}))
```

### Pattern B: Retry with Exponential Backoff

```python
import time
from typing import Callable

def retry_agent(agent_func: Callable, max_retries: int = 3, base_delay: float = 1.0):
    """Retry agent execution with exponential backoff."""
    def wrapper(state):
        for attempt in range(max_retries):
            try:
                return agent_func(state)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
    return wrapper

# Usage
workflow.add_node("flaky_agent", retry_agent(lambda s: FlakyAgent().run(s)))
```

### Pattern C: Circuit Breaker

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise

# Usage
breaker = CircuitBreaker()
workflow.add_node("protected_agent", lambda s: breaker.call(lambda: RiskyAgent().run(s)))
```

---

## Complete Example: Investment Research Workflow

Combining multiple patterns into a production-ready workflow:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class InvestmentState(TypedDict):
    stock_code: str
    market_data: dict
    news_data: list
    agent_results: Annotated[list, operator.add]
    risk_assessment: dict
    final_report: dict
    errors: Annotated[list, operator.add]

# Agents
class NewsAgent:
    def run(self, state: InvestmentState) -> dict:
        return {"agent_results": [{"agent": "news", "sentiment": "bullish"}]}

class FinancialAgent:
    def run(self, state: InvestmentState) -> dict:
        return {"agent_results": [{"agent": "financial", "score": 85}]}

class TechnicalAgent:
    def run(self, state: InvestmentState) -> dict:
        return {"agent_results": [{"agent": "technical", "signal": "buy"}]}

class RiskAgent:
    def run(self, state: InvestmentState) -> dict:
        return {"risk_assessment": {"level": "medium", "factors": ["volatility"]}}

class ReportAgent:
    def run(self, state: InvestmentState) -> dict:
        return {"final_report": {"recommendation": "buy", "confidence": 0.85}}

# Error handling wrapper
def safe_run(agent_class, state, fallback=None):
    try:
        return agent_class().run(state)
    except Exception as e:
        return {"errors": [str(e)]} if fallback is None else fallback

# Build workflow
workflow = StateGraph(InvestmentState)

# Parallel analysis agents
workflow.add_node("news", lambda s: safe_run(NewsAgent, s))
workflow.add_node("financial", lambda s: safe_run(FinancialAgent, s))
workflow.add_node("technical", lambda s: safe_run(TechnicalAgent, s))

# Sequential agents
workflow.add_node("risk", lambda s: safe_run(RiskAgent, s))
workflow.add_node("report", lambda s: safe_run(ReportAgent, s))

# Fan-out from entry to parallel agents
workflow.set_entry_point("news")
workflow.add_edge("news", "risk")
workflow.add_edge("financial", "risk")
workflow.add_edge("technical", "risk")

# Sequential flow
workflow.add_edge("risk", "report")
workflow.set_finish_point("report")

# Compile
app = workflow.compile()

# Execute
result = app.invoke({
    "stock_code": "AAPL",
    "market_data": {},
    "news_data": [],
    "agent_results": [],
    "errors": []
})
```

---

## Summary

| Pattern | Use Case | Parallelism | Complexity |
|---------|----------|-------------|------------|
| Fan-Out/Fan-In | Multiple analyses on same data | High | Medium |
| Sequential Pipeline | Step-by-step processing | None | Low |
| Conditional Routing | Dynamic agent selection | Variable | Medium |
| Iterative Refinement | Quality improvement loops | None | High |
| Supervisor | Flexible task routing | Variable | High |
| Map-Reduce | Batch processing | High | Medium |

Choose the pattern that best fits your use case, and combine patterns for complex workflows.
