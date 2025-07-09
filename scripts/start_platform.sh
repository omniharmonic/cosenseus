#!/bin/bash

# Civic Sense-Making Platform Startup Script
# This script launches both frontend and backend services together

set -e  # Exit on any error
# set -x # Print every command for debugging - DISABLED

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        # Use a subshell and '|| true' to prevent 'set -e' from exiting the script on a failed curl
        if (curl -s --fail "$url" >/dev/null 2>&1); then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to cleanup background processes
cleanup() {
    print_status "Shutting down services..."
    
    # Kill background processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend stopped"
    fi
    
    if [ ! -z "$NLP_PID" ]; then
        kill $NLP_PID 2>/dev/null || true
        print_status "NLP service stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Frontend stopped"
    fi
    
    print_success "All services stopped"
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGINT SIGTERM

# --- Robust auto-kill for required ports ---
ensure_port_free() {
  PORT=$1
  
  # Use lsof to find processes on the port
  PIDS=$(lsof -ti tcp:$PORT)
  if [ ! -z "$PIDS" ]; then
    print_warning "Port $PORT is in use by PID(s): $PIDS. Killing..."
    kill -9 $PIDS >/dev/null 2>&1
    
    # Wait for port to be released
    for i in {1..5}; do
        if ! lsof -ti tcp:$PORT >/dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
  fi

  # Final check
  if lsof -ti tcp:$PORT >/dev/null 2>&1; then
    print_error "Failed to free port $PORT. It is still in use."
    exit 1
  else
    print_success "Port $PORT is free."
  fi
}


# Parse arguments
BACKEND_ONLY=false
for arg in "$@"; do
    if [[ "$arg" == "--backend-only" ]]; then
        BACKEND_ONLY=true
    fi
    # Add more flags here if needed
done

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_status "Starting Civic Sense-Making Platform..."
print_status "Project root: $PROJECT_ROOT"

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/README.md" ]; then
    print_error "Could not find project root. Please run this script from the project directory."
    exit 1
fi

# Check if required tools are available
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed or not in PATH"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Kill processes on required ports before starting
REQUIRED_PORTS=(8000 8003 3000)
for PORT in "${REQUIRED_PORTS[@]}"; do
  ensure_port_free $PORT
done

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    print_warning "Ollama is not running. Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Start NLP service first (it's needed by the backend)
print_status "Starting NLP service..."
cd "$PROJECT_ROOT/backend/nlp_service"
source ../venv/bin/activate
python main.py > "$PROJECT_ROOT/logs/nlp_service.log" 2>&1 &
NLP_PID=$!
print_success "NLP service started (PID: $NLP_PID)"

# Wait for NLP service to be ready
wait_for_service "http://localhost:8003/health" "NLP Service"

# Start backend
print_status "Starting backend API gateway..."
cd "$PROJECT_ROOT/backend/api-gateway"
source ../venv/bin/activate
python main_local.py > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
print_success "Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
wait_for_service "http://localhost:8000/api/v1/" "Backend API"

# Start frontend unless --backend-only is set
FRONTEND_STARTED=false
if [ "$BACKEND_ONLY" = false ]; then
    if check_port 3000; then
        print_warning "Port 3000 is already in use. Skipping frontend startup."
    else
        print_status "Starting frontend..."
        cd "$PROJECT_ROOT/frontend"
        npm start > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        FRONTEND_STARTED=true
        print_success "Frontend started (PID: $FRONTEND_PID)"
        # Wait for frontend to be ready
        wait_for_service "http://localhost:3000" "Frontend"
    fi
else
    print_warning "--backend-only flag set. Not starting frontend."
fi

# Display final status
echo ""
print_success "🎉 Civic Sense-Making Platform is now running!"
echo ""
echo -e "${GREEN}Services:${NC}"
echo -e "  ${BLUE}Frontend:${NC}    http://localhost:3000"
echo -e "  ${BLUE}Backend API:${NC}  http://localhost:8000/api/v1/"
echo -e "  ${BLUE}API Docs:${NC}     http://localhost:8000/docs"
echo -e "  ${BLUE}NLP Service:${NC}  http://localhost:8003/health"
echo -e "  ${BLUE}Ollama:${NC}       http://localhost:11434"
echo ""
echo -e "${GREEN}Logs:${NC}"
echo -e "  ${BLUE}Backend:${NC}      $PROJECT_ROOT/logs/backend.log"
echo -e "  ${BLUE}Frontend:${NC}     $PROJECT_ROOT/logs/frontend.log"
echo -e "  ${BLUE}NLP Service:${NC}  $PROJECT_ROOT/logs/nlp_service.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Monitor backend and NLP service and keep script running
while true; do
    # Check if backend and NLP are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process died unexpectedly"
        cleanup
    fi
    if ! kill -0 $NLP_PID 2>/dev/null; then
        print_error "NLP service process died unexpectedly"
        cleanup
    fi
    # Only warn if frontend dies, do not kill everything
    if [ "$FRONTEND_STARTED" = true ]; then
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_warning "Frontend process died, but backend and NLP are still running. You can restart the frontend manually if needed."
            FRONTEND_STARTED=false
        fi
    fi
    sleep 10
done 