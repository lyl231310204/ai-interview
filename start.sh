#!/bin/bash
echo "========================================"
echo "  AI 智能面试系统 — 一键启动"
echo "========================================"

echo "[1/3] 安装后端依赖..."
cd backend
pip install -r requirements.txt -q

echo "[2/3] 安装前端依赖..."
cd ../frontend
npm install --registry=https://registry.npmmirror.com --silent

echo "[3/3] 启动服务..."
echo "后端: http://localhost:8000"
echo "前端: http://localhost:3000"

cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
cd ../frontend && npx nuxi dev --host 0.0.0.0 &

sleep 8
open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null
wait
