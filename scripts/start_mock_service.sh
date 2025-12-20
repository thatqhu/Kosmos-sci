#!/bin/bash
#
# 启动 Mock Training Service
#
# 使用方法:
#   ./scripts/start_mock_service.sh

echo "========================================================================"
echo "🚀 Starting Mock SCI Training Service"
echo "========================================================================"

# 检查依赖
echo "Checking dependencies..."

if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "❌ FastAPI not installed"
    echo "Installing: pip install fastapi uvicorn requests"
    pip install fastapi uvicorn requests
fi

echo "✅ Dependencies OK"
echo ""

# 启动服务
echo "Starting service on http://0.0.0.0:8001"
echo "API Docs: http://localhost:8001/docs"
echo "Health Check: http://localhost:8001/health"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================================================"

cd "$(dirname "$0")/.."
python3 tests/mock_training_service.py
