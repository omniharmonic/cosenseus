# cosenseus

CoSenseus is an AI-enabled dialogue tool for building consensus through generative conversation. It transforms natural language input from participants into structured insights, helping groups and communities move beyond debate and foster shared understanding.

## Overview

CoSenseus operates as a local-first application, ensuring privacy and user control. It uses local language models (via Ollama) to perform real-time analysis of civic and organizational dialogue. The current version is focused on providing a powerful, single-event experience with a clear path toward a scalable, cloud-native architecture.

### Key Features (Local-First MVP)

- **Local-First AI**: All analysis is performed on your local machine using Ollama.
- **Event Creation & Management**: Create and manage single dialogue events.
- **Multi-Round Conversations**: Support for iterative rounds of input and AI-powered synthesis.
- **Real-time Visualization**: Interactive visualizations for sentiment, word clouds, and consensus.
- **Admin-in-the-Loop**: Administrators review and approve AI-generated prompts before they are sent to participants.
- **Dynamic Reporting**: Flexible options to export raw data and generate formatted reports.

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

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- Ollama (for local AI processing)
- Kubernetes (for production)

### Development Setup

1. Clone the repository
2. Install Ollama and pull the required model: `ollama pull llama3.2:latest`
3. Run development environment: `./scripts/dev-setup.sh`
4. Start all services: `./start.sh`
5. Access frontend: http://localhost:3000
6. Access API docs: http://localhost:8000/docs
7. Check Ollama health: http://localhost:11434

### Backend-Only Mode

For backend development without frontend:
```bash
./start.sh --backend-only
```

## Recent Progress (August 2025)

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

## Development Phases

- **Phase 1** (Months 1-6): Core Platform
- **Phase 2** (Months 7-12): Advanced AI & Visualization
- **Phase 3** (Months 13-18): Integration & Scale
- **Phase 4** (Months 19-24): Civic Companion Evolution

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## License

[License details to be added] 