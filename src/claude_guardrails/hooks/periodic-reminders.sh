#!/usr/bin/env bash
# Periodic Reminders Engine for Claude Code
# Reads config from ~/.claude/guardrails/reminders.json
# Tracks state per reminder independently + global cumulative turn count

set -euo pipefail

# Configuration paths (relative to ~/.claude)
CLAUDE_HOME="${HOME}/.claude"
CONFIG_FILE="${CLAUDE_HOME}/guardrails/reminders.json"
STATE_DIR="${CLAUDE_HOME}/guardrails/state"
GLOBAL_STATE="${STATE_DIR}/_global.state"

mkdir -p "$STATE_DIR"

# Require jq
if ! command -v jq &>/dev/null; then
    exit 0  # Silent fail if jq not available
fi

# Require config
if [[ ! -f "$CONFIG_FILE" ]]; then
    exit 0
fi

NOW=$(date +%s)
NOW_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
PID=$$

# ============================================================================
# Global cumulative turn counter (never resets within process)
# ============================================================================
CUMULATIVE_TURNS=0
if [[ -f "$GLOBAL_STATE" ]]; then
    source "$GLOBAL_STATE"
fi
CUMULATIVE_TURNS=$((CUMULATIVE_TURNS + 1))
echo "CUMULATIVE_TURNS=$CUMULATIVE_TURNS" > "$GLOBAL_STATE"

# ============================================================================
# Process each reminder
# ============================================================================
jq -c '.reminders[]' "$CONFIG_FILE" | while read -r reminder; do
    ID=$(echo "$reminder" | jq -r '.id')
    INTERVAL_TURNS=$(echo "$reminder" | jq -r '.interval_turns')
    INTERVAL_SECONDS=$(echo "$reminder" | jq -r '.interval_seconds')
    MESSAGE=$(echo "$reminder" | jq -r '.message')

    STATE_FILE="${STATE_DIR}/${ID}.state"

    # Read state (defaults for first run)
    TURN_COUNT=0
    LAST_REMINDER=$NOW
    if [[ -f "$STATE_FILE" ]]; then
        source "$STATE_FILE"
    fi

    TURN_COUNT=$((TURN_COUNT + 1))
    ELAPSED=$((NOW - LAST_REMINDER))

    # Check if reminder is due
    REMIND=false
    if [[ $TURN_COUNT -ge $INTERVAL_TURNS ]] || [[ $ELAPSED -ge $INTERVAL_SECONDS ]]; then
        REMIND=true
        TURN_COUNT=0
        LAST_REMINDER=$NOW
    fi

    # Save state
    cat > "$STATE_FILE" <<EOF
TURN_COUNT=$TURN_COUNT
LAST_REMINDER=$LAST_REMINDER
EOF

    # Output reminder if due (with variable substitution)
    if [[ "$REMIND" == "true" ]]; then
        echo "$MESSAGE" | sed \
            -e "s/\$CUMULATIVE_TURNS/$CUMULATIVE_TURNS/g" \
            -e "s/\$PID/$PID/g" \
            -e "s/\$NOW_ISO/$NOW_ISO/g"
    fi
done
