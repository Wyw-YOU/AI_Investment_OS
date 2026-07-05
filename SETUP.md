# AI Investment OS — 环境搭建指南

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，设置 LLM 和 JWT：

```env
# LLM（选择一个 Provider）
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-key
LLM_MODEL=deepseek-chat
LLM_MAX_TOKENS=2000

# JWT
JWT_SECRET=your-random-secret-here

# 可选
DEBUG=false
REDIS_URL=redis://localhost:6379/0
```

### 2. 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
python -m app.init_db
uvicorn app.main:app --reload --port 8000
```

访问 API 文档：http://localhost:8000/docs

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:3000

### 4. Docker 一键启动

```bash
cp .env.example .env
# 编辑 .env
docker compose up -d
```

## LLM Provider 切换

在 `.env` 中修改三行即可切换模型：

```env
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-your-key
LLM_MODEL=deepseek-chat
```

| Provider | BASE_URL | MODEL |
|----------|----------|-------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| MiMo | `https://api.xiaomi.com/v1` | `MiMo-7B` |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `deepseek-ai/DeepSeek-V3` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |

## 云服务器部署

详见 [README.md](README.md) 的「云服务器部署」章节。

## 测试

```bash
cd backend
pytest tests/ -v
```
