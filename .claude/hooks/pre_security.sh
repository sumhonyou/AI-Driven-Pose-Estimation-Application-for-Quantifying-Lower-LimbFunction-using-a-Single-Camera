#!/bin/bash
# pre_security.sh — PreToolUse security check
# Reads JSON from stdin, checks for dangerous patterns in Bash commands,
# shows a Mac dialog for user approval when flagged.
# Exit 0 = allow, Exit 2 = block (stdout becomes the reason shown to Claude)

PROJ="/Users/sumhonyou/Documents/AI-Driven-Pose-Estimation-Application-for-Quantifying-Lower-LimbFunction-using-a-Single-Camera"
NOTIFY="$PROJ/.claude/hooks/notify.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null)

# Only inspect Bash tool calls
if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)

# Use Python to check dangerous patterns (avoids bash 3.2 associative array limits)
RESULT=$(python3 - "$COMMAND" <<'PYEOF'
import sys, re

command = sys.argv[1] if len(sys.argv) > 1 else ""

# (pattern_regex, human_reason)
CHECKS = [
    (r"rm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+/",           "Recursive force-delete starting at root /"),
    (r"rm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+~",            "Recursive force-delete in home directory"),
    (r"git\s+push\s+(--force|-f)\b",                 "Force push — overwrites remote history"),
    (r"git\s+reset\s+--hard",                        "Hard reset — destroys uncommitted changes"),
    (r"git\s+checkout\s+--\s+\.",                    "Discard all working tree changes"),
    (r"git\s+restore\s+\.",                          "Discard all working tree changes"),
    (r"git\s+clean\s+-[a-zA-Z]*f",                  "Delete all untracked files"),
    (r"--no-verify",                                 "Skip git hooks (bypasses safety checks)"),
    (r"\bDROP\s+TABLE\b",                            "Destructive SQL: DROP TABLE"),
    (r"\bDROP\s+DATABASE\b",                         "Destructive SQL: DROP DATABASE"),
    (r"\bTRUNCATE\s+TABLE\b",                        "Destructive SQL: TRUNCATE TABLE"),
    (r"curl\s+.*\|\s*(bash|sh)\b",                   "Remote code execution via curl"),
    (r"wget\s+.*\|\s*(bash|sh)\b",                   "Remote code execution via wget"),
]

for pattern, reason in CHECKS:
    if re.search(pattern, command, re.IGNORECASE):
        print(reason)
        sys.exit(0)

sys.exit(1)
PYEOF
)

PATTERN_MATCHED=$?

if [ $PATTERN_MATCHED -eq 0 ] && [ -n "$RESULT" ]; then
  REASON="$RESULT"
  # Truncate command for display
  DISPLAY_CMD=$(echo "$COMMAND" | head -c 200)

  # Send permission notification
  bash "$NOTIFY" "permission_needed" "Claude wants to run a flagged command. Check dialog." 2>/dev/null

  # Show AppleScript dialog
  DIALOG_RESULT=$(osascript 2>/dev/null <<APPLESCRIPT
tell application "System Events"
  activate
  set theResult to display dialog "⚠️ Security Warning

Claude wants to run:

${DISPLAY_CMD}

Risk: ${REASON}

Allow or Block?" ¬
    with title "Claude Code — Security Check" ¬
    buttons {"Block", "Allow"} ¬
    default button "Block" ¬
    with icon caution
  return button returned of theResult
end tell
APPLESCRIPT
  )

  DIALOG_EXIT=$?

  # If dialog failed (headless), block by default
  if [ $DIALOG_EXIT -ne 0 ]; then
    echo "Security dialog failed — blocked by default. Risk: $REASON"
    exit 2
  fi

  if [ "$DIALOG_RESULT" = "Allow" ]; then
    echo "[Security] User approved flagged command. Risk: $REASON" >&2
    exit 0
  else
    echo "Blocked by security check. Risk: $REASON. Command: $DISPLAY_CMD"
    exit 2
  fi
fi

exit 0
