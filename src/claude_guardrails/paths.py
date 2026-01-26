"""
Path constants and utilities for claude-guardrails.

All paths are relative to ~/.claude/ to match Claude Code's conventions.
"""

from pathlib import Path

# Base directories
CLAUDE_HOME = Path.home() / ".claude"
GUARDRAILS_DIR = CLAUDE_HOME / "guardrails"
HOOKS_DIR = CLAUDE_HOME / "hooks"

# Reminders
REMINDERS_CONFIG = GUARDRAILS_DIR / "reminders.json"
REMINDERS_STATE_DIR = GUARDRAILS_DIR / "state"

# Progressive disclosure
PROGRESSIVE_CONFIG = GUARDRAILS_DIR / "progressive-disclosure.yaml"

# URL discipline
URL_ALLOWLIST = GUARDRAILS_DIR / "url-allowlist.txt"

# Settings file (Claude Code's local settings)
SETTINGS_LOCAL = CLAUDE_HOME / "settings.local.json"


def ensure_dirs() -> None:
    """Create required directories if they don't exist."""
    GUARDRAILS_DIR.mkdir(parents=True, exist_ok=True)
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    REMINDERS_STATE_DIR.mkdir(parents=True, exist_ok=True)
