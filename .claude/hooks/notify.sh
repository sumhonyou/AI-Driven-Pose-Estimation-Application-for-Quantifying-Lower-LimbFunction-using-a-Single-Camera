#!/bin/bash
# notify.sh — Mac notification utility
# Usage A (from other hooks): notify.sh <type> "<message>"
# Usage B (as Notification hook, reads stdin JSON): notify.sh
#
# Types: permission_needed | task_finished | test_passed | test_failed

PROJ="/Users/sumhonyou/Documents/AI-Driven-Pose-Estimation-Application-for-Quantifying-Lower-LimbFunction-using-a-Single-Camera"

send_notification() {
  local TYPE="$1"
  local MSG="$2"

  case "$TYPE" in
    permission_needed)
      TITLE="⚠️ Claude Needs Permission"
      SUBTITLE="Action Required — Check Terminal"
      SOUND="Funk"
      ;;
    task_finished)
      TITLE="✅ Claude Finished"
      SUBTITLE="Task Complete"
      SOUND="Glass"
      ;;
    test_passed)
      TITLE="🧪 Tests Passed"
      SUBTITLE="All checks green"
      SOUND="Ping"
      ;;
    test_failed)
      TITLE="❌ Tests Failed"
      SUBTITLE="Check output for details"
      SOUND="Basso"
      ;;
    *)
      TITLE="Claude Code"
      SUBTITLE="Notification"
      SOUND="Pop"
      ;;
  esac

  # Sanitize message — remove characters that break osascript
  SAFE_MSG=$(echo "$MSG" | tr -d '"\\' | cut -c1-120)

  osascript -e "display notification \"$SAFE_MSG\" with title \"$TITLE\" subtitle \"$SUBTITLE\" sound name \"$SOUND\"" 2>/dev/null
}

# ---- Usage B: called as Notification hook (stdin JSON) ----
if [ -z "$1" ]; then
  INPUT=$(cat)
  RAW_MSG=$(echo "$INPUT" | jq -r '.message // ""' 2>/dev/null)
  TITLE_IN=$(echo "$INPUT" | jq -r '.title // ""' 2>/dev/null)

  # Infer notification type from content
  MSG_LOWER=$(echo "$RAW_MSG $TITLE_IN" | tr '[:upper:]' '[:lower:]')
  if echo "$MSG_LOWER" | grep -qE "permission|allow|approve|waiting|input"; then
    TYPE="permission_needed"
  else
    TYPE="task_finished"
  fi

  send_notification "$TYPE" "${RAW_MSG:-Claude needs your attention}"
  exit 0
fi

# ---- Usage A: called directly with args ----
send_notification "$1" "${2:-}"
