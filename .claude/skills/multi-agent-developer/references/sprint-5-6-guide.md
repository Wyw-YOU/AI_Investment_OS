# Sprint 5-6: Agent Foundation - 代码生成指南

基于dev-timeline规划和multi-agent-developer skill的完整开发指南

---

## Sprint概览

**Sprint名称**: Agent Foundation
**目标**: 建立Agent基础设施，实现第一个参考Agent (News Agent)
**预计时间**: 3周 (15个工作日)
**交付物**: BaseAgent, LangGraph基础, News Agent, 测试套件

---

## 任务分解与代码生成

### 任务1: BaseAgent实现 (Day 1-2)

**设计规格** (来自开发文档):
- 抽象基类，定义标准接口
- LLM集成层（支持OpenAI/Anthropic）
- 输出解析和验证（Pydantic V2）
- 错误处理和重试机制
- 置信度计算框架

**代码生成指令**:

```markdown
## 任务: 实现AI Investment OS的BaseAgent

### 背景
AI Investment OS是一个Multi-Agent投资研究系统，需要实现8个专门化的Agent。
BaseAgent是所有Agent的基础类，定义了统一的接口和通用功能。

### 参考资源
基于multi-agent-developer skill的以下文档:
- **agent-templates.md**: "LLM-Powered Agent Template" 章节
- **state-management.md**: "State Design Principles" 章节
- **开发规范**: Python 3.11+, Pydantic V2, SQLAlchemy 2.0

### 具体要求

1. **类结构**:
   - 继承自ABC抽象基类
   - 必需属性: name (str), description (str)
   - 核心方法: run(state: dict) -> AgentOutput
   - 辅助方法: build_prompt(), parse_response(), _call_llm()

2. **AgentOutput模型** (Pydantic):
   - agent_name: str
   - result: Dict[str, Any]
   - confidence: float (0.0-1.0, with validator)
   - citations: List[str]
   - metadata: Dict[str, Any] = {}
   - timestamp: datetime

3. **LLM集成**:
   - 支持OpenAI和Anthropic
   - 使用环境变量配置API keys
   - 实现retry_with_backoff装饰器
   - 支持temperature和max_tokens配置

4. **Prompt构建** (CRAFT框架):
   - build_prompt()方法使用CRAFT结构
   - 支持动态context注入
   - 包含角色定义、任务说明、输出格式

5. **输出解析**:
   - parse_response()方法从LLM响应提取JSON
   - 处理markdown代码块
   - 验证必需字段
   - 提供默认值和错误处理

6. **错误处理**:
   - 自定义异常: AgentExecutionError, AgentTimeoutError
   - 所有LLM调用包含try-catch
   - Fallback机制确保workflow不崩溃
   - 详细的日志记录

7. **AI Investment OS特定**:
   - 遵循分层架构: Agent层 → Service层 → Domain层
   - Agent不直接写数据库
   - 所有输出必须可追溯（包含citations）
   - 状态管理使用Workspace模式

### 输出文件

生成以下文件:

#### 1. `base_agent.py`
完整的BaseAgent实现，包含:
- BaseAgent抽象类
- LLMAgent具体类（带LLM集成）
- AgentOutput Pydantic模型
- 所有辅助方法
- 错误处理和重试机制

#### 2. `exceptions.py`
自定义异常类:
- AgentExecutionError
- AgentTimeoutError
- AgentValidationError

#### 3. `test_base_agent.py`
单元测试:
- 测试AgentOutput验证
- 测试prompt构建
- 测试输出解析
- 测试错误处理
- Mock LLM调用

### 代码规范

- Python 3.11+ 语法
- Type hints完整
- Docstring清晰
- 遵循PEP 8
- 使用Pydantic V2语法

### 示例输出结构

```python
# base_agent.py 应该包含:

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, validator
from typing import Any, Optional, Dict, List
from datetime import datetime
import logging
import json

class AgentOutput(BaseModel):
    """标准Agent输出格式"""
    agent_name: str
    result: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    citations: List[str] = []
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v

class BaseAgent(ABC):
    """Agent抽象基类"""

    name: str
    description: str

    @abstractmethod
    def run(self, state: dict) -> AgentOutput:
        pass

    # ... 其他方法

class LLMAgent(BaseAgent):
    """LLM驱动的Agent基类"""

    def __init__(self, model="gpt-4", temperature=0.7, max_tokens=2000):
        # LLM初始化
        pass

    def run(self, state: dict) -> AgentOutput:
        # 完整的执行流程
        pass

    # ... 其他方法
```

### 验收标准

- [ ] BaseAgent抽象类正确定义
- [ ] AgentOutput包含所有必需字段和验证器
- [ ] LLM调用包含重试机制
- [ ] Prompt构建遵循CRAFT框架
- [ ] 输出解析健壮（处理各种格式）
- [ ] 错误处理完整（不崩溃workflow）
- [ ] 单元测试覆盖率 > 90%
- [ ] 符合AI Investment OS编码规范
```

---

### 任务2: LangGraph Workflow基础 (Day 3)

**设计规格** (来自开发文档):
- StateGraph定义
- InvestmentState TypedDict
- 基础节点结构
- 并行执行模式

**代码生成指令**:

```markdown
## 任务: 创建AI Investment OS的LangGraph基础Workflow

### 背景
需要建立LangGraph工作流基础，支持多Agent并行执行。
参考SAD文档中的Agent Engine架构。

### 参考资源
- **workflow-patterns.md**: "Parallel Fan-Out/Fan-In Pattern"
- **state-management.md**: "TypedDict (LangGraph Standard)"
- **系统架构设计文档**: Agent Engine章节

### 具体要求

1. **InvestmentState定义** (TypedDict):
   - stock_code: str
   - workspace_id: str
   - market_data: Dict[str, Any]
   - news_data: List[Dict]
   - financials: Dict[str, Any]
   - price_history: List[Dict]
   - agent_outputs: Dict[str, AgentOutput] (使用Annotated确保并行安全)
   - risk_assessment: Optional[Dict]
   - final_report: Optional[Dict]
   - errors: List[str]
   - status: str

2. **Workflow结构**:
   ```
   START
     ↓
   Planner Agent
     ↓
   [Parallel Fan-Out]
   ├── News Agent
   ├── Financial Agent
   ├── Technical Agent
   └── Macro Agent
     ↓
   [Fan-In Merge]
     ↓
   Risk Agent
     ↓
   Quant Agent
     ↓
   Report Agent
     ↓
   END
   ```

3. **节点实现**:
   - 每个节点是函数，接收state返回partial state
   - 使用`_make_agent_node()`工厂函数
   - 包含执行状态追踪
   - 错误处理和fallback

4. **并行执行**:
   - 使用LangGraph的fan-out/fan-in模式
   - `Annotated[list, operator.add]`收集并行结果
   - 所有并行agents完成后才进入下一阶段

5. **错误处理**:
   - safe_agent_run包装器
   - 单个agent失败不崩溃workflow
   - 降级策略（跳过失败agent继续）

6. **AI Investment OS特定**:
   - 遵循DDD中的Workflow设计
   - 支持条件路由（根据stock特征选择agents）
   - 状态可持久化到Workspace
   - 支持WebSocket进度推送

### 输出文件

#### 1. `workflow.py`
完整的工作流定义:
- InvestmentState TypedDict
- WorkflowOrchestrator类
- 所有节点函数
- 工作流编译和执行方法

#### 2. `nodes.py`
所有agent节点的实现:
- planner_node()
- news_agent_node()
- financial_agent_node()
- technical_agent_node()
- macro_agent_node()
- risk_agent_node()
- quant_agent_node()
- report_agent_node()
- merge_node()

#### 3. `test_workflow.py`
集成测试:
- 测试完整workflow执行
- 测试并行执行
- 测试错误处理
- 测试条件路由

### 代码示例

```python
# workflow.py 应该包含:

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class InvestmentState(TypedDict):
    stock_code: str
    market_data: Dict[str, Any]
    agent_outputs: Annotated[Dict[str, AgentOutput], merge_outputs]
    # ... 其他字段

def create_workflow() -> StateGraph:
    workflow = StateGraph(InvestmentState)

    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("news", news_agent_node)
    workflow.add_node("financial", financial_agent_node)
    workflow.add_node("technical", technical_agent_node)
    workflow.add_node("macro", macro_agent_node)
    workflow.add_node("merge", merge_node)
    workflow.add_node("risk", risk_agent_node)
    workflow.add_node("quant", quant_agent_node)
    workflow.add_node("report", report_agent_node)

    # 定义边（Fan-Out/Fan-In）
    workflow.add_edge("planner", "news")
    workflow.add_edge("planner", "financial")
    workflow.add_edge("planner", "technical")
    workflow.add_edge("planner", "macro")

    workflow.add_edge("news", "merge")
    workflow.add_edge("financial", "merge")
    workflow.add_edge("technical", "merge")
    workflow.add_edge("macro", "merge")

    workflow.add_edge("merge", "risk")
    workflow.add_edge("risk", "quant")
    workflow.add_edge("quant", "report")
    workflow.add_edge("report", END)

    workflow.set_entry_point("planner")

    return workflow

# 编译和运行
app = create_workflow().compile()
result = app.invoke(initial_state)
```

### 验收标准

- [ ] InvestmentState包含所有必需字段
- [ ] Workflow正确使用Fan-Out/Fan-In模式
- [ ] 并行执行真正并行（不是串行）
- [ ] 错误处理确保workflow不崩溃
- [ ] 状态转换可追踪
- [ ] 集成测试通过
- [ ] 符合LangGraph最佳实践
```

---

### 任务3: News Agent实现 (Day 4-7)

**设计规格** (来自开发文档):
- 新闻情绪分析
- 事件提取
- 影响评估
- 结构化输出

**代码生成指令**:

```markdown
## 任务: 实现AI Investment OS的News Agent

### 背景
News Agent是第一个实现的专门化Agent，作为参考实现。
负责分析金融新闻，提取情绪、事件和风险信息。

### 参考资源
- **agent-templates.md**: "LLM-Powered Agent Template" 和 "News Agent" 示例
- **prompt-templates.md**: "News Analysis Prompt" 和 "Domain-Specific Prompt Templates"
- **详细设计文档**: News Agent规格

### 具体要求

1. **继承LLMAgent基类**
   - 使用CRAFT框架设计prompt
   - 实现专业化的新闻分析逻辑
   - 包含领域特定的知识

2. **NewsAgentOutput模型**:
   - sentiment: str (bullish/bearish/neutral)
   - sentiment_score: float (-1.0 to 1.0)
   - events: List[Event] (title, impact, affected_stocks, summary)
   - risk_factors: List[str]
   - key_quotes: List[str]
   - sources: List[Source] (url, title, publish_date, credibility)

3. **Prompt设计** (CRAFT框架):
   ```
   [ROLE]
   你是一位资深的金融新闻分析师，拥有20年的市场研究经验...

   [CONTEXT]
   股票代码: {stock_code}
   新闻数据: {news_data}
   市场环境: {market_context}

   [TASK]
   分析提供的新闻数据，提取:
   1. 整体情绪评估 (bullish/bearish/neutral)
   2. 情绪强度评分 (-1.0到1.0)
   3. 关键事件列表
   4. 风险因素识别
   5. 重要引言

   [OUTPUT FORMAT]
   {严格的JSON格式}

   [EXAMPLES]
   {输入输出示例}

   [CONSTRAINTS]
   - 基于数据事实，不编造信息
   - 区分事实和观点
   - 评估来源可信度
   - 提供引用来源
   ```

4. **情绪分析逻辑**:
   - 综合考虑标题、正文、来源
   - 使用加权评分系统
   - 考虑新闻时效性
   - 识别矛盾信号

5. **事件提取**:
   - 识别重大事件类型（财报、并购、政策等）
   - 评估事件影响程度
   - 关联受影响的股票
   - 提取时间线

6. **置信度计算**:
   - 基于新闻数量和质量
   - 考虑来源可信度
   - 情绪一致性评估
   - 数据完整性检查

7. **AI Investment OS特定**:
   - 输出用于Risk Agent和Report Agent
   - 支持Workspace持久化
   - 包含数据溯源信息
   - 支持实时新闻流处理

### 输出文件

#### 1. `news_agent.py`
完整的News Agent实现:
- NewsAgent类继承LLMAgent
- 所有业务逻辑方法
- 置信度计算
- 错误处理

#### 2. `prompts.py`
News Agent的prompt模板:
- build_news_prompt()函数
- CRAFT框架结构
- 动态context注入
- Few-shot示例

#### 3. `schemas.py`
News相关的数据模型:
- NewsAgentOutput
- Event
- Source
- Sentiment枚举

#### 4. `test_news_agent.py`
全面的测试:
- 单元测试agent逻辑
- Mock LLM响应测试
- 边界条件测试
- 错误场景测试

### 代码示例

```python
# news_agent.py 应该包含:

class NewsAgent(LLMAgent):
    """新闻分析Agent"""

    name = "news_agent"
    description = "金融新闻情绪分析和事件提取专家"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, state: dict) -> AgentOutput:
        """执行新闻分析"""
        try:
            # 1. 构建prompt
            prompt = self.build_prompt(state)

            # 2. 调用LLM
            response = self._call_llm(prompt)

            # 3. 解析输出
            parsed = self.parse_response(response)

            # 4. 计算置信度
            confidence = self._calculate_confidence(parsed, state)

            # 5. 提取引用
            citations = self._extract_citations(parsed, state)

            return AgentOutput(
                agent_name=self.name,
                result=parsed,
                confidence=confidence,
                citations=citations,
                metadata={"model": self.model}
            )

        except Exception as e:
            self.logger.error(f"News analysis failed: {e}")
            return self._create_fallback_output(state, str(e))

    def build_prompt(self, state: dict) -> str:
        """构建新闻分析prompt"""
        return build_news_prompt(
            stock_code=state.get("stock_code"),
            news_data=state.get("news_data", []),
            market_context=state.get("market_data", {})
        )

    def _calculate_confidence(self, result: dict, state: dict) -> float:
        """计算置信度"""
        factors = []

        # 新闻数量因子
        news_count = len(state.get("news_data", []))
        factors.append(min(news_count / 10, 1.0) * 0.3)

        # 来源质量因子
        sources = result.get("sources", [])
        avg_credibility = sum(s.get("credibility", 0.5) for s in sources) / max(len(sources), 1)
        factors.append(avg_credibility * 0.3)

        # 情绪一致性因子
        sentiment_score = abs(result.get("sentiment_score", 0))
        factors.append(sentiment_score * 0.4)

        return sum(factors)

    def _create_fallback_output(self, state: dict, error: str) -> AgentOutput:
        """创建fallback输出"""
        return AgentOutput(
            agent_name=self.name,
            result={
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "events": [],
                "risk_factors": [],
                "error": error
            },
            confidence=0.1,
            citations=[]
        )
```

### 验收标准

- [ ] NewsAgent正确继承LLMAgent
- [ ] Prompt遵循CRAFT框架
- [ ] 输出包含所有必需字段
- [ ] 情绪分析逻辑合理
- [ ] 事件提取准确
- [ ] 置信度计算有依据
- [ ] 引用追踪完整
- [ ] 错误处理健壮
- [ ] 单元测试通过
- [ ] 集成测试与workflow兼容
```

---

### 任务4: 集成和测试 (Day 8-9)

**代码生成指令**:

```markdown
## 任务: 集成所有组件并进行端到端测试

### 背景
BaseAgent、LangGraph基础和News Agent已经实现。
现在需要集成所有组件并进行全面测试。

### 测试策略

1. **单元测试** (已有)
   - 测试各个组件独立功能

2. **集成测试** (新建)
   - 测试BaseAgent + NewsAgent集成
   - 测试NewsAgent + Workflow集成
   - 测试完整的workflow执行流程

3. **端到端测试** (新建)
   - 模拟真实的股票分析场景
   - 使用mock数据测试完整流程
   - 验证输出格式和质量

### 测试场景

#### 场景1: 单Agent测试
```python
def test_news_agent_independently():
    """测试News Agent独立运行"""
    agent = NewsAgent()
    state = {
        "stock_code": "000001",
        "news_data": [
            {"title": "平安银行发布Q4财报，净利润增长15%", "source": "证券时报"},
            {"title": "银行板块今日上涨2%", "source": "东方财富"}
        ]
    }

    result = agent.run(state)

    assert result.agent_name == "news_agent"
    assert result.confidence > 0
    assert "sentiment" in result.result
    assert "events" in result.result
```

#### 场景2: Workflow集成测试
```python
def test_workflow_with_news_agent():
    """测试包含News Agent的workflow"""
    workflow = create_workflow()
    app = workflow.compile()

    state = {
        "stock_code": "000001",
        "market_data": {...},
        "news_data": [...]
    }

    result = app.invoke(state)

    assert "news_agent" in result["agent_outputs"]
    assert result["agent_outputs"]["news_agent"].confidence > 0
```

#### 场景3: 错误处理测试
```python
def test_workflow_with_failed_agent():
    """测试单个agent失败时的workflow行为"""
    # Mock News Agent失败
    with patch('news_agent.NewsAgent.run', side_effect=Exception("API Error")):
        result = app.invoke(state)

    # Workflow应该继续执行，News Agent使用fallback输出
    assert "news_agent" in result["agent_outputs"]
    assert result["agent_outputs"]["news_agent"].confidence == 0.1
    assert len(result["errors"]) > 0
```

### 输出文件

#### 1. `test_integration.py`
完整的集成测试套件:
- Agent独立测试
- Workflow集成测试
- 错误处理测试
- 性能测试

#### 2. `conftest.py`
测试fixtures:
- Mock LLM responses
- Sample market data
- Sample news data
- Helper functions

#### 3. `run_tests.sh` 或 `Makefile`
测试运行脚本

### 验收标准

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码覆盖率 > 80%
- [ ] 错误处理测试通过
- [ ] 性能测试通过（无内存泄漏）
- [ ] 文档更新
```

---

## 开发检查清单

### Sprint 5-6 完成标准

- [ ] BaseAgent类完整实现
- [ ] AgentOutput模型定义正确
- [ ] LLM集成工作正常
- [ ] LangGraph workflow可运行
- [ ] News Agent实现完成
- [ ] 所有测试通过
- [ ] 代码符合规范
- [ ] 文档更新

### 代码质量检查

- [ ] Type hints完整
- [ ] Docstring清晰
- [ ] 无代码重复
- [ ] 错误处理完整
- [ ] 日志记录充分
- [ ] 性能可接受

### 集成检查

- [ ] Agent与Workflow兼容
- [ ] 状态管理正确
- [ ] 并行执行正常
- [ ] 错误传播正确
- [ ] 输出格式一致

---

## 下一步: Sprint 7-8

完成Sprint 5-6后，可以开始Sprint 7-8: Agent Fleet

**任务预览**:
1. Financial Agent (基于News Agent模式)
2. Technical Agent
3. Macro Agent
4. Risk Agent
5. Agent集成测试
6. Workflow优化

每个Agent的实现都将参考News Agent的模式，确保代码一致性。

---

## 资源链接

- **multi-agent-developer skill**: Agent模板和最佳实践
- **dev-timeline skill**: 开发周期规划
- **AI Investment OS开发文档**: 详细设计规格
- **LangGraph文档**: Workflow框架参考

---

*使用这个指南，你可以在3周内完成Sprint 5-6的所有交付物。*
