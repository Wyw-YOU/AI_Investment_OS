# Multi-Agent Developer + Dev-Timeline 集成快速开始

将开发规划转化为可运行代码的一键式工作流

---

## 🎯 你将获得什么

✅ **从规划到代码的自动化转化**
✅ **基于Sprint的渐进式开发**
✅ **AI Investment OS特定的开发模板**
✅ **完整的代码生成和验证流程**

---

## 🚀 5分钟快速开始

### 场景1: 开始新的Sprint开发

**你可以说：**

```markdown
我要开始Sprint 5-6: Agent Foundation的开发

请帮我：
1. 分解具体任务
2. 生成BaseAgent的代码
3. 创建News Agent的实现
4. 建立LangGraph工作流基础
```

**工作流程：**

1. **dev-timeline** 规划Sprint任务和时间线
2. **multi-agent-developer** 生成具体代码
3. 你获得完整的可运行代码和测试

---

### 场景2: 实现特定Agent

**你可以说：**

```markdown
帮我实现AI Investment OS的Financial Agent

要求：
1. 基本面分析（PE, ROE, 收入增长等）
2. 结构化JSON输出
3. 与现有workflow集成
4. 包含完整的测试
```

**你会得到：**
- financial_agent.py (完整实现)
- prompts.py (专业prompt模板)
- schemas.py (数据模型)
- test_financial_agent.py (测试套件)

---

### 场景3: 创建Workflow

**你可以说：**

```markdown
基于LangGraph创建投资分析workflow

包含：
- Planner Agent
- News Agent (并行)
- Financial Agent (并行)
- Technical Agent (并行)
- Risk Agent
- Report Agent

使用Fan-Out/Fan-In并行模式
```

**你会得到：**
- workflow.py (完整workflow定义)
- nodes.py (所有节点实现)
- test_workflow.py (集成测试)

---

## 📋 完整开发示例

### 示例：从零开始实现News Agent

#### Step 1: 规划任务

```python
# 你说：
"""
我想实现AI Investment OS的News Agent
这是Sprint 5-6的一部分

请帮我规划这个任务的开发步骤
"""
```

**dev-timeline输出：**
```
## News Agent开发计划

**复杂度**: High
**预计时间**: 5-7天

### 任务分解：
1. 数据层设置 (1-2天)
   - News API集成
   - 数据库schema
   - 向量embedding

2. Agent核心逻辑 (2-3天)
   - Prompt工程
   - 情绪分析
   - 事件提取
   - 输出解析

3. 集成 (1-2天)
   - LangGraph节点
   - 状态管理
   - 错误处理

4. 测试 (1天)
   - 单元测试
   - 集成测试
   - Mock测试
```

#### Step 2: 生成代码

```python
# 你说：
"""
基于multi-agent-developer skill，生成News Agent的代码

参考：
- agent-templates.md中的LLMAgent Template
- prompt-templates.md中的News Analysis Prompt
- sprint-5-6-guide.md中的具体要求

要求：
1. 新闻情绪分析
2. 事件提取
3. 结构化JSON输出
4. 置信度评分
5. 引用追踪

生成文件：
- news_agent.py
- prompts.py
- schemas.py
- test_news_agent.py
"""
```

**multi-agent-developer输出：**

```python
# news_agent.py
class NewsAgent(LLMAgent):
    """金融新闻分析Agent"""

    name = "news_agent"
    description = "金融新闻情绪分析和事件提取专家"

    def run(self, state: dict) -> AgentOutput:
        # 1. 构建prompt (CRAFT框架)
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
            citations=citations
        )

    def build_prompt(self, state: dict) -> str:
        return build_news_prompt(
            stock_code=state.get("stock_code"),
            news_data=state.get("news_data", []),
            market_context=state.get("market_data", {})
        )

# ... 完整实现
```

#### Step 3: 验证和集成

```python
# 你说：
"""
请验证生成的News Agent代码

检查：
1. 是否符合设计规格
2. 测试是否通过
3. 是否与workflow兼容
4. 是否遵循最佳实践
"""
```

**验证结果：**
```
✅ 代码验证通过

1. 继承LLMAgent基类 ✓
2. 使用CRAFT prompt框架 ✓
3. 输出包含置信度和引用 ✓
4. 错误处理完整 ✓
5. 单元测试通过 (15/15) ✓
6. 与workflow集成测试通过 ✓

可以开始下一步开发
```

---

## 🔧 常用命令模板

### 命令1: 实现Agent

```markdown
基于multi-agent-developer skill，实现AI Investment OS的[Agent名称]。

背景：这是[Sprint X-Y]的一部分
设计规格：来自[详细设计文档章节]

要求：
1. [具体要求1]
2. [具体要求2]
3. [具体要求3]

使用的skill资源：
- agent-templates.md: [具体模板]
- prompt-templates.md: [具体prompt类型]

输出文件：
- [文件1]
- [文件2]
- [测试文件]
```

### 命令2: 创建Workflow

```markdown
基于multi-agent-developer skill的workflow-patterns.md，创建[Workflow名称]。

使用[具体模式名称]模式

包含以下agents：
1. [Agent1]
2. [Agent2]
3. [Agent3]

执行模式：[并行/串行/条件]

输出：workflow.py
```

### 命令3: 设计Prompt

```markdown
基于multi-agent-developer skill的prompt-templates.md，设计[Agent名称]的prompt。

使用CRAFT框架
领域：[投资分析/新闻分析/风险评估等]

参考prompt-templates.md中的[具体模板名称]

要求：
1. [具体要求1]
2. [具体要求2]

输出：prompts.py
```

---

## 📚 Sprint开发路线图

### Sprint 1-2: Foundation (第1-3周)
**目标**: 项目基础设置

```markdown
我要开始Sprint 1-2: Foundation的开发

任务：
1. 项目结构设置 (monorepo)
2. Docker配置
3. 数据库migrations
4. 基础API框架
5. 认证系统

请帮我规划并生成代码
```

### Sprint 3-4: Core Services (第4-6周)
**目标**: 核心业务服务

```markdown
我要开始Sprint 3-4: Core Services

任务：
1. Stock Service
2. Workspace Service
3. 前端框架

请帮我实现这些服务
```

### Sprint 5-6: Agent Foundation (第7-9周) ⭐
**目标**: Agent基础设施

```markdown
我要开始Sprint 5-6: Agent Foundation

任务：
1. BaseAgent类
2. LangGraph工作流基础
3. News Agent (参考实现)

请生成完整的Agent框架代码
```

**参考**: sprint-5-6-guide.md

### Sprint 7-8: Agent Fleet (第10-12周)
**目标**: 完整的Agent团队

```markdown
我要开始Sprint 7-8: Agent Fleet

任务：
1. Financial Agent
2. Technical Agent
3. Macro Agent
4. Risk Agent

基于News Agent模式，批量生成这些Agents
```

### Sprint 9-10: Advanced Features (第13-15周)
**目标**: 高级功能

```markdown
我要开始Sprint 9-10: Advanced Features

任务：
1. Quant Agent
2. Report Agent
3. RAG集成
4. 多Agent编排优化

请实现这些高级功能
```

### Sprint 11-12: Integration & Polish (第16-18周)
**目标**: 集成和优化

```markdown
我要开始Sprint 11-12: Integration & Polish

任务：
1. Candidate Pool自动化
2. Strategy Center
3. 报告生成
4. 前端优化

请帮我集成所有模块
```

### Sprint 13-14: Testing & Deployment (第19-20周)
**目标**: 测试和部署

```markdown
我要开始Sprint 13-14: Testing & Deployment

任务：
1. 端到端测试
2. 性能优化
3. 安全审计
4. 生产部署

请帮我准备生产环境
```

---

## 💡 最佳实践

### 1. 渐进式开发

```
单个Agent → Agent组合 → 完整Workflow → 系统集成
```

**建议**：
- 从News Agent开始，建立模式
- 然后实现其他Agent，复用模式
- 最后集成完整workflow

### 2. 测试驱动

```
先写测试 → 生成代码 → 验证通过 → 下一个任务
```

**建议**：
- 每个Agent都要有单元测试
- 每个Workflow都要有集成测试
- 保持高测试覆盖率

### 3. 模式复用

```
BaseAgent模式 → 所有Agent复用
News Agent模式 → 其他Agent参考
Workflow模式 → 不同场景复用
```

**建议**：
- 建立代码模板库
- 记录最佳实践
- 持续优化模式

### 4. 文档同步

```
代码实现 → 更新文档 → 保持同步
```

**建议**：
- 代码和文档同时生成
- 记录设计决策
- 维护API文档

---

## 🆘 常见问题

### Q1: 如何开始第一个Agent？

```markdown
推荐从News Agent开始：

1. 参考sprint-5-6-guide.md
2. 使用agent-templates.md中的LLMAgent Template
3. 使用prompt-templates.md中的News Analysis Prompt
4. 包含完整的测试

这个Agent将作为其他Agent的参考实现
```

### Q2: 如何确保代码质量？

```markdown
使用multi-agent-developer skill会自动确保：
- ✅ 遵循BaseAgent模式
- ✅ 使用CRAFT prompt框架
- ✅ 包含置信度和引用
- ✅ 完整的错误处理
- ✅ 全面的测试覆盖

同时参考开发规范文档确保符合项目标准
```

### Q3: 如何处理Agent间的依赖？

```markdown
按顺序实现：
1. BaseAgent (所有Agent的基础)
2. News Agent (参考实现)
3. Financial Agent (复用模式)
4. Technical Agent (复用模式)
5. Risk Agent (依赖前面的输出)
6. Report Agent (依赖所有Agent)

workflow-patterns.md包含处理依赖的模式
```

### Q4: 如何集成到现有系统？

```markdown
每个生成的模块都包含：
1. 清晰的接口定义
2. 标准化的输入输出
3. 完整的集成测试
4. 详细的集成文档

参考development-integration.md了解集成流程
```

---

## 📞 获取帮助

### 需要帮助时可以说：

```markdown
# 任务规划
"帮我规划Sprint [X-Y]的开发任务"

# 代码生成
"基于multi-agent-developer skill生成[模块名称]"

# 问题解决
"[模块名称]遇到了[具体问题]，请帮我解决"

# 代码审查
"请审查我实现的[模块名称]代码"

# 最佳实践
"实现[功能]的最佳实践是什么？"
```

---

## ✨ 开始你的第一个Sprint

现在就开始吧！试试这个：

```markdown
我要开始Sprint 5-6: Agent Foundation的开发

请帮我：
1. 分解具体任务和时间估算
2. 生成BaseAgent的完整代码
3. 创建News Agent的实现
4. 建立LangGraph工作流基础
5. 包含完整的测试套件

参考sprint-5-6-guide.md和multi-agent-developer skill的所有资源
```

---

## 🎉 你将获得

✅ **完整的Sprint计划** - 任务分解、时间估算、依赖关系
✅ **生产级代码** - 符合AI Investment OS规范
✅ **全面的测试** - 单元测试和集成测试
✅ **详细的文档** - 设计决策和使用说明
✅ **集成指南** - 如何与现有系统集成

**开发效率提升50%以上！** 🚀

---

*这个快速开始指南将帮助你立即开始使用multi-agent-developer skill进行AI Investment OS的开发。*
