#!/bin/bash

# Census Local Development Startup Script
echo "🚀 Starting Census Local Development Environment..."

# Check if Ollama is running
echo "🔍 Checking Ollama status..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running. Please start Ollama first:"
    echo "   ollama serve"
    echo "   Then in another terminal: ollama run llama3.2"
    exit 1
fi

echo "✅ Ollama is running"

# Check if we're in the right directory
if [ ! -f "backend/api-gateway/main_local.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Create local data directory
mkdir -p local_data

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies if needed
echo "📦 Checking frontend dependencies..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# --- Robust auto-kill for required ports ---
ensure_port_free() {
  PORT=$1
  echo "🔍 Checking for processes using port $PORT..."

  # Kill local processes using the port
  PIDS=$(lsof -ti tcp:$PORT)
  if [ ! -z "$PIDS" ]; then
    echo "⚠️  Gracefully stopping local processes on port $PORT: $PIDS"
    kill $PIDS # Use graceful kill instead of kill -9
  fi

  # Kill Docker containers using the port
  if command -v docker &> /dev/null; then
    CONTAINERS=$(docker ps --format '{{.ID}} {{.Ports}}' | grep ":$PORT" | awk '{print $1}')
    for CONTAINER in $CONTAINERS; do
      echo "⚠️  Stopping Docker container using port $PORT: $CONTAINER"
      docker stop $CONTAINER
    done
  fi

  # Wait until the port is actually free
  for i in {1..10}; do
    sleep 0.5
    if ! lsof -i tcp:$PORT &> /dev/null; then
      echo "✅ Port $PORT is now free."
      return 0
    fi
    echo "⏳ Waiting for port $PORT to be released..."
  done

  echo "❌ Port $PORT is still in use after waiting. Exiting."
  exit 1
}

REQUIRED_PORTS=(8000 8003 3000)
for PORT in "${REQUIRED_PORTS[@]}"; do
  ensure_port_free $PORT
  # Add a short sleep to avoid race conditions
  sleep 0.5
done

# Go back to root before starting servers
cd ..

# Start backend server
echo "🔧 Starting backend server..."
(cd backend/api-gateway && ../venv/bin/python main_local.py > ../../logs/backend.log 2>&1) &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "🎨 Starting frontend server..."
(cd frontend && npm start) &
FRONTEND_PID=$!

echo "✅ Local development environment started!"
echo ""
echo "📊 Services:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Ollama: http://localhost:11434"
echo ""
echo "🛑 To stop all services, press Ctrl+C"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait 