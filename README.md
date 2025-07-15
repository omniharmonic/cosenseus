# CoSenseus - AI-Enabled Civic Dialogue Platform

CoSenseus is an AI-enabled dialogue tool for building consensus through generative conversation. It transforms natural language input from participants into structured insights, helping groups and communities move beyond debate and foster shared understanding.

## 🎯 Overview

CoSenseus operates as a local-first application, ensuring privacy and user control. It uses local language models (via Ollama) to perform real-time analysis of civic and organizational dialogue. The current version is focused on providing a powerful, single-event experience with a clear path toward a scalable, cloud-native architecture.

### ✨ Key Features (Local-First MVP)

- **🤖 Local-First AI**: All analysis is performed on your local machine using Ollama
- **📅 Event Creation & Management**: Create and manage single dialogue events
- **🔄 Multi-Round Conversations**: Support for iterative rounds of input and AI-powered synthesis
- **📊 Real-time Visualization**: Interactive visualizations for sentiment, word clouds, and consensus
- **👥 Admin-in-the-Loop**: Administrators review and approve AI-generated prompts before they are sent to participants
- **📄 Dynamic Reporting**: Flexible options to export raw data and generate formatted reports
- **🌐 Network Access**: Share your local instance with others on your network for collaborative sessions

## Architecture

### Core Components

- **Backend Services**: Python FastAPI microservices
- **Frontend Application**: React.js with TypeScript
- **AI/ML Pipeline**: PyTorch, Transformers, scikit-learn
- **Databases**: PostgreSQL, Neo4j, Redis, Vector databases
- **Infrastructure**: Kubernetes, Docker, AWS/GCP

### Project Structure

```
senseus/
├── backend/              # Backend microservices
│   ├── api-gateway/      # Main API gateway service
│   ├── event-service/    # Event management service
│   ├── nlp-service/      # Natural language processing
│   ├── auth-service/     # Authentication and authorization
│   ├── profile-service/  # User profile management
│   └── shared/          # Shared utilities and models
├── frontend/            # React frontend application
├── mobile/              # React Native mobile apps
├── infrastructure/      # Kubernetes, Docker, Terraform
├── docs/               # Technical documentation
├── scripts/            # Development and deployment scripts
└── tests/              # Integration and E2E tests
```

## 🚀 Quick Start

### 📋 Prerequisites

Before running CoSenseus, ensure you have the following installed:

- **Node.js 18+** - [Download here](https://nodejs.org/)
- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Ollama** - [Download here](https://ollama.ai/)
- **Git** - [Download here](https://git-scm.com/)

### 🛠️ Installation & Setup

#### Step 1: Clone the Repository
```bash
git clone https://github.com/omniharmonic/cosenseus.git
cd cosenseus
```

#### Step 2: Install Ollama and AI Model
```bash
# Install Ollama (if not already installed)
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# In a new terminal, pull the required AI model
ollama pull llama3.2:3b
```

#### Step 3: Setup Development Environment
```bash
# Run the development setup script
./scripts/dev-setup.sh
```

#### Step 4: Start the Platform
```bash
# Start all services (frontend + backend)
./start.sh

# Or start backend only (for development)
./start.sh --backend-only
```

### 🌐 Access the Application

Once started, you can access:

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1/
- **API Documentation**: http://localhost:8000/docs
- **Ollama Health Check**: http://localhost:11434

### 🛑 Stopping the Platform

Press `Ctrl+C` in the terminal where you ran `./start.sh` to gracefully stop all services.

## 📖 Detailed Usage Guide

### 🎯 Getting Started with CoSenseus

#### 1. **First-Time Setup**

After completing the installation steps above:

1. **Open your browser** and navigate to http://localhost:3000
2. **Create your first session**:
   - Enter your name (e.g., "Event Organizer")
   - Click "Create Session"
   - Save your session code for future access
3. **You'll be redirected to the dashboard** where you can create events

#### 2. **Creating Your First Event**

1. **Click "Create Event"** in the Admin tab
2. **Fill in event details**:
   - **Title**: "Community Planning Session"
   - **Description**: "Discuss local development priorities"
   - **Event Type**: "Discussion"
   - **Add Questions**: Include 2-3 open-ended questions
3. **Click "Create Event"**
4. **Publish the event** when ready to invite participants

#### 3. **Inviting Participants**

1. **Share the event link** with participants
2. **Participants can access** via:
   - **Local network**: http://[YOUR_IP]:3000 (e.g., http://192.168.1.154:3000)
   - **Same device**: http://localhost:3000
3. **Participants create sessions** and join your event

#### 4. **Running a Multi-Round Dialogue**

1. **Monitor responses** in the event dashboard
2. **When ready to advance**:
   - Click "End Round & Start Analysis"
   - Wait for AI analysis to complete
   - Review and approve AI-generated prompts for the next round
3. **Continue for multiple rounds** as needed
4. **Generate final reports** when the dialogue is complete

### 🌐 Network Access for Collaborative Sessions

CoSenseus supports local network access, allowing multiple participants to join from different devices:

#### **For the Host (Event Organizer)**:
1. **Find your local IP address**:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Windows
   ipconfig | findstr "IPv4"
   ```
2. **Share the network URL** with participants:
   ```
   http://[YOUR_IP]:3000
   ```
   Example: `http://192.168.1.154:3000`

#### **For Participants**:
1. **Open the shared URL** in their browser
2. **Create a session** with their name
3. **Join the event** and start participating

### 🔧 Troubleshooting

#### **Common Issues & Solutions**

**Port Already in Use**:
```bash
# Check what's using the port
lsof -i :8000  # Backend port
lsof -i :3000  # Frontend port

# Kill the process if needed
kill -9 [PID]
```

**Ollama Not Running**:
```bash
# Start Ollama service
ollama serve

# Check if it's running
curl http://localhost:11434/api/tags
```

**Database Issues**:
```bash
# Reset the database (WARNING: This will delete all data)
rm -rf ~/.cosenseus/cosenseus_local.db
./start.sh
```

**Network Access Not Working**:
1. **Check firewall settings** - ensure ports 3000 and 8000 are open
2. **Verify IP address** - use `ifconfig` or `ipconfig` to get correct IP
3. **Test connectivity** - try `curl http://[YOUR_IP]:8000/api/v1/` from another device

#### **Logs and Debugging**

View service logs for debugging:
```bash
# Backend logs
tail -f logs/backend.log

# NLP service logs
tail -f logs/nlp_service.log

# Frontend logs (if running in terminal)
# Check the terminal where you ran npm start
```

### 📊 Available Commands

#### **Startup Commands**:
```bash
# Start all services
./start.sh

# Start backend only (for development)
./start.sh --backend-only

# Start with custom configuration
./scripts/start_local_dev.sh
```

#### **Development Commands**:
```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd frontend && npm install

# Run tests
cd backend && python -m pytest
cd frontend && npm test

# Build for production
cd frontend && npm run build
```

#### **Ollama Commands**:
```bash
# Start Ollama service
ollama serve

# Pull AI model
ollama pull llama3.2:3b

# List available models
ollama list

# Test model
ollama run llama3.2:3b "Hello, how are you?"
```

## 📈 Recent Progress (August 2025)

### ✅ Network Access & Local Development
- **Network Access Fix**: Resolved API URL generation for local network access
- **Database Optimization**: Moved from iCloud Drive to local system directory for better reliability
- **Service Stability**: Enhanced error handling and timeout management
- **Multi-Device Support**: Participants can now access from different devices on local network

### ✅ Backend Service Stability & Ollama Integration
- **Service Stability**: Resolved backend process crashes and port conflicts
- **Ollama Integration**: Enhanced with improved error handling and timeout management
- **Process Management**: Robust service orchestration with auto-kill functionality
- **Development Environment**: Comprehensive startup scripts with backend-only mode
- **Testing & Validation**: All services (Backend API Gateway, NLP Service, Frontend, Ollama) operational

### ✅ Critical Dialogue Progression Fix
- **Root Cause**: Fixed missing analysis fields in `SynthesisResponse` Pydantic model
- **Solution**: Enhanced response model and endpoint to return complete analysis data
- **Result**: Complete data flow from AI analysis through dialogue manager to frontend approval system

## 🏗️ Development Phases

- **Phase 1** (Months 1-6): ✅ Core Platform - **COMPLETED**
- **Phase 2** (Months 7-12): ✅ Advanced AI & Visualization - **COMPLETED**
- **Phase 3** (Months 13-18): 🔄 Integration & Scale - **IN PROGRESS**
- **Phase 4** (Months 19-24): ⏳ Civic Companion Evolution - **PLANNED**

## 🎯 Use Cases

CoSenseus is designed for various civic and organizational dialogue scenarios:

### **🏛️ Civic Engagement**
- **Town Hall Meetings**: Facilitate community discussions on local issues
- **Policy Feedback**: Collect structured input on proposed policies
- **Candidate Forums**: Enable meaningful dialogue between candidates and constituents
- **Neighborhood Planning**: Gather community input on development projects

### **🏢 Organizational Decision-Making**
- **Strategic Planning**: Align teams around organizational goals
- **Change Management**: Build consensus around organizational changes
- **Stakeholder Engagement**: Gather diverse perspectives on key decisions
- **Team Building**: Foster understanding and collaboration within teams

### **🎓 Educational Settings**
- **Classroom Discussions**: Facilitate structured dialogue on complex topics
- **Research Collaboration**: Synthesize diverse academic perspectives
- **Student Government**: Enable democratic decision-making processes
- **Faculty Meetings**: Build consensus on institutional decisions

## 🤝 Contributing

We welcome contributions to CoSenseus! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines and our code of conduct.

### **Development Setup**
```bash
# Fork and clone the repository
git clone https://github.com/[your-username]/cosenseus.git
cd cosenseus

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes and test
./start.sh --backend-only  # For backend development
cd frontend && npm start   # For frontend development

# Commit and push
git add .
git commit -m "feat: Add your feature description"
git push origin feature/your-feature-name
```

### **Reporting Issues**
- Use the [GitHub Issues](https://github.com/omniharmonic/cosenseus/issues) page
- Include detailed steps to reproduce the issue
- Attach relevant logs and screenshots

## 📄 License

[License details to be added]

## 🙏 Acknowledgments

- **Ollama** for providing local AI capabilities
- **FastAPI** for the robust backend framework
- **React** for the responsive frontend
- **The civic technology community** for inspiration and guidance

---

**Made with ❤️ for better civic dialogue and consensus building** 