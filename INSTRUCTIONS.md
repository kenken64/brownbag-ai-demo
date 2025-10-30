## Complete Setup Guide: Claude Code with Multi-Agent Development Team

### Part 1: Installing Claude Code

1. **Prerequisites**
   - Claude Pro or Team subscription (recommended) OR Anthropic API key
   - Node.js and npm installed on your system
   - Terminal/Command Prompt access

2. **Installation Steps**
   ```bash
   # Install Claude Code via npm
   npm install -g @anthropic-ai/claude-code
   ```

3. **Configuration**
   ```bash
   # If using Claude Pro/Team subscription, authentication is handled automatically
   # No API key configuration needed!

   # If using Anthropic API key (optional):
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

4. **Verify Installation**
   ```bash
   claude --version
   claude test
   ```

### Part 2: Creating 4 Specialized Sub-Agents

Create a configuration file `agents-config.yaml`:

```yaml
agents:
  frontend-dev:
    name: "Frontend Developer"
    model: "claude-opus-4-1-20250805"
    specialization: "React, TypeScript, UI/UX, WebSocket integration"
    context_files:
      - "src/frontend/**"
      - "package.json"
    instructions: |
      You are a senior frontend developer specializing in React and TypeScript.
      Focus on creating responsive, real-time trading interfaces.
      Prioritize performance and user experience.

  backend-dev:
    name: "Backend Developer"
    model: "claude-opus-4-1-20250805"
    specialization: "Node.js, Python, APIs, Database design"
    context_files:
      - "src/backend/**"
      - "requirements.txt"
    instructions: |
      You are a senior backend developer specializing in scalable API design.
      Focus on security, performance, and reliability for financial applications.
      Implement proper error handling and data validation.

  trading-dev:
    name: "Trading Systems Developer"
    model: "claude-opus-4-1-20250805"
    specialization: "Trading algorithms, Market analysis, Risk management"
    context_files:
      - "src/trading/**"
      - "strategies/**"
    instructions: |
      You are a quantitative developer with expertise in trading systems.
      Focus on implementing robust trading strategies, risk management, and market analysis.
      Ensure all financial calculations are precise and tested.

  ai-dev:
    name: "AI/ML Developer"
    model: "claude-opus-4-1-20250805"
    specialization: "Machine Learning, Deep Learning, Predictive modeling"
    context_files:
      - "src/ml/**"
      - "models/**"
    instructions: |
      You are an AI/ML engineer specializing in financial prediction models.
      Focus on feature engineering, model optimization, and real-time inference.
      Implement proper model evaluation and monitoring.
```

### Part 3: Initialize Agents

In Claude Code, run the following prompt:

```
initialize all the sub agents based on the agents-config.yaml
```

This will:
- Create all necessary directory structures for each agent workspace
- Set up `src/frontend/`, `src/backend/`, `src/trading/`, and `src/ml/` directories
- Create subdirectories specific to each agent's needs
- Generate README.md documentation for each agent workspace
- Create an `AGENTS.md` file with comprehensive multi-agent system documentation
- Update `CLAUDE.md` with architecture information

The initialization process creates:
- **Frontend Agent**: components, pages, hooks, services, store, utils, types
- **Backend Agent**: api, controllers, models, services, middleware, utils, config, tests
- **Trading Agent**: strategies, indicators, risk, execution, backtest, signals, utils
- **AI/ML Agent**: features, models, training, inference, evaluation, preprocessing, utils
- **Additional folders**: `strategies/` and `models/` for trading and ML artifacts

### Part 4: Create the Main PRP File

Create `PRPs/ubs-ai-crypto-trading-bot.md`:

```markdown
# AI Crypto Trading Bot Development Plan

## Project Overview
Build a comprehensive AI-powered cryptocurrency trading bot with real-time analysis.

## Task Delegation

### Frontend Tasks (@frontend-dev)
- [ ] Create React dashboard with real-time charts
- [ ] Implement WebSocket connections for live data
- [ ] Build portfolio management interface
- [ ] Design trading controls and order placement UI
- [ ] Create performance analytics dashboard

### Backend Tasks (@backend-dev)
- [ ] Set up Express/FastAPI server
- [ ] Implement exchange API integrations (Binance, Coinbase)
- [ ] Create database schema for trades and analytics
- [ ] Build authentication and authorization system
- [ ] Implement order execution engine

### Trading Tasks (@trading-dev)
- [ ] Develop trading strategy modules
- [ ] Implement risk management system
- [ ] Create backtesting framework
- [ ] Build position sizing algorithms
- [ ] Implement stop-loss and take-profit mechanisms

### AI/ML Tasks (@ai-dev)
- [ ] Build price prediction models
- [ ] Implement sentiment analysis for crypto news
- [ ] Create pattern recognition system
- [ ] Develop reinforcement learning trading agent
- [ ] Build model evaluation and monitoring pipeline

## Execution Timeline
- Frontend: ~40 hours
- Backend: ~50 hours
- Trading Logic: ~35 hours
- AI/ML Models: ~45 hours
- Integration & Testing: ~30 hours
- **Total Estimated: ~200 hours**
```

### Part 5: Execute with Duration Estimation

```bash
# Estimate execution time for the entire PRP
claude /estimate-duration PRPs/ubs-ai-crypto-trading-bot.md

# This will output something like:
# Estimated Duration Analysis:
# - Frontend Tasks: 40-50 hours
# - Backend Tasks: 45-55 hours
# - Trading Tasks: 30-40 hours
# - AI/ML Tasks: 40-50 hours
# - Total Project: 155-195 hours
# - Parallel Execution: 50-60 hours (with 4 agents)
```

### Part 6: Execute PRP with Task Delegation

```bash
# Execute the main PRP with automatic task delegation
claude execute-prp PRPs/ubs-ai-crypto-trading-bot.md --delegate-auto

# Or manually delegate to specific agents
claude execute-prp PRPs/ubs-ai-crypto-trading-bot.md \
  --delegate frontend:frontend-dev \
  --delegate backend:backend-dev \
  --delegate trading:trading-dev \
  --delegate ai:ai-dev
```

### Part 7: Custom Slash Commands Setup

Create a `.claude-code-commands` file:

```json
{
  "commands": {
    "/execute-prp": {
      "action": "execute_prp",
      "params": ["file_path"],
      "delegation": true
    },
    "/estimate": {
      "action": "estimate_duration",
      "params": ["file_path"]
    },
    "/status": {
      "action": "show_agent_status",
      "params": []
    }
  }
}
```

### Part 8: Running the Complete Workflow

```bash
# Start Claude Code in interactive mode
claude interactive

# In the Claude Code prompt:
> /estimate PRPs/ai-crypto-trading-bot.md
> /execute-prp PRPs/ai-crypto-trading-bot.md delegate frontend to frontend-dev
> /execute-prp PRPs/ai-crypto-trading-bot.md delegate backend to backend-dev
> /execute-prp PRPs/ai-crypto-trading-bot.md delegate trading to trading-dev
> /execute-prp PRPs/ai-crypto-trading-bot.md delegate ai to ai-dev

# Monitor progress
> /status
```

### Part 9: Monitoring and Coordination

```bash
# Create a monitoring script
cat > monitor-agents.sh << 'EOF'
#!/bin/bash
claude status --all-agents
claude logs --tail 50
claude progress PRPs/ubs-ai-crypto-trading-bot.md
EOF

chmod +x monitor-agents.sh
./monitor-agents.sh
```

### Additional Tips:

1. **Parallel Execution**: Claude Code can run agents in parallel to reduce total execution time

2. **Progress Tracking**: Use `claude progress` to see real-time updates

3. **Agent Communication**: Agents can share context through a shared workspace:
   ```bash
   claude workspace create --shared
   ```

4. **Error Handling**: Set up retry logic:
   ```bash
   claude config --set max_retries=3
   claude config --set retry_delay=30
   ```

5. **Cost Optimization**: Monitor API usage:
   ```bash
   claude usage --detailed
   ```

This setup provides a complete multi-agent development environment where each specialized agent can work on their domain while Claude Code coordinates the overall project execution. The system can estimate durations and automatically delegate tasks based on the PRP markdown specifications.