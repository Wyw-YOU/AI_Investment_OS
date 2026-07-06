---
name: bug-hunter
description: >
  代码审核、测试与 bug 修复 skill。在沙盒（worktree）中独立运行测试和静态分析，
  输出结构化 bug 列表供用户审阅，用户确认后再修复。当用户提到"找bug"、"代码审核"、
  "review"、"测试"、"audit"、"检查代码"、"test"、"docker报错"、"部署失败"、
  "容器起不来"时触发。
  即使用户没明确说"bug"，只要意图是排查代码问题、验证代码质量、或修复部署问题，也应触发。
---

# Bug Hunter — 代码审核、测试与修复

## 核心流程

```
1. 创建沙盒 (worktree)
2. 代码审核 + 运行测试
3. 输出结构化 bug 列表
4. 等待用户确认
5. 逐个修复已确认的 bug
```

## 第一步：创建沙盒环境

用 `EnterWorktree` 创建独立的 git worktree，所有测试和分析都在沙盒中进行，
不污染用户的工作分支。

```
EnterWorktree name="bug-hunter-sandbox"
```

进入沙盒后，先确认环境可用：

**后端：**
```bash
cd backend && pip install -r requirements.txt -q && python -c "import app; print('backend OK')"
```

**前端：**
```bash
cd frontend && npm install --silent && npx next build 2>&1 | tail -20
```

若环境准备失败，在 bug 列表中注明"环境问题"并继续静态分析。

## 第二步：代码审核（静态分析）

按以下维度逐文件扫描，每个维度给出独立发现：

### 2.1 运行时错误风险
- 未处理的 `None` / `Optional` 访问（`x.y` 当 `x` 可能为 `None`）
- 索引越界：`list[0]` 未检查是否为空
- 类型混淆：Pydantic schema 和 SQLAlchemy model 字段类型不匹配
- `await` 缺失：async 函数内调用了 async 函数但没 `await`

### 2.2 安全问题
- SQL 注入（字符串拼接 SQL，而非参数化查询）
- 硬编码密钥、token、密码
- CORS 配置过于宽松（`allow_origins=["*"]` 在生产环境）
- JWT secret 使用弱默认值
- 敏感信息出现在日志输出中

### 2.3 逻辑错误
- 异常被静默吞掉（`except: pass` 或 `except Exception` 不记录日志）
- 条件判断永远为真或为假
- 循环变量在循环内被意外覆盖
- 函数返回值未被使用（应返回但没有 return）

### 2.4 架构/设计问题
- 循环导入
- 全局可变状态
- 函数参数过多（>6个）
- 过长函数（>100行）

### 2.5 前端特有
- `useEffect` 缺少依赖项
- 状态更新在组件卸载后发生（内存泄漏）
- `any` 类型滥用
- 事件监听器未清理
- 服务端组件与客户端组件混用（`"use client"` 标注问题）

### 2.6 Docker 部署检查
- Dockerfile 语法错误（`COPY` 路径不存在、`RUN` 命令失败）
- 基础镜像版本不一致或已过时
- `docker-compose.yml` 中服务端口与 Dockerfile `EXPOSE` 不匹配
- 环境变量在 `.env.example` 中有定义但 `docker-compose.yml` 未传递
- 服务启动顺序依赖（如 backend 依赖 redis 但没设 `depends_on`）
- `healthcheck` 缺失或命令错误
- `.dockerignore` 缺失导致构建上下文过大或误排除关键文件
- 多阶段构建中产物路径错误
- 容器内文件权限问题（非 root 用户无法写入目录）
- 数据卷挂载路径与容器内路径不一致

## 第三步：运行测试

在沙盒中实际运行测试，捕获失败和警告：

```bash
# 后端单元测试
cd backend && python -m pytest tests/ -v --tb=short 2>&1

# 前端类型检查和构建
cd frontend && npx tsc --noEmit 2>&1 && npm run build 2>&1 | tail -30
```

测试失败 = bug，但测试通过 ≠ 无 bug（静态分析仍需进行）。

### Docker 部署测试

当用户提到部署问题或 docker 时，额外运行：

```bash
# 构建所有服务镜像（捕获构建阶段错误）
docker-compose build --no-cache 2>&1

# 拉起所有服务（捕获启动阶段错误）
docker-compose up -d 2>&1

# 等待服务稳定后检查状态
sleep 10 && docker-compose ps

# 查看各服务日志，定位具体报错
docker-compose logs backend 2>&1 | tail -50
docker-compose logs frontend 2>&1 | tail -50
docker-compose logs redis 2>&1 | tail -30

# 验证服务是否正常响应
curl -s http://localhost:8000/health || echo "backend unreachable"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "frontend unreachable"
```

**Docker 报错分类：**
- 构建失败（`docker-compose build` 报错）→ 检查 Dockerfile、依赖、COPY 路径
- 启动失败（容器 exit code 非 0）→ 检查入口命令、环境变量、端口冲突
- 运行时崩溃（容器频繁 restart）→ 检查日志、健康检查、服务间连接
- 网络问题（服务间不通）→ 检查 docker-compose networks、depends_on、端口映射

## 第四步：输出 bug 列表

按以下格式输出，用户可以逐条审阅：

```
## Bug 列表

### BUG-001 [严重] 🔴
- **文件**: backend/app/api/auth.py:45
- **问题**: JWT token 过期时间设置为 0，导致所有 token 立即失效
- **原因**: `timedelta(days=0)` 应为 `timedelta(days=7)`
- **复现**: 登录后立即访问受保护接口，返回 401

### BUG-002 [高] 🟠
- **文件**: backend/app/services/market_data.py:112
- **问题**: akshare 接口异常时未处理，导致整个分析流程崩溃
- **原因**: 缺少 try-except，网络超时直接抛出到 API 层

### BUG-003 [中] 🟡
- **文件**: frontend/src/components/KlineChart.tsx:78
- **问题**: useEffect 依赖项缺失，stockCode 变化后图表不更新
- **原因**: 依赖数组应包含 [stockCode] 但为空 []

### BUG-004 [低] 🟢
- **文件**: backend/app/config.py:15
- **问题**: CORS allow_origins 在 .env.example 中硬编码为 *
- **原因**: 示例配置应使用具体域名
```

**严重等级说明：**
- 🔴 **严重**：功能完全不可用，数据丢失，安全漏洞
- 🟠 **高**：核心功能异常，用户体验严重受损
- 🟡 **中**：非核心功能问题，有变通方案
- 🟢 **低**：代码质量、潜在风险、最佳实践违规

输出 bug 列表后，**停止并等待用户确认**，不要自动修复。

## 第五步：修复已确认的 bug

用户确认要修复的 bug 后，按以下规则修复：

1. **逐个修复**，每修复一个都做一次验证
2. **修复后立即运行相关测试**，确认修复有效且不引入新问题
3. 修复顺序：严重 → 高 → 中 → 低
4. 若某个 bug 修复复杂度高，在修复前告知用户预期改动范围

修复完成后输出总结：
```
## 修复总结
- ✅ BUG-001: 已修复，pytest 通过
- ✅ BUG-002: 已修复，新增 3 个异常处理用例
- ⏭️ BUG-003: 用户选择暂不修复
```

## 第六步：退出沙盒

所有工作完成后，询问用户是否保留沙盒分支：
- `ExitWorktree action="keep"` — 保留沙盒，方便后续复查
- `ExitWorktree action="remove"` — 清理沙盒，合并回原分支

## 注意事项

- **不要修复未被用户确认的 bug**，即使你觉得很明显
- **不要修改测试用例来让测试通过**（除非测试本身有错）
- **不要引入新的依赖**，除非用户同意
- **保持修复最小化**，不要顺手重构或优化不相关代码
