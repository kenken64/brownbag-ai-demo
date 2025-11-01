#!/bin/bash

# YOLO Mode - Run Claude Code without permission prompts
# WARNING: This skips all safety confirmations. Use with caution!

claude --dangerously-skip-permissions "$@"
