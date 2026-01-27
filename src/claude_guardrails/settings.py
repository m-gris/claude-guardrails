"""
Claude Code settings.local.json management.

Handles reading/writing hook registrations in Claude Code's settings file.
"""

import json
from dataclasses import dataclass
from typing import Any

from claude_guardrails.paths import SETTINGS_LOCAL
from claude_guardrails.types import HookEvent


@dataclass(frozen=True)
class HookSpec:
    """Specification for a hook to register."""

    event: HookEvent
    matcher: str | None  # Tool matcher (e.g., "Read", "WebFetch")
    command: str  # Command to run


def load_settings() -> dict[str, Any]:
    """Load settings.local.json, returning empty dict if not exists."""
    if not SETTINGS_LOCAL.exists():
        return {}
    return json.loads(SETTINGS_LOCAL.read_text())


def save_settings(settings: dict[str, Any]) -> None:
    """Save settings to settings.local.json."""
    SETTINGS_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_LOCAL.write_text(json.dumps(settings, indent=2) + "\n")


def register_hook(spec: HookSpec) -> bool:
    """
    Register a hook in settings.local.json.

    Returns True if hook was added, False if already exists.
    """
    settings = load_settings()

    # Ensure hooks structure exists
    event_key = spec.event.value
    if "hooks" not in settings:
        settings["hooks"] = {}
    if event_key not in settings["hooks"]:
        settings["hooks"][event_key] = []

    event_hooks = settings["hooks"][event_key]

    # Build the hook entry
    hook_entry = {"type": "command", "command": spec.command}

    # Find or create the matcher group
    target_group = None
    for group in event_hooks:
        group_matcher = group.get("matcher")
        if group_matcher == spec.matcher:
            target_group = group
            break

    if target_group is None:
        # Create new group
        if spec.matcher:
            target_group = {"matcher": spec.matcher, "hooks": []}
        else:
            target_group = {"hooks": []}
        event_hooks.append(target_group)

    # Check if hook already registered
    for existing in target_group["hooks"]:
        if existing.get("command") == spec.command:
            return False  # Already exists

    # Add the hook
    target_group["hooks"].append(hook_entry)
    save_settings(settings)
    return True


def unregister_hook(spec: HookSpec) -> bool:
    """
    Remove a hook from settings.local.json.

    Returns True if hook was removed, False if not found.
    """
    settings = load_settings()

    event_key = spec.event.value
    if "hooks" not in settings:
        return False
    if event_key not in settings["hooks"]:
        return False

    event_hooks = settings["hooks"][event_key]

    # Find the matcher group
    for group in event_hooks:
        group_matcher = group.get("matcher")
        if group_matcher == spec.matcher:
            # Find and remove the hook
            original_len = len(group["hooks"])
            group["hooks"] = [
                h for h in group["hooks"] if h.get("command") != spec.command
            ]
            if len(group["hooks"]) < original_len:
                # Clean up empty groups
                if not group["hooks"]:
                    event_hooks.remove(group)
                save_settings(settings)
                return True

    return False


def is_hook_registered(spec: HookSpec) -> bool:
    """Check if a hook is registered."""
    settings = load_settings()
    event_key = spec.event.value

    if "hooks" not in settings:
        return False
    if event_key not in settings["hooks"]:
        return False

    for group in settings["hooks"][event_key]:
        if group.get("matcher") == spec.matcher:
            for hook in group["hooks"]:
                if hook.get("command") == spec.command:
                    return True

    return False
