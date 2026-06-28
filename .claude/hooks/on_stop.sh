#!/bin/bash
# on_stop.sh — Stop hook
# Fires when Claude finishes a session.
# 1. Runs tests for any files changed in this git session
# 2. Appends a session-end summary to Completion_Task_Details.md
# 3. Sends a "task finished" Mac notification

PROJ="/Users/sumhonyou/Documents/AI-Driven-Pose-Estimation-Application-for-Quantifying-Lower-LimbFunction-using-a-Single-Camera"
NOTIFY="$PROJ/.claude/hooks/notify.sh"
LOG="$PROJ/Completion_Task_Details.md"
VENV="$PROJ/backend/.venv/bin"

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "[Stop] Claude session ending at $TIMESTAMP"

# ── 1. DETECT CHANGED FILES ──────────────────────────────────────────────────

# Files changed vs last commit (staged + unstaged)
CHANGED=$(git -C "$PROJ" diff --name-only HEAD 2>/dev/null; git -C "$PROJ" diff --name-only 2>/dev/null)
CHANGED=$(echo "$CHANGED" | sort -u | tr '\n' ' ')
echo "[Stop] Changed files: ${CHANGED:-none}"

FRONTEND_CHANGED=$(git -C "$PROJ" diff --name-only HEAD 2>/dev/null | grep "^frontend/" | head -1)
BACKEND_CHANGED=$(git -C "$PROJ" diff --name-only HEAD 2>/dev/null | grep "^backend/" | head -1)

# ── 2. RUN TESTS ─────────────────────────────────────────────────────────────

TEST_RESULTS=""

if [ -n "$FRONTEND_CHANGED" ]; then
  HAS_TEST=$(cd "$PROJ/frontend" && node -e "const p=require('./package.json'); console.log(p.scripts?.test?'yes':'no')" 2>/dev/null)
  if [ "$HAS_TEST" = "yes" ]; then
    echo "[Stop] Running frontend tests..."
    cd "$PROJ/frontend" && npm test -- --run 2>&1 | tail -10
    [ ${PIPESTATUS[0]} -eq 0 ] && TEST_RESULTS="$TEST_RESULTS Frontend:✅" || TEST_RESULTS="$TEST_RESULTS Frontend:❌"
  else
    TEST_RESULTS="$TEST_RESULTS Frontend:⏭️(no tests yet)"
  fi
fi

if [ -n "$BACKEND_CHANGED" ]; then
  TEST_COUNT=$(find "$PROJ/backend" -name "test_*.py" -o -name "*_test.py" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$TEST_COUNT" -gt 0 ]; then
    echo "[Stop] Running backend tests..."
    source "$VENV/activate" 2>/dev/null || true
    cd "$PROJ/backend" && python -m pytest --tb=short -q 2>&1 | tail -15
    [ ${PIPESTATUS[0]} -eq 0 ] && TEST_RESULTS="$TEST_RESULTS Backend:✅" || TEST_RESULTS="$TEST_RESULTS Backend:❌"
  else
    TEST_RESULTS="$TEST_RESULTS Backend:⏭️(no tests yet)"
  fi
fi

[ -z "$TEST_RESULTS" ] && TEST_RESULTS="No file changes detected"

# ── 3. LOG SESSION END ────────────────────────────────────────────────────────

{
  echo ""
  echo "---"
  echo "## Session End — $TIMESTAMP"
  echo "- **Changed files:** ${CHANGED:-none}"
  echo "- **Test results:** $TEST_RESULTS"
} >> "$LOG"

echo "[Stop] Session summary written to Completion_Task_Details.md"

# ── 4. MAC NOTIFICATION ───────────────────────────────────────────────────────

NOTIF_MSG="Session done. Tests:${TEST_RESULTS}. See Completion_Task_Details.md"
bash "$NOTIFY" "task_finished" "$NOTIF_MSG"

exit 0
