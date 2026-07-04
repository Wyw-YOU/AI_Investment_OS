# AI Investment OS — Environment Setup

## Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend, Phase 4)
- Docker & Docker Compose (optional)
- 任意大模型 API Key（DeepSeek / 通义千问 / MiMo 等）

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure LLM (edit .env first)
cp ../.env.example ../.env
# Edit .env: set LLM_BASE_URL + LLM_API_KEY + LLM_MODEL

# Initialize database
python -m app.init_db

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend (Phase 4)

```bash
cd frontend
npm install
npm run dev
```

### Docker (All Services)

```bash
cp .env.example .env
# Edit .env with your LLM provider config
docker compose up -d
```

## LLM Provider Configuration

系统使用 OpenAI 兼容接口，支持所有提供 OpenAI 格式 API 的大模型。

在 `.env` 中配置以下三个变量即可切换模型：

```env
LLM_BASE_URL=<provider-api-url>
LLM_API_KEY=<your-api-key>
LLM_MODEL=<model-name>
```

### 已验证的国产大模型配置

| Provider | BASE_URL | MODEL | 推荐理由 |
|----------|----------|-------|---------|
| **DeepSeek** | `https://api.deepseek.com` | `deepseek-chat` | 性价比最高，中文金融理解能力强 |
| **通义千问** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` | 阿里云生态，稳定性好 |
| **MiMo** | `https://api.xiaomi.com/v1` | `MiMo-7B` | 小米模型，免费额度 |
| **Moonshot** | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` | Kimi 背后模型 |
| **SiliconFlow** | `https://api.siliconflow.cn/v1` | `deepseek-ai/DeepSeek-V3` | 多模型聚合平台 |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o-mini` | 海外直连 |

### 示例：使用 DeepSeek

```env
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=deepseek-chat
LLM_MAX_TOKENS=2000
```

### 示例：使用通义千问

```env
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=qwen-plus
LLM_MAX_TOKENS=2000
```

## API Docs

Once backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Cloud Deployment (2C4G Ubuntu)

```bash
# On Ubuntu server
git clone <repo-url>
cd AI_Investment_OS
cp .env.example .env
nano .env  # Set LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

cd backend
pip install -r requirements.txt
python -m app.init_db
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```
