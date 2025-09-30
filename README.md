# AI Crypto Trader - Context Engineering Demo

A demonstration repository showcasing context engineering techniques for AI-assisted development with Claude Code.

## Overview

This repository demonstrates best practices for context engineering when working with AI coding assistants. It includes configuration files and custom commands that help Claude Code understand and work effectively within the project.

## Context Engineering Components

### CLAUDE.md
Project-specific guidance file that provides Claude Code with:
- Project architecture overview
- Development commands and workflows
- Key patterns and conventions

### settings.local.json
Permission configuration for Claude Code operations:
- Approved bash commands (grep, ls, find, pytest, python, etc.)
- Allowed web fetch domains (docs.anthropic.com, github.com)
- Custom security boundaries

### Custom Commands

#### `/execute-prp`
Execute PRP (Project Requirements and Plan) files with structured workflow:
1. **Load PRP** - Read and understand requirements
2. **ULTRATHINK** - Create comprehensive implementation plan
3. **Execute** - Implement all code
4. **Validate** - Run validation commands and fix failures
5. **Complete** - Verify all requirements met

Usage: `/execute-prp <path-to-prp-file>`

## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/kenken64/brownbag-ai-demo.git
cd brownbag-ai-demo
```

2. Open with Claude Code to see context engineering in action

3. The AI assistant will automatically:
   - Load CLAUDE.md for project context
   - Respect permissions in settings.local.json
   - Have access to custom commands like `/execute-prp`

## Context Engineering Best Practices

1. **Clear Documentation** - Maintain CLAUDE.md with architecture and commands
2. **Permission Boundaries** - Define allowed operations in settings.local.json
3. **Custom Commands** - Create reusable workflows for common tasks
4. **Structured Planning** - Use PRP files for complex features

## Repository Structure

```
.
├── .claude/
│   └── commands/
│       └── execute-prp.md    # Custom PRP execution command
├── CLAUDE.md                  # Project context for Claude Code
├── settings.local.json        # Permissions configuration
└── README.md                  # This file
```

## Purpose

This repository serves as a reference implementation for:
- Configuring AI coding assistants for optimal productivity
- Establishing clear boundaries and workflows
- Creating reproducible development patterns
- Teaching context engineering concepts

## License

MIT