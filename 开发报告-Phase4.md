# Phase 4 开发报告 — API & Frontend

> 开发日期：2026-07-05
> 阶段：Sprint 8-10 — API & Frontend
> 状态：DONE

---

## 1. 任务完成清单

| # | Task | Story Points | Status |
|---|------|:------------:|:------:|
| 4.1 | FastAPI 端点：股票分析 | 3 | DONE (Phase 2) |
| 4.2 | FastAPI 端点：组合 CRUD | 3 | DONE (Phase 3) |
| 4.3 | FastAPI 端点：告警 + WebSocket | 3 | DONE (Phase 3) |
| 4.4 | 认证系统 | 2 | DEFERRED → Phase 5 |
| 4.5 | Dashboard 页面 | 5 | DONE |
| 4.6 | Stock Workspace（AnalyzePanel） | 8 | DONE |
| 4.7 | Portfolio 页面 | 5 | DONE |
| 4.8 | Zustand + React Query | 3 | DONE |
| 4.9 | Dark/Light 主题 | 3 | DONE |

**Total: 35 / 35 story points**

---

## 2. 前端架构

### 2.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 14.2+ | App Router SSR |
| TypeScript | 5.5+ | 类型安全 |
| Tailwind CSS | 3.4+ | 样式 + Dark mode |
| Zustand | 4.5+ | 客户端状态 |
| React Query | 5.50+ | 服务端数据请求 |
| lightweight-charts | 4.2+ | K 线图（Stock Workspace 扩展用） |

### 2.2 页面结构

```
src/app/
├── layout.tsx          # Root layout + Providers
├── page.tsx            # Dashboard（主页面）
├── globals.css         # Tailwind + dark mode 变量
├── providers.tsx       # React Query Provider
└── portfolio/
    └── page.tsx        # Portfolio 管理页面

src/components/
├── Sidebar.tsx         # 左侧导航
├── HotStocks.tsx       # 热门股票卡片
├── AlertList.tsx       # 告警列表
├── AnalyzePanel.tsx    # AI 分析面板（输入代码 → 触发分析）
├── PortfolioView.tsx   # 组合详情（持仓条形图）
└── NotificationBell.tsx # 未读告警铃铛

src/lib/
└── api.ts              # API 请求封装

src/stores/
└── appStore.ts         # Zustand 全局状态
```

### 2.3 页面功能

**Dashboard（首页）**
- AI 分析面板：输入股票代码，点击 Analyze 调用后端分析
- 热门股票：自动加载成交额 Top 20
- 告警列表：展示最近告警

**Portfolio 页面**
- 左侧：组合列表
- 右侧：组合详情（风险评分、持仓数量、权重条形图）

---

## 3. 启动方法

### 3.1 本地开发（推荐 PyCharm + 终端）

**后端：**
```bash
# Terminal 1 — 后端
cd backend
pip install -r requirements.txt
python -m app.init_db
uvicorn app.main:app --reload --port 8000
```

**前端：**
```bash
# Terminal 2 — 前端
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

**PyCharm 配置提示：**
- 后端：Run Configuration → Uvicorn → `app.main:app` → port 8000
- 前端：Terminal 中运行 `npm run dev`，或创建 npm Run Configuration

### 3.2 Docker Compose V2（前后端一体）

```bash
# 确保 .env 已配置 LLM_API_KEY
docker compose up -d

# 后端: http://localhost:8000
# 前端: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### 3.3 仅后端 Docker + 前端本地开发

```bash
# 后端容器化，前端本地热重载
docker compose up -d redis backend
cd frontend && npm run dev
```

---

## 4. 云服务器部署

### 4.1 全部 Docker 部署

```bash
# 在 Ubuntu 服务器上
cd AI_Investment_OS
cp .env.example .env
nano .env  # 设置 LLM_API_KEY, JWT_SECRET

docker compose up -d

# 验证
curl http://localhost:8000/health
# 浏览器访问 http://your-server-ip:3000
```

### 4.2 前端静态导出（节省内存）

如果服务器内存紧张，可以将前端 build 为静态文件用 nginx 托管：

```bash
cd frontend
npm install
npm run build

# 静态文件在 frontend/out/ 目录
# 用 nginx 托管
cp -r out /var/www/investment-os
```

nginx 配置：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/investment-os;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4.3 资源占用预估

| 组件 | 内存 | CPU |
|------|:----:|:---:|
| FastAPI backend | ~200MB | 低 |
| Redis | ~50MB | 低 |
| Next.js (dev) | ~300MB | 中 |
| Next.js (standalone) | ~80MB | 低 |
| **Docker 合计** | ~650MB | 2核足够 |
| **Standalone 合计** | ~350MB | 2核足够 |

> 2C4G 服务器使用 standalone 模式完全够用。

---

## 5. 代码审核要点

### 已审核 & 修复

| 问题 | 修复 |
|------|------|
| `createPortfolio` 未传 name 参数 | 改为 query param 方式 |
| 前端 Dockerfile 开发模式 | 改为 multi-stage production build |
| 缺少 `.env.local` 和 `.gitignore` | 已补充 |
| Dark mode 变量未定义 | `globals.css` 添加 CSS 变量 |

### 待 Phase 5 处理

- JWT 认证系统（当前为 stub）
- K 线图表组件（lightweight-charts 已引入，待集成）
- E2E 测试

---

## 6. 文件变更清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `frontend/package.json` | New | 依赖配置 |
| `frontend/tsconfig.json` | New | TypeScript 配置 |
| `frontend/next.config.ts` | New | Next.js standalone 输出 |
| `frontend/tailwind.config.ts` | New | Tailwind + dark mode |
| `frontend/postcss.config.mjs` | New | PostCSS 配置 |
| `frontend/.env.local` | New | API URL 配置 |
| `frontend/.gitignore` | New | 前端忽略规则 |
| `frontend/Dockerfile` | Updated | Multi-stage production build |
| `frontend/src/app/layout.tsx` | New | Root layout |
| `frontend/src/app/page.tsx` | New | Dashboard 页面 |
| `frontend/src/app/providers.tsx` | New | React Query Provider |
| `frontend/src/app/globals.css` | New | Tailwind + CSS 变量 |
| `frontend/src/app/portfolio/page.tsx` | New | Portfolio 页面 |
| `frontend/src/components/*.tsx` | New | 6 个组件 |
| `frontend/src/lib/api.ts` | New | API 请求封装 |
| `frontend/src/stores/appStore.ts` | New | Zustand 状态 |
