"""
Shared domain types for claude-guardrails.

Enums provide exhaustiveness checking and prevent stringly-typed errors.
"""

from enum import Enum


class HookEvent(Enum):
    """Claude Code hook event types."""

    SESSION_START = "SessionStart"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"


class CopyStatus(Enum):
    """Result status for file copy operations."""

    COPIED = "copied"
    SKIPPED = "skipped"
    CONFLICT = "conflict"
