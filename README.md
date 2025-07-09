# Census

An AI-powered platform that enhances civic discourse by processing natural language input from participants and generating structured insights about consensus, alignment, and opportunities for generative dialogue.

## Overview

The Civic Sense-Making Platform operates as a distributed system with microservices architecture, designed to handle real-time natural language processing, persistent user profile management, and complex dialogue analysis at scale.

### Key Features

- **Event Creation & Management**: Create civic events with customizable inquiries
- **Natural Language Processing**: Voice and text input processing with semantic analysis
- **Polis-Style Clustering**: Advanced opinion clustering and visualization
- **Persistent Civic Profiles**: User-owned data with cross-event persistence
- **Multi-Round Conversations**: Support for iterative rounds of input and synthesis
- **Real-time Visualization**: Interactive opinion landscapes and consensus mapping

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
- Kubernetes (for production)

### Development Setup

1. Clone the repository
2. Run development environment: `./scripts/dev-setup.sh`
3. Start services: `docker-compose up -d`
4. Access frontend: http://localhost:3000
5. Access API docs: http://localhost:8000/docs

## Development Phases

- **Phase 1** (Months 1-6): Core Platform
- **Phase 2** (Months 7-12): Advanced AI & Visualization
- **Phase 3** (Months 13-18): Integration & Scale
- **Phase 4** (Months 19-24): Civic Companion Evolution

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## License

[License details to be added] 