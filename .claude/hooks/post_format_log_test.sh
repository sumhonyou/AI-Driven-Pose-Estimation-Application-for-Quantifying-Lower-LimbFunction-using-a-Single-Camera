#!/bin/bash
# post_format_log_test.sh — PostToolUse handler for Edit / Write / NotebookEdit
# 1. Runs Prettier (JS/TS) or Black+isort (Python) on the changed file
# 2. Appends a log entry to Completion_Task_Details.md
# 3. Runs the relevant test suite if test files exist

PROJ="/Users/sumhonyou/Documents/AI-Driven-Pose-Estimation-Application-for-Quantifying-Lower-LimbFunction-using-a-Single-Camera"
NOTIFY="$PROJ/.claude/hooks/notify.sh"
LOG="$PROJ/Completion_Task_Details.md"
VENV="$PROJ/backend/.venv/bin"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null)

# Only process code-change tools
if [[ "$TOOL_NAME" != "Edit" && "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "NotebookEdit" ]]; then
  exit 0
fi

# Extract file path (Edit/Write use file_path, NotebookEdit uses notebook_path)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // ""' 2>/dev/null)
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# ── 1. FORMAT ────────────────────────────────────────────────────────────────

if [[ "$FILE_PATH" =~ \.(js|jsx|ts|tsx|css|json|html|md)$ ]]; then
  # Prettier for frontend files
  if [ -f "$PROJ/frontend/node_modules/.bin/prettier" ]; then
    "$PROJ/frontend/node_modules/.bin/prettier" --write "$FILE_PATH" 2>/dev/null
  elif command -v npx &>/dev/null; then
    # Fallback: use npx (may download on first run)
    cd "$PROJ/frontend" && npx --yes prettier --write "$FILE_PATH" 2>/dev/null
  fi
elif [[ "$FILE_PATH" =~ \.py$ ]]; then
  # Black + isort for Python files
  # Prefer venv binaries; fall back to Anaconda PATH
  BLACK_BIN="$VENV/black"
  ISORT_BIN="$VENV/isort"
  [ ! -f "$BLACK_BIN" ] && BLACK_BIN=$(which black 2>/dev/null)
  [ ! -f "$ISORT_BIN" ] && ISORT_BIN=$(which isort 2>/dev/null)

  if [ -n "$BLACK_BIN" ] && [ -f "$BLACK_BIN" ]; then
    "$BLACK_BIN" "$FILE_PATH" 2>/dev/null
  fi

  if [ -n "$ISORT_BIN" ] && [ -f "$ISORT_BIN" ]; then
    "$ISORT_BIN" "$FILE_PATH" 2>/dev/null
  fi
fi

# ── 2. LOG TO Completion_Task_Details.md ─────────────────────────────────────

{
  echo ""
  echo "### $TIMESTAMP | $TOOL_NAME"
  echo "- **File:** \`$FILE_PATH\`"
  # Capture the description from the tool input (what Claude said it was doing)
  DESCRIPTION=$(echo "$INPUT" | jq -r '.tool_input.description // ""' 2>/dev/null)
  [ -n "$DESCRIPTION" ] && echo "- **Action:** $DESCRIPTION"
} >> "$LOG"

# ── 3. RUN TESTS ─────────────────────────────────────────────────────────────

RUN_FRONTEND=false
RUN_BACKEND=false

[[ "$FILE_PATH" == "$PROJ/frontend/"* ]] && RUN_FRONTEND=true
[[ "$FILE_PATH" == "$PROJ/backend/"* ]] && RUN_BACKEND=true

if $RUN_FRONTEND; then
  # Check if test script exists in package.json
  HAS_TEST=$(cd "$PROJ/frontend" && node -e "const p=require('./package.json'); console.log(p.scripts?.test?'yes':'no')" 2>/dev/null)
  if [ "$HAS_TEST" = "yes" ]; then
    cd "$PROJ/frontend" && npm test -- --run 2>&1 | tail -15
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
      bash "$NOTIFY" "test_passed" "Frontend tests passed after editing $(basename "$FILE_PATH")"
    else
      bash "$NOTIFY" "test_failed" "Frontend tests FAILED after editing $(basename "$FILE_PATH")"
    fi
  fi
fi

if $RUN_BACKEND; then
  # Check if any pytest test files exist
  TEST_COUNT=$(find "$PROJ/backend" -name "test_*.py" -o -name "*_test.py" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$TEST_COUNT" -gt 0 ]; then
    source "$VENV/activate" 2>/dev/null || true
    cd "$PROJ/backend" && python -m pytest --tb=short -q 2>&1 | tail -20
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
      bash "$NOTIFY" "test_passed" "Backend tests passed after editing $(basename "$FILE_PATH")"
    else
      bash "$NOTIFY" "test_failed" "Backend tests FAILED after editing $(basename "$FILE_PATH")"
    fi
  fi
fi

exit 0
