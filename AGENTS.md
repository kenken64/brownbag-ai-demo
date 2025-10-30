# Multi-Agent System Configuration

This document describes the multi-agent architecture for the AI-powered cryptocurrency trading system.

## Overview

The system is organized into four specialized agents, each responsible for different aspects of the trading platform:

1. **Frontend Developer** - User interface and real-time visualization
2. **Backend Developer** - API, database, and system infrastructure
3. **Trading Systems Developer** - Trading strategies and execution
4. **AI/ML Developer** - Predictive models and machine learning

## Agent Details

### 1. Frontend Developer Agent

- **Model:** claude-opus-4-1-20250805
- **Specialization:** React, TypeScript, UI/UX, WebSocket integration
- **Workspace:** `src/frontend/`
- **Context Files:** `src/frontend/**`, `package.json`

**Responsibilities:**
- Real-time trading interface development
- WebSocket integration for live market data
- Performance optimization
- Responsive design implementation

**Documentation:** [src/frontend/README.md](src/frontend/README.md)

---

### 2. Backend Developer Agent

- **Model:** claude-opus-4-1-20250805
- **Specialization:** Node.js, Python, APIs, Database design
- **Workspace:** `src/backend/`
- **Context Files:** `src/backend/**`, `requirements.txt`

**Responsibilities:**
- RESTful API development
- Database schema design and optimization
- Security implementation
- External exchange integration
- Error handling and validation

**Documentation:** [src/backend/README.md](src/backend/README.md)

---

### 3. Trading Systems Developer Agent

- **Model:** claude-opus-4-1-20250805
- **Specialization:** Trading algorithms, Market analysis, Risk management
- **Workspace:** `src/trading/`, `strategies/`
- **Context Files:** `src/trading/**`, `strategies/**`

**Responsibilities:**
- Trading strategy implementation
- Technical indicator development
- Risk management systems
- Backtesting framework
- Order execution logic

**Documentation:** [src/trading/README.md](src/trading/README.md)

---

### 4. AI/ML Developer Agent

- **Model:** claude-opus-4-1-20250805
- **Specialization:** Machine Learning, Deep Learning, Predictive modeling
- **Workspace:** `src/ml/`, `models/`
- **Context Files:** `src/ml/**`, `models/**`

**Responsibilities:**
- Feature engineering
- Model development and training
- Real-time inference
- Model evaluation and monitoring
- Integration with trading systems

**Documentation:** [src/ml/README.md](src/ml/README.md)

---

## Agent Collaboration

### Data Flow

```
Market Data → Backend → AI/ML Agent → Trading Agent → Backend → Frontend
                ↓                          ↓
            Database                   Execution
```

### Integration Points

1. **Backend ↔ Frontend**
   - REST APIs for data retrieval
   - WebSocket for real-time updates
   - Authentication and session management

2. **Backend ↔ AI/ML**
   - Feature data pipelines
   - Model inference endpoints
   - Performance metrics collection

3. **AI/ML ↔ Trading**
   - Prediction signals
   - Market sentiment analysis
   - Risk score calculation

4. **Trading ↔ Backend**
   - Order execution requests
   - Position management
   - Trade history storage

## Configuration

Agent configuration is defined in `agents-config.yaml`. To modify agent settings:

1. Edit the YAML configuration file
2. Update relevant workspace documentation
3. Reinitialize affected agent workspaces if needed

## Getting Started

Each agent workspace contains:
- `README.md` - Agent-specific documentation
- Directory structure for organized development
- `.gitkeep` files to preserve empty directories

To work with a specific agent:
1. Navigate to the agent's workspace directory
2. Review the README.md for responsibilities and guidelines
3. Follow the directory structure conventions
4. Ensure code adheres to agent specialization

## Development Workflow

1. **Planning Phase**
   - Identify which agent(s) should handle the task
   - Review agent responsibilities and context

2. **Implementation Phase**
   - Work within the designated agent workspace
   - Follow agent-specific guidelines
   - Coordinate with other agents at integration points

3. **Testing Phase**
   - Unit tests within agent workspace
   - Integration tests across agent boundaries
   - End-to-end testing through the full pipeline

4. **Deployment Phase**
   - Deploy backend and ML services
   - Deploy frontend to hosting platform
   - Monitor agent-specific metrics

## Best Practices

- Keep agent workspaces isolated to maintain clear boundaries
- Use shared types/interfaces for cross-agent communication
- Document integration points clearly
- Follow agent-specific coding conventions
- Maintain comprehensive test coverage within each workspace

## Status

**Initialization Status:** ✓ Complete

All agent workspaces have been initialized and are ready for development.

**Created:** 2025-10-30
**Last Updated:** 2025-10-30
