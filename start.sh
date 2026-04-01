#!/bin/bash
# 启动后端服务

cd /root/.openclaw/workspace/pregnancy-miniprogram
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8088 > /tmp/backend.log 2>&1 &
echo "后端服务启动中..."
sleep 3
curl -s http://localhost:8088/health && echo -e "\n✅ 后端服务启动成功" || echo "❌ 启动失败，查看日志: tail -50 /tmp/backend.log"