#!/bin/bash
# Semiconductor Training System — Start Script
cd "$(dirname "$0")"

echo "📚 半导体培训系统"
echo "=================="
echo ""

# Kill existing processes
pkill -f "uvicorn app.main" 2>/dev/null
pkill -f "streamlit run streamlit_app.py" 2>/dev/null
sleep 1

# Start FastAPI backend
echo "🚀 Starting FastAPI backend on :8001..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
API_PID=$!
sleep 2

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend on :8502..."
python3 -m streamlit run streamlit_app.py --server.port 8502 --server.headless true --server.baseUrlPath=/train-proxy &
UI_PID=$!

echo ""
echo "✅ Training system started!"
echo "   Frontend: http://localhost:8502"
echo "   Backend:  http://localhost:8001"
echo "   API Docs: http://localhost:8001/docs"
echo ""
echo "   Account: erwinbo / erwinbo669570"
echo ""
echo "Press Ctrl+C to stop"
wait
