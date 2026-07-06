---
name: multi-agent-developer
description: Guide for designing and implementing multi-agent systems. Provides expert guidance on agent architecture, workflow orchestration using LangGraph, prompt design, output parsing, and state management. Use this skill when building AI systems with multiple specialized agents, designing agent collaboration patterns, implementing workflow DAGs, or generating agent code templates. Applicable to any multi-agent system including investment research, data analysis, content generation, or autonomous task execution.
---

# Multi-Agent System Developer Skill

This skill provides expert guidance for designing and implementing multi-agent AI systems. It combines architectural patterns with practical code generation to help you build robust, scalable agent-based systems.

## Core Principles

### 1. Agent Specialization
Each agent should have a single, well-defined responsibility. Agents are domain experts, not generalists. This separation of concerns makes the system:
- Easier to test and debug
- More maintainable and extensible
- Capable of parallel execution
- Flexible for different workflows

### 2. Workflow Orchestration
Multi-agent systems require explicit coordination. Use workflow engines (like LangGraph) to:
- Define execution order and dependencies
- Enable parallel agent execution
- Handle errors and fallbacks
- Manage state transitions

### 3. Structured Communication
Agents must communicate through well-defined interfaces:
- Standardized input/output formats
- Type-safe data contracts
- Explicit state management
- Event-driven notifications

### 4. Separation of Concerns
Keep business logic, AI logic, and orchestration separate:
- **Agents**: Domain expertise and analysis
- **Workflow**: Coordination and control flow
- **Services**: Business operations and persistence
- **API**: External interface

---

## Workflow

When developing a multi-agent system, follow this structured approach:

### Phase 1: Agent Design & Planning

1. **Identify Agent Roles**
   - Analyze the problem domain
   - Break down into specialized tasks
   - Define clear agent responsibilities
   - Identify dependencies and communication patterns

2. **Define Agent Interfaces**
   - Design input data structures
   - Define output formats and schemas
   - Establish confidence scoring and citation requirements
   - Plan error handling strategies

3. **Design Workflow Architecture**
   - Map out the execution DAG
   - Identify parallel execution opportunities
   - Define conditional branching points
   - Plan error recovery and fallback paths

### Phase 2: Core Implementation

4. **Implement BaseAgent Framework**
   - Create base class with standard interface
   - Implement common utilities (logging, error handling)
   - Set up LLM integration layer
   - Build output parsing infrastructure

5. **Create Specialized Agents**
   - Implement each agent's domain logic
   - Design structured prompts for each agent
   - Build output validators and parsers
   - Add confidence scoring and citations

6. **Build Workflow Orchestrator**
   - Implement LangGraph StateGraph
   - Define nodes and edges
   - Configure parallel execution
   - Add conditional routing logic

### Phase 3: State Management & Integration

7. **Design State Management**
   - Define AgentState structure
   - Implement state persistence
   - Design memory systems (short-term and long-term)
   - Set up event sourcing for traceability

8. **Implement Communication Layer**
   - Set up event-driven messaging
   - Implement WebSocket for real-time updates
   - Design notification system
   - Add logging and monitoring

### Phase 4: Testing & Optimization

9. **Test Agent Interactions**
   - Unit test individual agents
   - Integration test agent workflows
   - Test error handling and edge cases
   - Validate output quality and consistency

10. **Optimize Performance**
    - Profile agent execution times
    - Optimize parallel execution
    - Implement caching strategies
    - Tune prompt engineering

---

## Agent Development Patterns

### Pattern 1: BaseAgent Template

Every agent should follow this standard interface:

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class AgentOutput(BaseModel):
    agent_name: str
    result: dict[str, Any]
    confidence: float
    citations: list[str]
    metadata: dict[str, Any] = {}

class BaseAgent(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, state: dict) -> AgentOutput:
        """
        Execute agent logic and return structured output.

        Args:
            state: Current workflow state including all context

        Returns:
            AgentOutput with results, confidence, and citations
        """
        pass

    def build_prompt(self, state: dict) -> str:
        """
        Construct prompt from current state.
        Override for custom prompt engineering.
        """
        raise NotImplementedError

    def parse_response(self, response: str) -> dict:
        """
        Parse LLM response into structured output.
        Override for custom parsing logic.
        """
        raise NotImplementedError
```

### Pattern 2: Structured Prompt Design

Prompts should follow this structure for consistency and reliability:

```markdown
[ROLE]
You are a {domain} expert specializing in {specific_area}.

[CONTEXT]
{relevant_data_and_context}

[TASK]
{clear_specific_instructions}

[OUTPUT FORMAT]
{exact_json_or_structured_format}

[EXAMPLES]
{example_input_output_pairs}

[CONSTRAINTS]
{limitations_and_requirements}
```

### Pattern 3: Output Validation

Always validate agent outputs to ensure quality:

```python
from pydantic import validator

class AgentOutput(BaseModel):
    agent_name: str
    result: dict
    confidence: float
    citations: list[str]

    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v

    @validator('citations')
    def validate_citations(cls, v):
        if not v:
            raise ValueError('At least one citation required')
        return v
```

---

## Workflow Orchestration Patterns

### Pattern 1: Parallel Execution

Execute multiple independent agents simultaneously:

```python
from langgraph.graph import StateGraph

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent_1", Agent1())
workflow.add_node("agent_2", Agent2())
workflow.add_node("agent_3", Agent3())
workflow.add_node("aggregator", AggregatorAgent())

# Parallel edges
workflow.add_edge("agent_1", "aggregator")
workflow.add_edge("agent_2", "aggregator")
workflow.add_edge("agent_3", "aggregator")

# Entry and exit points
workflow.set_entry_point("agent_1")  # All three start in parallel
workflow.set_finish_point("aggregator")
```

### Pattern 2: Sequential Pipeline

Execute agents in sequence where each depends on the previous:

```python
workflow = StateGraph(AgentState)

workflow.add_node("data_collector", DataCollector())
workflow.add_node("analyzer", Analyzer())
workflow.add_node("validator", Validator())
workflow.add_node("reporter", Reporter())

workflow.add_edge("data_collector", "analyzer")
workflow.add_edge("analyzer", "validator")
workflow.add_edge("validator", "reporter")

workflow.set_entry_point("data_collector")
workflow.set_finish_point("reporter")
```

### Pattern 3: Conditional Routing

Route to different agents based on conditions:

```python
from langgraph.graph import END

def should_use_expensive_analysis(state):
    if state.get("complexity_score", 0) > 0.7:
        return "deep_analyzer"
    return "fast_analyzer"

workflow = StateGraph(AgentState)

workflow.add_node("classifier", ClassifierAgent())
workflow.add_node("fast_analyzer", FastAnalyzer())
workflow.add_node("deep_analyzer", DeepAnalyzer())

workflow.add_conditional_edges(
    "classifier",
    should_use_expensive_analysis,
    {
        "fast_analyzer": "fast_analyzer",
        "deep_analyzer": "deep_analyzer"
    }
)
```

### Pattern 4: Error Handling & Fallback

Implement robust error handling:

```python
def safe_agent_execution(state, agent, fallback_result=None):
    try:
        return agent.run(state)
    except Exception as e:
        logger.error(f"Agent {agent.name} failed: {e}")
        return AgentOutput(
            agent_name=agent.name,
            result=fallback_result or {"error": str(e)},
            confidence=0.0,
            citations=[]
        )
```

---

## State Management

### AgentState Design

Design state structures that are:
- Minimal (only necessary data)
- Serializable (can be persisted)
- Immutable between nodes (copy on write)
- Well-typed (use Pydantic models)

```python
from pydantic import BaseModel
from typing import Any
from datetime import datetime

class AgentState(BaseModel):
    # Core identifiers
    task_id: str
    user_id: str

    # Input data
    query: str
    context: dict[str, Any]

    # Intermediate results
    agent_outputs: dict[str, AgentOutput] = {}

    # Final output
    final_result: dict[str, Any] = {}

    # Metadata
    started_at: datetime = datetime.now()
    status: str = "pending"
```

### Memory Patterns

1. **Short-term Memory (Workflow State)**
   - Current workflow execution context
   - Intermediate agent results
   - Passed between nodes via state

2. **Long-term Memory (Persistent)**
   - Database storage for completed analyses
   - User history and preferences
   - Historical patterns and insights

3. **Episodic Memory (Context Window)**
   - Recent conversation history
   - Current session context
   - Limited by context window size

---

## Prompt Engineering Best Practices

### 1. Role Definition
Clearly define the agent's expertise and perspective:
```
You are a senior financial analyst with 20 years of experience
in equity research, specializing in technology sector analysis.
```

### 2. Context Injection
Provide relevant, structured context:
```
[CONTEXT]
Stock: AAPL (Apple Inc.)
Current Price: $175.50
Market Cap: $2.8T
Recent News: iPhone 15 launch, Services revenue growth
```

### 3. Task Specification
Be specific about what you want:
```
[TASK]
Analyze the stock's technical indicators and provide:
1. Trend direction (bullish/bearish/neutral)
2. Key support and resistance levels
3. Momentum indicators (RSI, MACD)
4. Volume analysis
5. Short-term price prediction (1-2 weeks)
```

### 4. Output Format
Define exact structure expected:
```json
{
  "trend": "bullish",
  "support_levels": [170, 165],
  "resistance_levels": [180, 185],
  "rsi": 65,
  "macd_signal": "bullish_crossover",
  "prediction": {
    "direction": "up",
    "target": 182,
    "confidence": 0.75
  }
}
```

### 5. Examples
Provide input-output examples:
```
[EXAMPLE]
Input: Stock XYZ with RSI=30, MACD=bullish_crossover, high volume
Output: {
  "trend": "oversold_bounce",
  "signal": "strong_buy",
  "confidence": 0.85
}
```

---

## Common Workflow Templates

### Investment Research Workflow
```
User Query
    ↓
Planner Agent (task decomposition)
    ↓
[Parallel Execution]
├── News Agent (sentiment analysis)
├── Financial Agent (fundamentals)
├── Technical Agent (indicators)
└── Macro Agent (economic context)
    ↓
Risk Agent (risk assessment)
    ↓
Quant Agent (scoring)
    ↓
Report Agent (synthesis)
    ↓
Final Report
```

### Content Generation Workflow
```
Topic Input
    ↓
Research Agent (gather information)
    ↓
Outline Agent (structure content)
    ↓
[Parallel Execution]
├── Introduction Writer
├── Section Writers (multiple)
└── Conclusion Writer
    ↓
Editor Agent (consistency check)
    ↓
SEO Agent (optimization)
    ↓
Final Content
```

### Data Analysis Workflow
```
Data Source
    ↓
Data Collector Agent
    ↓
[Parallel Execution]
├── Statistical Analyzer
├── Pattern Detector
└── Anomaly Identifier
    ↓
Insight Synthesizer
    ↓
Visualization Agent
    ↓
Report Generator
```

---

## Debugging Multi-Agent Systems

### Common Issues

1. **Agent Output Quality Issues**
   - Check prompt clarity and specificity
   - Verify context injection is complete
   - Review output format requirements
   - Add more examples to prompt

2. **Workflow Execution Failures**
   - Validate state schema compatibility
   - Check agent dependencies
   - Implement proper error handling
   - Add logging at each node

3. **Performance Bottlenecks**
   - Identify slow agents (profile execution)
   - Maximize parallel execution
   - Implement caching for repeated operations
   - Optimize prompt length

4. **State Management Issues**
   - Ensure state is immutable between nodes
   - Validate state serialization
   - Check for race conditions in parallel execution
   - Implement proper state persistence

### Debugging Tools

1. **Logging**
```python
import structlog

logger = structlog.get_logger()

def run(self, state):
    logger.info("agent_start", agent=self.name, state_keys=list(state.keys()))
    result = self.execute(state)
    logger.info("agent_complete", agent=self.name, confidence=result.confidence)
    return result
```

2. **State Inspection**
```python
def inspect_state(state, stage):
    print(f"\n{'='*50}")
    print(f"Stage: {stage}")
    print(f"Keys: {list(state.keys())}")
    print(f"Agent outputs: {list(state.get('agent_outputs', {}).keys())}")
    print(f"{'='*50}\n")
```

3. **Visualization**
```python
# Generate workflow visualization
workflow.get_graph().draw_mermaid_png(output_file="workflow.png")
```

---

## Integration with Existing Systems

### API Integration
```python
from fastapi import APIRouter, BackgroundTasks

router = APIRouter()

@router.post("/api/agent/run")
async def run_agent_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    # Create workflow
    workflow = create_workflow(request.workflow_type)

    # Execute asynchronously
    background_tasks.add_task(
        execute_workflow,
        workflow,
        request.input_data
    )

    return {"status": "started", "task_id": request.task_id}
```

### WebSocket Updates
```python
from fastapi import WebSocket

@router.websocket("/ws/workflow/{task_id}")
async def workflow_updates(websocket: WebSocket, task_id: str):
    await websocket.accept()

    # Subscribe to workflow events
    async for event in workflow_event_stream(task_id):
        await websocket.send_json({
            "type": event.type,
            "agent": event.agent_name,
            "status": event.status,
            "progress": event.progress
        })
```

---

## Best Practices Summary

### Do's
✅ Define clear agent responsibilities
✅ Use structured prompts with examples
✅ Validate all agent outputs
✅ Implement proper error handling
✅ Maximize parallel execution
✅ Log everything for debugging
✅ Use type-safe state management
✅ Test agent interactions thoroughly

### Don'ts
❌ Create overly complex workflows
❌ Allow agents to share mutable state
❌ Skip output validation
❌ Ignore error handling
❌ Use vague or ambiguous prompts
❌ Mix business logic with agent logic
❌ Forget to handle edge cases
❌ Skip performance profiling

---

## Quick Start Checklist

When starting a new multi-agent project:

- [ ] Define problem domain and agent roles
- [ ] Design agent interfaces and data contracts
- [ ] Create workflow DAG structure
- [ ] Implement BaseAgent framework
- [ ] Design prompts for each agent
- [ ] Build workflow orchestrator
- [ ] Implement state management
- [ ] Add error handling and logging
- [ ] Test individual agents
- [ ] Test complete workflow
- [ ] Optimize performance
- [ ] Deploy and monitor

---

## Development Cycle Integration

This skill integrates with development planning to enable **Sprint-based code generation**. When combined with the dev-timeline skill, it transforms development plans into working code.

### Sprint-Based Development Workflow

```
Development Plan (dev-timeline)
    ↓
Sprint Task Decomposition
    ↓
Module Specifications
    ↓
Code Generation (multi-agent-developer)
    ↓
Testing & Validation
    ↓
Integration & Deployment
```

### When Users Request Module Development

If users mention:
- "Implement [module name] from the development plan"
- "Generate code for Sprint [X-Y]"
- "Build [Agent name] according to the timeline"
- "Start developing [feature]"

Follow this process:

1. **Identify the Sprint and Module**
   - Use dev-timeline to understand the development phase
   - Reference the detailed development documents
   - Identify specific deliverables and acceptance criteria

2. **Extract Design Specifications**
   - Read relevant sections from development documents
   - Identify agent responsibilities and interfaces
   - Define input/output formats
   - Plan integration points

3. **Generate Code Using Skill Resources**
   - Use agent-templates.md for agent implementations
   - Use prompt-templates.md for prompt design
   - Use workflow-patterns.md for workflow orchestration
   - Use state-management.md for state design
   - Reference development-integration.md for Sprint-specific guidance

4. **Provide Complete Deliverables**
   - Generate all required files
   - Include tests and documentation
   - Verify against acceptance criteria
   - Ensure integration compatibility

### Reference Documentation

For Sprint-specific guidance, see:

- **references/development-integration.md** - Overall integration workflow
- **references/sprint-5-6-guide.md** - Agent Foundation sprint guide
- **references/workflow-patterns.md** - Workflow implementation patterns
- **references/agent-templates.md** - Agent code templates
- **references/prompt-templates.md** - Prompt design patterns

### Example: Implementing News Agent

When asked to "Implement the News Agent for AI Investment OS":

```markdown
Based on the development plan (Sprint 5-6: Agent Foundation) and multi-agent-developer skill:

1. **Design Specifications** (from detailed design document):
   - News sentiment analysis
   - Event extraction
   - Impact assessment
   - Structured JSON output

2. **Using Skill Resources**:
   - agent-templates.md: LLMAgent Template
   - prompt-templates.md: News Analysis Prompt (CRAFT framework)
   - development-integration.md: Sprint 5-6 task breakdown

3. **Generated Files**:
   - news_agent.py (agent implementation)
   - prompts.py (prompt templates)
   - schemas.py (data models)
   - test_news_agent.py (unit tests)

4. **Verification**:
   - ✅ Inherits from BaseAgent/LLMAgent
   - ✅ Uses CRAFT prompt framework
   - ✅ Outputs include confidence and citations
   - ✅ Error handling complete
   - ✅ Tests pass
```

### Integration with dev-timeline Skill

The dev-timeline skill provides:
- Development phase planning
- Sprint breakdown and timeline estimation
- Task dependency identification
- Risk assessment

This skill (multi-agent-developer) provides:
- Code generation for specific modules
- Architectural pattern implementation
- Best practices enforcement
- Quality assurance

**Combined**, they enable:
- Plan-driven development
- Consistent code quality
- Efficient Sprint execution
- Reduced development time

---

## Quick Start for AI Investment OS

To start developing AI Investment OS modules:

### Step 1: Plan the Sprint

```python
# Use dev-timeline skill
"""
请帮我规划Sprint [X-Y]的开发任务，包括：
1. 任务分解
2. 时间估算
3. 依赖关系
4. 交付物清单
"""
```

### Step 2: Generate Module Code

```python
# Use multi-agent-developer skill
"""
基于multi-agent-developer skill和开发文档，实现[模块名称]

要求：
1. 参考[具体设计文档章节]
2. 使用[具体skill资源]
3. 遵循AI Investment OS编码规范
4. 包含完整的测试

请生成：
- [文件1]
- [文件2]
- [文件3]
"""
```

### Step 3: Verify and Integrate

```python
# Verify implementation
"""
请验证生成的代码：
1. 符合设计规格
2. 通过所有测试
3. 与现有系统兼容
4. 遵循最佳实践
"""
```

### Available Sprint Guides

- **Sprint 1-2**: Foundation (Project setup, DB, API framework)
- **Sprint 3-4**: Core Services (Stock service, Workspace service)
- **Sprint 5-6**: Agent Foundation (BaseAgent, LangGraph, News Agent) ← See sprint-5-6-guide.md
- **Sprint 7-8**: Agent Fleet (Financial, Technical, Macro, Risk Agents)
- **Sprint 9-10**: Advanced Features (Quant, Report, RAG integration)
- **Sprint 11-12**: Integration & Polish (Candidate Pool, Strategy, Reports)
- **Sprint 13-14**: Testing & Deployment (E2E testing, Production)

---

## Reference Documentation

The skill includes comprehensive reference documentation:



- **references/workflow-patterns.md** - Common workflow DAG patterns with code examples
- **references/agent-templates.md** - Complete agent implementation templates
- **references/prompt-templates.md** - Prompt engineering patterns and examples
- **references/state-management.md** - State design patterns and best practices

---

## Example: Complete Multi-Agent Investment System

See the reference documentation for a complete example of building an investment research system with:

- 8 specialized agents (News, Financial, Technical, Macro, Risk, Quant, Report, Planner)
- LangGraph workflow orchestration
- Parallel agent execution
- Structured output formats
- Event-driven updates
- State persistence

This pattern can be adapted for any domain requiring multiple specialized AI agents working together.
