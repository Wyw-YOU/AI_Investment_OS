# Development-to-Code Integration Guide

将开发周期规划转化为具体代码实现的工作流指南

---

## 概述

这个指南将**dev-timeline skill**的开发规划能力与**multi-agent-developer skill**的代码生成能力结合，实现从开发计划到可运行代码的自动化转化。

## 核心理念

**从规划到实现的一键转化：**

```
开发周期规划 (dev-timeline)
    ↓
Sprint任务分解
    ↓
模块设计规格
    ↓
代码生成 (multi-agent-developer)
    ↓
测试验证
    ↓
集成部署
```

---

## Sprint-Based 开发工作流

### 工作流程

每个Sprint的开发流程：

1. **规划阶段** (使用dev-timeline)
   - 确定Sprint目标和交付物
   - 识别依赖和风险
   - 分解任务到1-2天粒度

2. **设计阶段** (结合开发文档)
   - 提取详细设计规格
   - 定义接口和数据结构
   - 设计模块边界

3. **实现阶段** (使用multi-agent-developer)
   - 生成agent代码
   - 创建workflow实现
   - 实现状态管理

4. **验证阶段**
   - 运行测试
   - 验证集成
   - 性能测试

---

## Sprint 5-6: Agent Foundation (示例)

### Sprint目标
建立Agent基础设施，实现第一个参考Agent (News Agent)

### 任务分解

#### 任务1: Base Agent类实现 (1-2天)

**设计规格：**
- 继承自抽象基类
- 标准化接口：name, description, run()
- LLM集成层
- 输出解析和验证
- 错误处理和重试

**使用multi-agent-developer生成：**

```python
# 生成命令示例
"""
基于multi-agent-developer skill的agent-templates.md，实现AI Investment OS的BaseAgent类。

要求：
1. 使用BaseAgent Template模式
2. 包含LLM集成（支持OpenAI和Anthropic）
3. 实现AgentOutput Pydantic模型
4. 包含retry_with_backoff机制
5. 支持JSON输出解析
6. 实现置信度计算和引用追踪
7. 遵循AI Investment OS的编码规范（Python 3.11+, Pydantic V2）

输出：完整的base_agent.py文件，包含所有必要的类和方法
"""
```

#### 任务2: LangGraph Workflow基础 (1天)

**设计规格：**
- StateGraph定义
- AgentState TypedDict
- 基础节点和边配置
- 错误处理节点

**使用multi-agent-developer生成：**

```python
# 生成命令示例
"""
基于multi-agent-developer skill的workflow-patterns.md，创建AI Investment OS的基础LangGraph workflow。

要求：
1. 使用StateGraph定义工作流
2. 实现InvestmentState TypedDict（包含stock_code, market_data, agent_outputs等）
3. 定义基础节点结构（planner, agents, report）
4. 实现Fan-Out/Fan-In并行执行模式
5. 包含错误处理和fallback机制
6. 支持条件路由

参考workflow-patterns.md中的Parallel Fan-Out/Fan-In Pattern

输出：workflow.py文件，包含完整的workflow定义和基础节点
"""
```

#### 任务3: News Agent实现 (2-3天)

**设计规格：**
- 新闻情绪分析
- 事件提取
- 影响评估
- 结构化输出

**使用multi-agent-developer生成：**

```python
# 生成命令示例
"""
基于multi-agent-developer skill的prompt-templates.md和agent-templates.md，实现AI Investment OS的News Agent。

要求：
1. 继承自BaseAgent
2. 使用CRAFT prompt框架设计专业的金融新闻分析prompt
3. 实现NewsAgentOutput Pydantic模型（包含sentiment, events, risk_factors等）
4. 包含置信度计算（基于数据质量和来源可信度）
5. 实现引用追踪（来源URL、发布时间等）
6. 遵循AI Investment OS的Agent开发规范（结构化JSON输出、不编造数据）

参考prompt-templates.md中的News Analysis Prompt模板

输出：
- news_agent.py（Agent实现）
- prompts.py（prompt模板）
- schemas.py（输出数据结构）
"""
```

#### 任务4: 集成和测试 (1天)

**设计规格：**
- 单元测试
- 集成测试
- Mock数据测试

---

## 开发模板系统

### 模板1: Agent开发模板

```markdown
## Agent开发任务模板

### 基本信息
- **Agent名称**: [Agent名称]
- **所属领域**: [Investment Domain / Analytics Domain等]
- **Sprint**: [Sprint编号]
- **预计时间**: [X天]

### 设计规格
- **输入**: [State中的哪些字段]
- **输出**: [AgentOutput结构]
- **职责**: [具体功能描述]
- **依赖**: [其他Agent或服务]

### 使用的Skill资源
- [ ] agent-templates.md中的[具体模板名称]
- [ ] prompt-templates.md中的[具体prompt类型]
- [ ] workflow-patterns.md中的[具体模式]
- [ ] state-management.md中的[具体策略]

### 代码生成指令
```
基于multi-agent-developer skill，实现[Agent名称]。

参考资源：
- agent-templates.md: [具体章节]
- prompt-templates.md: [具体模板]
- [其他相关文档]

要求：
1. [具体要求1]
2. [具体要求2]
3. ...

输出文件：
- [文件1]
- [文件2]
```

### 验收标准
- [ ] Agent类正确继承BaseAgent
- [ ] Prompt结构符合CRAFT框架
- [ ] 输出包含置信度和引用
- [ ] 错误处理完整
- [ ] 单元测试通过
- [ ] 集成测试通过
```

### 模板2: Workflow开发模板

```markdown
## Workflow开发任务模板

### 基本信息
- **Workflow名称**: [名称]
- **包含Agents**: [Agent列表]
- **Sprint**: [Sprint编号]
- **预计时间**: [X天]

### 设计规格
- **执行模式**: [并行/串行/条件]
- **状态结构**: [AgentState定义]
- **错误策略**: [重试/fallback/降级]

### 使用的Skill资源
- workflow-patterns.md中的[具体模式]
- state-management.md中的[具体策略]

### 代码生成指令
```
基于multi-agent-developer skill，创建[Workflow名称]。

使用workflow-patterns.md中的[模式名称]模式

包含以下agents：
1. [Agent1]
2. [Agent2]
3. ...

要求：
1. [具体要求]

输出：workflow.py
```
```

### 模板3: Sprint交付物模板

```markdown
## Sprint [编号]: [Sprint名称]

### Sprint目标
[目标描述]

### 交付物清单
1. [ ] [交付物1] - [预计时间]
2. [ ] [交付物2] - [预计时间]
3. [ ] [交付物3] - [预计时间]

### 依赖关系
- [前置依赖]
- [外部依赖]

### 风险和缓解
- **风险1**: [描述] → [缓解措施]
- **风险2**: [描述] → [缓解措施]

### 代码生成任务
#### 任务1: [任务名称]
- **Skill资源**: [使用的资源]
- **生成指令**: [具体指令]
- **输出文件**: [文件列表]

#### 任务2: [任务名称]
...

### 验收标准
- [ ] [标准1]
- [ ] [标准2]
- [ ] 所有测试通过
- [ ] 代码审查完成
```

---

## 集成工作流示例

### 场景：实现Sprint 5-6的Agent Foundation

#### Step 1: 使用dev-timeline规划

```python
# 用户输入
"""
我想开始Sprint 5-6的开发：Agent Foundation

请帮我：
1. 分解这个Sprint的具体任务
2. 估算每个任务的时间
3. 识别依赖关系
4. 制定详细的开发计划
"""
```

#### Step 2: 生成Sprint计划

dev-timeline skill输出详细的Sprint计划，包括：
- 任务分解
- 时间估算
- 依赖图
- 里程碑

#### Step 3: 使用multi-agent-developer生成代码

对于每个任务，使用multi-agent-developer skill：

```python
# 任务1: 实现BaseAgent
"""
基于multi-agent-developer skill的agent-templates.md，实现AI Investment OS的BaseAgent。

要求：
1. 参考BaseAgent Template模式
2. 包含LLM集成层
3. 实现AgentOutput Pydantic模型
4. 包含错误处理和重试机制
5. 遵循AI Investment OS编码规范

请生成完整的base_agent.py文件
"""

# 任务2: 创建News Agent
"""
基于multi-agent-developer skill，实现News Agent。

参考：
- agent-templates.md: LLMAgent Template
- prompt-templates.md: News Analysis Prompt

要求：
1. 新闻情绪分析
2. 事件提取
3. 结构化JSON输出
4. 置信度评分
5. 引用追踪

请生成：
- news_agent.py
- prompts.py
- schemas.py
"""

# 任务3: 创建基础Workflow
"""
基于multi-agent-developer skill的workflow-patterns.md，创建基础workflow。

使用Parallel Fan-Out/Fan-In模式

包含：
- Planner节点
- News Agent节点
- Report节点
- 错误处理

请生成workflow.py
"""
```

#### Step 4: 验证和迭代

- 运行生成的测试
- 验证集成
- 根据反馈优化

---

## 高级功能

### 1. 智能代码补全

当用户正在编写代码时，skill可以：
- 识别正在实现的模块属于哪个Sprint
- 提供相关的模板和示例
- 建议下一步实现什么

### 2. 进度追踪

集成开发进度追踪：
- 自动记录已完成的任务
- 更新Sprint burndown
- 识别阻塞和风险

### 3. 依赖管理

自动管理模块依赖：
- 检查前置依赖是否完成
- 建议实现顺序
- 警告循环依赖

### 4. 代码质量检查

生成的代码自动检查：
- 符合AI Investment OS编码规范
- 包含必要的错误处理
- 有完整的测试覆盖
- 遵循DDD原则

---

## 使用示例

### 示例1: 开始新的Sprint

**用户输入：**
```
我要开始Sprint 7-8: Agent Fleet的开发
请帮我规划并生成Financial Agent的代码
```

**工作流程：**
1. dev-timeline生成Sprint 7-8详细计划
2. 识别Financial Agent的任务分解
3. multi-agent-developer生成agent代码
4. 创建测试和文档
5. 验证集成

### 示例2: 实现特定模块

**用户输入：**
```
帮我实现Risk Agent，包括：
- 风险评分系统
- 风险因子分析
- 与workflow的集成
```

**工作流程：**
1. 查找Risk Agent的设计规格
2. 使用multi-agent-developer生成代码
3. 参考risk相关的prompt模板
4. 创建测试用例
5. 验证与现有workflow的集成

### 示例3: 修复集成问题

**用户输入：**
```
News Agent和Financial Agent的输出格式不一致
请帮我统一它们的接口
```

**工作流程：**
1. 分析两个agent的输出结构
2. 设计统一的接口规范
3. 重构agent代码
4. 更新workflow适配
5. 运行集成测试

---

## 最佳实践

### 1. 渐进式开发
- 从单个agent开始，建立模式
- 逐步添加更多agent
- 最后集成完整workflow

### 2. 测试驱动
- 先写测试，再生成代码
- 保持高测试覆盖率
- 自动化回归测试

### 3. 文档同步
- 代码和文档同时生成
- 保持API文档更新
- 记录设计决策

### 4. 持续集成
- 每个Sprint结束时集成
- 自动化部署流程
- 监控生产环境

---

## 工具集成

### 与现有工具的集成

1. **Git集成**
   - 自动生成commit message
   - 创建feature分支
   - 管理PR

2. **CI/CD集成**
   - 自动运行测试
   - 代码质量检查
   - 自动部署

3. **项目管理集成**
   - 更新任务状态
   - 生成进度报告
   - 识别阻塞

---

## 下一步

1. **创建Sprint模板库** - 为每个Sprint预定义任务模板
2. **建立代码示例库** - 收集可复用的代码片段
3. **优化生成质量** - 根据实际使用反馈改进
4. **集成更多工具** - 支持更多开发工具和平台

---

## 快速开始

### 第一步：规划Sprint

```python
# 使用dev-timeline skill
"""
请帮我规划Sprint [X-Y]的开发任务
"""
```

### 第二步：生成代码

```python
# 使用multi-agent-developer skill
"""
基于multi-agent-developer skill，实现[模块名称]

参考：[具体资源]
要求：[具体要求]
"""
```

### 第三步：验证和迭代

```python
# 运行测试和验证
"""
请验证生成的代码并运行测试
"""
```

---

*这个集成指南将帮助你从开发规划无缝过渡到代码实现，最大化利用两个skill的协同效应。*
