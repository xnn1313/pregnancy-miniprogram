#!/bin/bash
# 孕期小程序后端服务启动脚本

cd /root/.openclaw/workspace/pregnancy-miniprogram

# 检查是否已有进程在运行
PID=$(pgrep -f "uvicorn backend.main:app")
if [ -n "$PID" ]; then
    echo "后端服务已在运行 (PID: $PID)"
    exit 0
fi

# 启动服务
echo "启动后端服务..."
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8088 >> /tmp/backend.log 2>&1 &

# 等待启动
sleep 2

# 检查是否成功
if curl -s http://localhost:8088/health > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
    echo "API 文档: http://localhost:8088/docs"
else
    echo "❌ 启动失败，查看日志:"
    tail -20 /tmp/backend.log
fi