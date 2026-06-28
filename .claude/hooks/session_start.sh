#!/bin/bash
# session_start.sh — SessionStart hook
# Injects context summary into Claude's conversation at the start of each session.
# Claude reads this output to understand where the project is, what was done last,
# and what the next task should be. Claude will also suggest rule updates if needed.

PROJ="/Users/sumhonyou/Documents/AI-Driven-Pose-Estimation-Application-for-Quantifying-Lower-LimbFunction-using-a-Single-Camera"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              SESSION START — PROJECT CONTEXT BRIEF           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Current task phase ───────────────────────────────────────────────────────
echo "## Current Task Status (task.md — top 40 lines)"
head -40 "$PROJ/task.md" 2>/dev/null
echo ""

# ── Recent completions (last 80 lines of log) ────────────────────────────────
echo "## Recent Completion Log (last 80 lines of Completion_Task_Details.md)"
tail -80 "$PROJ/Completion_Task_Details.md" 2>/dev/null
echo ""

# ── Recent git history ───────────────────────────────────────────────────────
echo "## Recent Git History (last 15 commits)"
git -C "$PROJ" log --oneline -15 2>/dev/null
echo ""

# ── Current rules ────────────────────────────────────────────────────────────
echo "## Active Coding Rules (rules.md)"
cat "$PROJ/.claude/rules.md" 2>/dev/null
echo ""

# ── Unstaged / staged changes ────────────────────────────────────────────────
echo "## Current Git Status"
git -C "$PROJ" status --short 2>/dev/null
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    INSTRUCTIONS FOR CLAUDE                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Summarize in 3-5 bullets what was completed in previous sessions."
echo "2. State clearly which phase and task is next based on task.md."
echo "3. If you notice any recurring patterns or missing rules from previous"
echo "   sessions that would help future development, PROPOSE them to the user"
echo "   before modifying rules.md. Do NOT auto-edit rules.md without approval."
echo "4. Ask the user what they want to work on today before starting any code."
