@echo off
REM YOLO Mode - Run Claude Code without permission prompts
REM WARNING: This skips all safety confirmations. Use with caution!

claude --dangerously-skip-permissions %*
