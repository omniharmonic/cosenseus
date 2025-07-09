#!/bin/bash

# Census Local Development Setup Script
echo "🚀 Setting up Census Local Development Environment..."

# Check if we're in the right directory
if [ ! -f "backend/api-gateway/main_local.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Create local data directory
echo "📁 Creating local data directory..."
mkdir -p local_data

# Check Python version
echo "🐍 Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Setup Python virtual environment
echo "📦 Setting up Python virtual environment..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies for local development
echo "📦 Installing additional local development dependencies..."
pip install requests

cd ..

# Setup frontend dependencies
echo "📦 Setting up frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
else
    echo "Frontend dependencies already installed"
fi

cd ..

# Check if Ollama is running
echo "🔍 Checking Ollama status..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Ollama is not running. Please start it with:"
    echo "   ollama serve"
    echo "   Then in another terminal: ollama run llama3.2"
fi

echo ""
echo "✅ Local development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start Ollama: ollama serve"
echo "2. In another terminal: ollama run llama3.2"
echo "3. Start the development environment: ./scripts/start_local_dev.sh"
echo ""
echo "🌐 Services will be available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Ollama: http://localhost:11434" 