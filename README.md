# Claude Guardrails

Guardrails and hooks for [Claude Code](https://claude.ai/claude-code) — the CLI assistant.

## Features

### 1. Periodic Reminders
Configurable reminders that fire based on turn count OR elapsed time.

- **Dual-trigger**: fires when `turns >= interval` OR `elapsed_seconds >= interval`
- **Per-reminder state**: each reminder tracks its own turn count + timestamp
- **Variable interpolation**: `$CUMULATIVE_TURNS`, `$PID`, `$NOW_ISO`
- **Global turn counter**: built-in, never resets within session

### 2. Progressive Disclosure
Intercepts `Read` tool calls on large JSON/YAML files and suggests `jq`/`yq` exploration.

- Gentle nudge for files 100-250 lines
- Strong nudge (asks confirmation) for files > 250 lines
- Suggests appropriate tool (`jq` for JSON, `yq` for YAML)

### 3. URL Discipline
Validates `WebFetch` URLs to prevent hallucinated/invented paths.

- Allows known entry points (`/`, `/docs/`, `/sitemap.xml`, etc.)
- Prompts for confirmation on deep paths
- Encourages URL discovery over URL invention

## Installation

```bash
# Install hooks (copies to ~/.claude/, does NOT enable)
uvx claude-guardrails install

# Install and enable all guardrails
uvx claude-guardrails install --all
```

## Usage

### Reminders

```bash
# Enable/disable the hook
uvx claude-guardrails reminders enable
uvx claude-guardrails reminders disable

# Manage reminders
uvx claude-guardrails reminders list
uvx claude-guardrails reminders add           # interactive
uvx claude-guardrails reminders add --id turn-marker --turns 1 --seconds 1 --message "<turn n=\"\$CUMULATIVE_TURNS\"/>"
uvx claude-guardrails reminders show <id>
uvx claude-guardrails reminders remove <id>
uvx claude-guardrails reminders reset <id>    # or 'all'
```

### Progressive Disclosure

```bash
uvx claude-guardrails progressive-disclosure enable
uvx claude-guardrails progressive-disclosure disable
uvx claude-guardrails progressive-disclosure status
uvx claude-guardrails progressive-disclosure config
```

### URL Discipline

```bash
uvx claude-guardrails url-discipline enable
uvx claude-guardrails url-discipline disable
uvx claude-guardrails url-discipline status
uvx claude-guardrails url-discipline allow "*.github.com"
uvx claude-guardrails url-discipline list
uvx claude-guardrails url-discipline deny "*.github.com"
```

### Status

```bash
# Show status of all guardrails
uvx claude-guardrails status
```

## Configuration

All configuration lives in `~/.claude/`:

```
~/.claude/
├── hooks/                              # Hook scripts
│   ├── periodic-reminders.sh
│   ├── structured-file-nudge.py
│   └── webfetch-url-discipline.py
├── guardrails/
│   ├── reminders.json                  # Reminder configuration
│   ├── state/                          # Runtime state (turn counts, timestamps)
│   ├── progressive-disclosure.yaml     # (optional) Threshold config
│   └── url-allowlist.txt               # URL allowlist patterns
└── settings.local.json                 # Claude Code settings (hooks registered here)
```

## Example Reminders

```json
{
  "reminders": [
    {
      "id": "turn-marker",
      "interval_turns": 1,
      "interval_seconds": 1,
      "message": "<turn n=\"$CUMULATIVE_TURNS\" pid=\"$PID\" ts=\"$NOW_ISO\"/>"
    },
    {
      "id": "task-check",
      "interval_turns": 10,
      "interval_seconds": 900,
      "message": "<task-check>Review your task list.</task-check>"
    }
  ]
}
```

## Requirements

- Python 3.10+
- `jq` (for reminders hook and progressive disclosure suggestions)
- `yq` (for progressive disclosure on YAML files)

## License

MIT
