@echo off
echo ========================================
echo   AI 智能面试系统 — 一键启动
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请先安装 Node.js 20+
    pause
    exit /b 1
)

echo [1/3] 安装后端依赖...
cd backend
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 后端依赖安装失败
    pause
    exit /b 1
)

echo [2/3] 安装前端依赖...
cd ..\frontend
npm install --registry=https://registry.npmmirror.com --silent
if %errorlevel% neq 0 (
    echo [错误] 前端依赖安装失败
    pause
    exit /b 1
)

echo [3/3] 启动服务...
echo.
echo 后端地址: http://localhost:8000
echo 前端地址: http://localhost:3000
echo.
echo 按 Ctrl+C 停止所有服务
echo ========================================

:: 启动后端
start "AI面试-后端" cmd /c "cd /d %~dp0backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端
start "AI面试-前端" cmd /c "cd /d %~dp0frontend && npx nuxi dev --host 0.0.0.0"

:: 自动打开浏览器
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo 服务已启动，浏览器即将打开...
pause
