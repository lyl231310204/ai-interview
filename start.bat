@echo off
echo ========================================
echo   AI 面试系统 — 一键部署
echo ========================================

:: 有 Docker 优先
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [Docker 模式] 启动中...
    docker compose up -d --build
    start http://localhost:3000
    echo 访问 http://localhost:3000
    pause
    exit /b 0
)

:: 手动模式
cd /d "%~dp0backend"
start "后端" cmd /c "uvicorn app.main:app --host 0.0.0.0 --port 8000"
cd /d "%~dp0frontend"
start "前端" cmd /c "npx nuxi dev --host 0.0.0.0"
timeout /t 8 /nobreak >nul
start http://localhost:3000
pause
