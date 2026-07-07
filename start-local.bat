@echo off
REM AI Investment OS - 本地启动脚本 (Win11)
REM 用法: 双击运行 或 在项目根目录执行 start-local.bat

echo ================================
echo   AI Investment OS - 本地启动
echo ================================
echo.

REM 检查 .env
if not exist ".env" (
    echo [!] 未找到 .env 文件，请先复制并配置:
    echo     copy .env.example .env
    echo     然后编辑 .env 填入 LLM API Key
    pause
    exit /b 1
)

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] 未找到 Python，请安装 Python 3.11+
    pause
    exit /b 1
)

REM 检查 Node
node --version >nul 2>&1
if errorlevel 1 (
    echo [!] 未找到 Node.js，请安装 Node.js 18+
    pause
    exit /b 1
)

echo [1/4] 安装后端依赖 (腾讯云镜像)...
cd backend
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q -i https://mirrors.tencent.com/pypi/simple/ --trusted-host mirrors.tencent.com
cd ..

echo [2/4] 安装前端依赖 (腾讯云镜像)...
cd frontend
if not exist "node_modules" (
    call npm config set registry https://mirrors.tencent.com/npm/
    call npm install
)
cd ..

echo [3/4] 启动后端 (端口 8000)...
start "AI-Investment-OS-Backend" cmd /k "cd backend && .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [4/4] 启动前端 (端口 3000)...
timeout /t 3 /nobreak >nul
start "AI-Investment-OS-Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ================================
echo   启动完成!
echo   前端: http://localhost:3000
echo   后端: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo ================================
echo.
echo 按任意键退出此窗口 (后端和前端会继续运行)
pause >nul
