# Check Development Status for Sub-Agents

Check the current development status and progress for all specialized sub-agents in the multi-agent system.

## Overview

Analyze the workspace directories and provide a comprehensive status report for each agent:
- **Frontend Developer** (`src/frontend/`)
- **Backend Developer** (`src/backend/`)
- **Trading Systems Developer** (`src/trading/`, `strategies/`)
- **AI/ML Developer** (`src/ml/`, `models/`)

## Status Check Process

1. **Scan Agent Workspaces**
   - Check each agent's directory structure
   - Count files and subdirectories
   - Identify what has been implemented
   - Note what's still missing or incomplete

2. **Analyze Current Progress**
   For each agent workspace, check:
   - Files created vs expected structure
   - Implementation completeness
   - Dependencies installed (package.json, requirements.txt, etc.)
   - Test coverage
   - Documentation status

3. **Check PRP Progress** (if applicable)
   - Look for active PRP files in `PRPs/` directory
   - Match completed tasks against agent responsibilities
   - Identify pending tasks

4. **Git Status Integration**
   - Check modified files per agent workspace
   - Identify uncommitted changes
   - Show recent commits affecting each workspace

## Report Format

Generate a structured status report:

### 🎨 Frontend Developer Status
- **Workspace:** `src/frontend/`
- **Structure Status:** ✓ Initialized / ⚠️ Partial / ✗ Not Started
- **Files Created:** [count] files
- **Key Components:**
  - [ ] Components directory
  - [ ] Pages/Routes
  - [ ] State management
  - [ ] WebSocket integration
  - [ ] UI/UX implementation
- **Dependencies:** ✓ Configured / ⚠️ Missing
- **Tests:** [count] test files
- **Last Activity:** [most recent file modification]
- **Completion:** [percentage]%

### ⚙️ Backend Developer Status
- **Workspace:** `src/backend/`
- **Structure Status:** ✓ Initialized / ⚠️ Partial / ✗ Not Started
- **Files Created:** [count] files
- **Key Components:**
  - [ ] API endpoints
  - [ ] Database models
  - [ ] Authentication
  - [ ] Exchange integrations
  - [ ] Order execution engine
- **Dependencies:** ✓ Configured / ⚠️ Missing
- **Tests:** [count] test files
- **Last Activity:** [most recent file modification]
- **Completion:** [percentage]%

### 📈 Trading Systems Developer Status
- **Workspace:** `src/trading/`, `strategies/`
- **Structure Status:** ✓ Initialized / ⚠️ Partial / ✗ Not Started
- **Files Created:** [count] files
- **Key Components:**
  - [ ] Trading strategies
  - [ ] Risk management
  - [ ] Backtesting framework
  - [ ] Technical indicators
  - [ ] Position sizing
- **Strategies Implemented:** [count] strategies
- **Tests:** [count] test files
- **Last Activity:** [most recent file modification]
- **Completion:** [percentage]%

### 🤖 AI/ML Developer Status
- **Workspace:** `src/ml/`, `models/`
- **Structure Status:** ✓ Initialized / ⚠️ Partial / ✗ Not Started
- **Files Created:** [count] files
- **Key Components:**
  - [ ] Price prediction models
  - [ ] Sentiment analysis
  - [ ] Pattern recognition
  - [ ] RL trading agent
  - [ ] Model evaluation pipeline
- **Models Trained:** [count] models in `models/`
- **Tests:** [count] test files
- **Last Activity:** [most recent file modification]
- **Completion:** [percentage]%

### 📊 Overall Project Status
- **Total Files:** [count] across all workspaces
- **Overall Completion:** [percentage]%
- **Active Development:** [agent names with recent activity]
- **Blockers:** [list any identified blockers or missing dependencies]
- **Next Steps:** [recommended actions based on current status]

### 🔄 Recent Activity
- Show last 5 git commits (if in git repo)
- Show most recently modified files per agent
- Highlight any merge conflicts or issues

### ⚠️ Warnings & Recommendations
- Missing dependencies
- Incomplete configurations
- Integration gaps between agents
- Suggested next tasks

## Usage Examples

```bash
# Check status of all agents
claude /status

# The command will automatically scan all agent workspaces and provide a comprehensive report
```

## Notes

- This command is read-only and doesn't modify any files
- Status is based on current file system state
- Completion percentages are estimates based on expected structure
- Use this before starting new work to understand current state
- Helpful for daily standups and progress tracking
