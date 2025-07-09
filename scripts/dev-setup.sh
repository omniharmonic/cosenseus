#!/bin/bash

# Civic Sense-Making Platform - Development Setup Script
# This script sets up the development environment for the platform

set -e  # Exit on any error

echo "🚀 Setting up Civic Sense-Making Platform development environment..."

# Check for required tools
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 is not installed. Please install $1 and try again."
        exit 1
    fi
}

echo "📋 Checking dependencies..."
check_dependency "docker"
check_dependency "docker-compose"
check_dependency "node"
check_dependency "python3"

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p backend/auth-service
mkdir -p backend/event-service
mkdir -p backend/nlp-service
mkdir -p backend/profile-service
mkdir -p frontend/src
mkdir -p infrastructure/database
mkdir -p infrastructure/monitoring/prometheus
mkdir -p infrastructure/monitoring/grafana/dashboards
mkdir -p infrastructure/monitoring/grafana/datasources
mkdir -p infrastructure/kubernetes
mkdir -p tests/integration
mkdir -p tests/e2e
mkdir -p docs/api

# Create __init__.py files for Python packages
echo "🐍 Setting up Python package structure..."
touch backend/__init__.py
touch backend/api-gateway/__init__.py
touch backend/api-gateway/core/__init__.py
touch backend/api-gateway/routers/__init__.py
touch backend/shared/__init__.py
touch backend/shared/models/__init__.py

# Create environment file
echo "🔧 Creating environment configuration..."
cat > .env << EOF
# Environment
ENVIRONMENT=development
DEBUG=true

# Security
SECRET_KEY=development-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Database
DATABASE_URL=postgresql://census_user:census_password@localhost:5432/census
REDIS_URL=redis://localhost:6379

# Microservices
AUTH_SERVICE_URL=http://localhost:8001
EVENT_SERVICE_URL=http://localhost:8002
NLP_SERVICE_URL=http://localhost:8003
PROFILE_SERVICE_URL=http://localhost:8004

# External Services
OPENAI_API_KEY=your-openai-api-key-here
AZURE_SPEECH_KEY=your-azure-speech-key-here
AZURE_SPEECH_REGION=your-azure-region-here

# Vector Database
VECTOR_DB_TYPE=chroma
CHROMA_URL=http://localhost:8900

# Neo4j
NEO4J_URL=bolt://neo4j:census_password@localhost:7687

# File Storage
UPLOAD_DIR=/tmp/uploads
MAX_FILE_SIZE=10485760

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Monitoring
PROMETHEUS_METRICS=true
LOG_LEVEL=INFO
EOF

# Create database initialization script
echo "🗄️ Creating database initialization script..."
cat > infrastructure/database/init.sql << EOF
-- Initialize the Civic Sense-Making Platform database
-- This script runs on first database startup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set up full text search configuration
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS civic_english (COPY=english);

-- Create initial admin user (development only)
-- Password: admin123 (hashed)
-- This will be replaced by proper user creation through the API
EOF

# Create Prometheus configuration
echo "📊 Setting up monitoring configuration..."
cat > infrastructure/monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files: []

scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:8001']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'event-service'
    static_configs:
      - targets: ['event-service:8002']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'nlp-service'
    static_configs:
      - targets: ['nlp-service:8003']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'profile-service'
    static_configs:
      - targets: ['profile-service:8004']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

# Create Grafana datasource configuration
cat > infrastructure/monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

# Create basic frontend package.json
echo "⚛️ Setting up frontend structure..."
cat > frontend/package.json << EOF
{
  "name": "census-frontend",
  "version": "1.0.0",
  "description": "Civic Sense-Making Platform Frontend",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "typescript": "^4.9.5",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "react-router-dom": "^6.8.0",
    "@mui/material": "^5.15.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "d3": "^7.8.0",
    "@types/d3": "^7.4.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF

# Create frontend Dockerfile
cat > frontend/Dockerfile.dev << EOF
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
EOF

# Make script executable
chmod +x scripts/dev-setup.sh

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your API keys"
echo "2. Run 'docker-compose up -d' to start all services"
echo "3. Visit http://localhost:3000 for frontend"
echo "4. Visit http://localhost:8000/docs for API documentation"
echo "5. Visit http://localhost:3001 for Grafana monitoring (admin/admin)"
echo ""
echo "🎉 Happy coding!" 