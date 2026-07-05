# AI Investment OS — Phase 4 测试报告

**日期：** 2026-07-05
**阶段：** Phase 0-4（含前端 Dashboard UI）
**后端测试：** 83 passed, 0 failed
**前端状态：** 代码完成，npm install 需解决环境问题

---

## 目录

1. [Phase 4 新增内容概览](#1-phase-4-新增内容概览)
2. [前端代码审核](#2-前端代码审核)
3. [前端启动与测试](#3-前端启动与测试)
4. [页面功能测试](#4-页面功能测试)
5. [前后端联调测试](#5-前后端联调测试)
6. [预期结果速查表](#6-预期结果速查表)
7. [已发现的问题](#7-已发现的问题)
8. [遗留问题与建议](#8-遗留问题与建议)

---

## 1. Phase 4 新增内容概览

### 前端文件（17 个）

| 目录 | 文件 | 说明 |
|------|------|------|
| 根目录 | `package.json` | Next.js 14 + React 18 + React Query 5 + Zustand 4 |
| 根目录 | `tsconfig.json` | TypeScript 5.5, strict mode, `@/*` 路径别名 |
| 根目录 | `next.config.ts` | standalone output（Docker 部署用） |
| 根目录 | `tailwind.config.ts` | Tailwind 3.4, dark mode: class |
| `src/app/` | `layout.tsx` | 根布局，中文 lang，Providers 包裹 |
| `src/app/` | `providers.tsx` | React Query Provider（staleTime=30s） |
| `src/app/` | `globals.css` | Tailwind directives + dark mode CSS 变量 |
| `src/app/` | `page.tsx` | Dashboard 主页 |
| `src/app/portfolio/` | `page.tsx` | Portfolio 详情页 |
| `src/lib/` | `api.ts` | API 客户端（8 个接口函数） |
| `src/stores/` | `appStore.ts` | Zustand store（currentStock + darkMode） |
| `src/components/` | `Sidebar.tsx` | 侧边栏导航 |
| `src/components/` | `HotStocks.tsx` | 热门股票列表 |
| `src/components/` | `AlertList.tsx` | 告警列表 |
| `src/components/` | `AnalyzePanel.tsx` | AI 分析面板（输入股票代码 → 调用分析） |
| `src/components/` | `PortfolioView.tsx` | 组合详情（持仓权重柱状图） |
| `src/components/` | `NotificationBell.tsx` | 通知铃铛（30s 轮询未读告警） |

### 架构设计

```
src/app/
├── layout.tsx          ← 根布局（Providers 包裹）
├── providers.tsx       ← React Query ClientProvider
├── page.tsx            ← Dashboard（AnalyzePanel + HotStocks + AlertList）
└── portfolio/
    └── page.tsx        ← Portfolio（侧边栏选择 + PortfolioView）

src/components/         ← 6 个 UI 组件
src/lib/api.ts          ← 统一 API 客户端
src/stores/appStore.ts  ← 全局状态（Zustand）
```

---

## 2. 前端代码审核

### 总评

| 维度 | 得分 | 说明 |
|------|------|------|
| 正确性 | 4/5 | API 调用逻辑正确，类型基本完备 |
| 架构一致性 | 4.5/5 | 完全符合设计文档（Next.js + Tailwind + Zustand + React Query） |
| 安全性 | 3.5/5 | 无 XSS 风险，但 API 无认证（Phase 5） |
| 性能 | 4/5 | staleTime=30s 合理，NotificationBell 30s 轮询 |
| 可维护性 | 4/5 | 组件职责单一，API 层统一，状态管理清晰 |
| **综合** | **4/0/5** | |

### 亮点

- **统一 API 客户端** — `api.ts` 封装 `apiFetch<T>`，错误处理统一，所有接口一处管理
- **React Query 集成** — `staleTime: 30s` + `retry: 1`，避免频繁请求，网络异常自动重试
- **暗色模式** — Zustand store + Tailwind `dark:` class，`toggleDarkMode` 直接操作 `document.documentElement`
- **组件 Skeleton** — 加载状态使用 `animate-pulse` skeleton，用户体验好
- **PortfolioView 权重可视化** — 持仓权重用 CSS progress bar 展示，直观清晰
- **NotificationBell** — 30s 轮询未读数，红点显示 `9+` 上限

### 发现的问题

#### 🔴 [High] `npm install` 失败 — `unrs-resolver` ENOENT

**现象：**
```
npm error code ENOENT
npm error syscall spawn C:\WINDOWS\system32\cmd.exe
npm error path D:\...\frontend\node_modules\unrs-resolver
npm error errno -4058
npm error enoent spawn C:\WINDOWS\system32\cmd.exe ENOENT
```

**根因：** npm 的 `unrs-resolver` 包在 Windows 上尝试 spawn `cmd.exe` 但路径解析失败。可能原因：
1. `PATH` 环境变量中 `C:\WINDOWS\system32` 不在搜索路径
2. 杀毒软件拦截了 `cmd.exe` 的 spawn
3. npm 缓存损坏

**修复方案：**
```bash
# 方案 1：清除 npm 缓存重试
npm cache clean --force
cd frontend && npm install

# 方案 2：使用管理员 PowerShell
# 以管理员身份运行 PowerShell，再执行 npm install

# 方案 3：删除 node_modules 重试
rm -rf frontend/node_modules frontend/package-lock.json
cd frontend && npm install

# 方案 4：使用 yarn 代替
npm install -g yarn
cd frontend && yarn install
```

#### 🟡 [Medium] `api.ts` 中 `apiFetch` 无错误响应体解析

**文件:** `frontend/src/lib/api.ts:8`

```typescript
if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
```

后端返回的 JSON 错误信息（如 `{"error": "not found"}`）被丢弃。应解析响应体：

```typescript
if (!res.ok) {
  const body = await res.json().catch(() => ({}));
  throw new Error(body.error || `API ${res.status}: ${res.statusText}`);
}
```

#### 🟡 [Medium] `AnalyzePanel` 分析结果直接 `JSON.stringify` 展示

**文件:** `frontend/src/components/AnalyzePanel.tsx:31`

```tsx
<pre className="whitespace-pre-wrap">{JSON.stringify(mutation.data, null, 2)}</pre>
```

完整的分析结果（含所有 Agent 输出）直接 dump，用户体验差。应提取关键字段（verdict、score、summary）展示。

#### 🟡 [Medium] `HotStocks` 颜色逻辑反了

**文件:** `frontend/src/components/HotStocks.tsx:26`

```tsx
<span className={s.change_pct >= 0 ? "text-red-600" : "text-green-600"}>
```

A 股惯例：涨红跌绿。代码是 `>= 0` 红色、`< 0` 绿色，这**符合 A 股惯例**。但如果是国际用户可能觉得反了。当前逻辑正确，无需修改。

#### 🟡 [Low] `portfolio/page.tsx` 使用 `any` 类型

**文件:** `frontend/src/app/portfolio/page.tsx:34`

```tsx
portfolios.map((p: any) => (
```

应定义 TypeScript interface：

```typescript
interface Portfolio {
  id: string;
  name: string;
  risk_score: number;
  holdings: Record<string, number>;
  candidate_pool: string[];
}
```

#### 🟡 [Low] `appStore.ts` 中 `toggleDarkMode` 直接操作 DOM

**文件:** `frontend/src/stores/appStore.ts:15`

```typescript
document.documentElement.classList.toggle("dark", next);
```

Next.js SSR 时 `document` 不存在。虽然当前组件都是 `"use client"`，但 store 在服务端导入时会报错。建议用 `useEffect` 同步。

---

## 3. 前端启动与测试

### 前置条件

```bash
# 确保后端服务运行中
cd backend
uvicorn app.main:app --reload --port 8000
```

### 安装与启动

```bash
cd frontend

# 安装依赖（如遇 ENOENT 错误，见上方修复方案）
npm install

# 启动开发服务器
npm run dev
```

**预期结果：**
```
  ▲ Next.js 14.2.x
  - Local:   http://localhost:3000
  - Network: http://192.168.x.x:3000

 ✓ Ready in 2.3s
```

浏览器打开 `http://localhost:3000`，应看到 Dashboard 页面。

### 构建验证

```bash
cd frontend
npm run build
```

**预期结果：**
```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Creating an optimized production build

Route (app)                    Size     First Load JS
┌ ○ /                          5.2 kB        89 kB
├ ○ /portfolio                 3.1 kB        87 kB
└ ○ /_not-found                871 B         85 kB
+ First Load JS shared by all  84.3 kB
```

---

## 4. 页面功能测试

### 4.1 Dashboard 页面 (`/`)

打开 `http://localhost:3000`，验证以下内容：

| 检查项 | 预期结果 |
|-------|---------|
| 侧边栏 | 显示 "AI Investment OS" + Dashboard / Portfolio 两个链接 |
| 标题 | "Dashboard" + 右侧通知铃铛 |
| AI Analysis 面板 | 输入框默认 "600519" + Analyze 按钮 |
| Hot Stocks 面板 | 加载中显示 skeleton → 显示热门股票列表（需后端 akshare 正常） |
| Alerts 面板 | 显示告警列表或 "No alerts." |

**测试 AI 分析：**
1. 在输入框输入 `600519`
2. 点击 "Analyze"
3. 按钮变为 "Analyzing..."（禁用状态）
4. 等待 5-15 秒后显示 JSON 结果

**预期结果：** 显示完整的分析结果 JSON（含 decision、report、agent_outputs）。

### 4.2 Portfolio 页面 (`/portfolio`)

点击侧边栏 "Portfolio"，验证以下内容：

| 检查项 | 预期结果 |
|-------|---------|
| 左侧列表 | "No portfolios yet."（如果未创建组合） |
| 创建组合 | 通过 API 或 Swagger 创建后刷新页面 |
| 选择组合 | 点击组合名 → 右侧显示 PortfolioView |
| Risk Score | 显示数字 |
| Holdings | 显示持仓数量 |
| Total Weight | 显示权重百分比 |
| 权重条形图 | 每只股票一个蓝色进度条 |

### 4.3 通知铃铛

| 检查项 | 预期结果 |
|-------|---------|
| 无告警 | 铃铛图标，无红点 |
| 有未读告警 | 铃铛 + 红色数字角标 |
| 超过 9 条 | 显示 "9+" |

---

## 5. 前后端联调测试

### 5.1 端到端流程

```bash
# 终端 1：启动后端
cd backend && uvicorn app.main:app --reload --port 8000

# 终端 2：启动前端
cd frontend && npm run dev
```

浏览器操作流程：

1. 打开 `http://localhost:3000`
2. Dashboard → 输入 `600519` → 点击 Analyze
3. 等待分析完成，查看结果
4. 通过 Swagger (`http://localhost:8000/docs`) 创建一个 Portfolio
5. 刷新前端 Portfolio 页面，查看新创建的组合
6. 点击组合查看持仓详情

### 5.2 API 连通性快速验证

```bash
# 检查前端能否访问后端
curl http://localhost:8000/health
# 预期: {"status":"ok","version":"0.1.0"}

# 检查 CORS 配置
curl -H "Origin: http://localhost:3000" -I http://localhost:8000/api/stocks/hot
# 预期: Access-Control-Allow-Origin: http://localhost:3000
```

---

## 6. 预期结果速查表

| 测试项 | 命令/操作 | 预期结果 |
|-------|---------|---------|
| 后端测试 | `cd backend && pytest tests/ -v` | `83 passed` |
| 前端安装 | `cd frontend && npm install` | 无报错，`node_modules/` 创建成功 |
| 前端构建 | `npm run build` | `✓ Compiled successfully` |
| 前端启动 | `npm run dev` | `http://localhost:3000` 可访问 |
| Dashboard | 浏览器打开 `/` | 侧边栏 + AI分析 + 热门股票 + 告警 |
| AI 分析 | 输入 600519 → Analyze | JSON 结果展示 |
| Portfolio | 浏览器打开 `/portfolio` | 组合列表 + 详情 |
| 通知铃铛 | 有未读告警时 | 红色数字角标 |
| CORS | 前端调后端 API | 无跨域错误 |

---

## 7. 已发现的问题

### 需立即修复

| # | 问题 | 严重性 | 修复方案 |
|---|------|--------|---------|
| 1 | `npm install` ENOENT 错误 | High | 清缓存/管理员运行/用 yarn |

### 代码改进

| # | 问题 | 严重性 | 说明 |
|---|------|--------|------|
| 2 | `apiFetch` 不解析错误响应体 | Medium | 后端错误信息丢失 |
| 3 | AnalyzePanel 直接 JSON.stringify | Medium | 应提取关键字段展示 |
| 4 | `any` 类型散落各组件 | Low | 应定义 TypeScript interface |
| 5 | `toggleDarkMode` 直接操作 DOM | Low | SSR 不安全 |

---

## 8. 遗留问题与建议

### 功能待完善

| 功能 | 当前状态 | 说明 |
|------|---------|------|
| 用户登录页 | 未实现 | Phase 5 实现 JWT 认证 + 登录表单 |
| K 线图表 | 未实现 | `lightweight-charts` 已安装但未使用，可添加 K 线图组件 |
| WebSocket 实时推送 | 后端就绪，前端未接入 | 应在前端建立 WebSocket 连接接收告警推送 |
| 分析结果可视化 | 仅 JSON dump | 应提取 verdict/score/key_points 展示为卡片 |
| Portfolio 创建表单 | 仅通过 API | 前端应添加创建组合的表单 |
| 响应式布局 | 未适配移动端 | 当前仅桌面布局 |

### 技术债务

| 项目 | 说明 |
|------|------|
| TypeScript `any` 类型 | 所有 API 响应使用 `any`，应定义完整 interface |
| 无 Error Boundary | 组件崩溃会导致整个页面白屏 |
| 无 loading/error 全局处理 | 每个组件单独处理，应提取公共 Loading/Error 组件 |
| ESLint 未配置规则 | `eslint-config-next` 默认规则，应添加项目规则 |
