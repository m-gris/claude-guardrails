#!/usr/bin/env python3
"""
Structured File Nudge Hook

Intercepts Read tool calls for JSON/YAML files and adds context
suggesting jq/yq exploration before full file reads.

Architecture: Functional core, imperative shell
- Data: Configuration, domain types
- Pure functions: All decision logic
- Effects: Only at edges (stdin/stdout, filesystem)
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# =============================================================================
# CONFIGURATION (Data)
# =============================================================================

STRUCTURED_EXTENSIONS = frozenset({".json", ".yaml", ".yml"})
SMALL_FILE_THRESHOLD = 100      # lines: no nudge
MEDIUM_FILE_THRESHOLD = 250     # lines: gentle nudge
# above MEDIUM: strong nudge


# =============================================================================
# DOMAIN TYPES (Data)
# =============================================================================

class NudgeLevel(Enum):
    NONE = "none"
    GENTLE = "gentle"
    STRONG = "strong"


@dataclass(frozen=True)
class FileInfo:
    path: str
    extension: str
    line_count: Optional[int]


@dataclass(frozen=True)
class HookInput:
    tool_name: str
    file_path: str


@dataclass(frozen=True)
class HookOutput:
    should_add_context: bool
    context_message: Optional[str]
    permission_decision: str  # "allow" | "ask"


# =============================================================================
# PURE FUNCTIONS (Logic)
# =============================================================================

def parse_hook_input(raw: dict) -> HookInput:
    """Extract relevant fields from hook stdin."""
    return HookInput(
        tool_name=raw.get("tool_name", ""),
        file_path=raw.get("tool_input", {}).get("file_path", ""),
    )


def extract_extension(path: str) -> str:
    """Get lowercase file extension."""
    import os
    return os.path.splitext(path)[1].lower()


def is_structured_file(extension: str) -> bool:
    """Check if extension indicates a queryable structured file."""
    return extension in STRUCTURED_EXTENSIONS


def determine_nudge_level(line_count: Optional[int]) -> NudgeLevel:
    """Decide nudge intensity based on file size."""
    if line_count is None:
        return NudgeLevel.NONE
    if line_count < SMALL_FILE_THRESHOLD:
        return NudgeLevel.NONE
    if line_count < MEDIUM_FILE_THRESHOLD:
        return NudgeLevel.GENTLE
    return NudgeLevel.STRONG


def query_tool_for_extension(extension: str) -> str:
    """Return appropriate query tool name for file type."""
    if extension == ".json":
        return "jq"
    return "yq"


def format_nudge_message(file_info: FileInfo, nudge_level: NudgeLevel) -> Optional[str]:
    """Generate context message based on nudge level. Pure string formatting."""
    if nudge_level == NudgeLevel.NONE:
        return None

    tool = query_tool_for_extension(file_info.extension)
    line_count = file_info.line_count or "unknown"

    preamble = {
        NudgeLevel.GENTLE: f"Note: {file_info.path} is {line_count} lines (structured file).",
        NudgeLevel.STRONG: f"Heads up: {file_info.path} is {line_count} lines (structured file).",
    }[nudge_level]

    return f"""{preamble}
Probe first?  {tool} 'keys' "{file_info.path}"  |  {tool} '.specific.path' "{file_info.path}"
Or proceed with Read if you really need the whole thing."""


def decide_hook_output(file_info: FileInfo) -> HookOutput:
    """Main decision function: given file info, produce hook output."""
    if not is_structured_file(file_info.extension):
        return HookOutput(
            should_add_context=False,
            context_message=None,
            permission_decision="allow",
        )

    nudge_level = determine_nudge_level(file_info.line_count)
    message = format_nudge_message(file_info, nudge_level)

    return HookOutput(
        should_add_context=message is not None,
        context_message=message,
        permission_decision="ask" if nudge_level == NudgeLevel.STRONG else "allow",
    )


def render_output(hook_output: HookOutput) -> Optional[str]:
    """Serialize hook output to JSON for Claude Code. Pure transformation."""
    if not hook_output.should_add_context:
        return None

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": hook_output.permission_decision,
            "additionalContext": hook_output.context_message,
        }
    }
    return json.dumps(output)


# =============================================================================
# EFFECTFUL FUNCTIONS (I/O at the edges)
# =============================================================================

def read_stdin() -> dict:
    """Effect: Read and parse JSON from stdin."""
    return json.load(sys.stdin)


def get_line_count(path: str) -> Optional[int]:
    """Effect: Count lines in file via subprocess."""
    try:
        result = subprocess.run(
            ["wc", "-l", path],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return int(result.stdout.split()[0])
    except (subprocess.TimeoutExpired, ValueError, IndexError, FileNotFoundError):
        pass
    return None


def write_stdout(content: str) -> None:
    """Effect: Write to stdout."""
    print(content)


# =============================================================================
# MAIN (Imperative shell)
# =============================================================================

def main() -> int:
    """
    Orchestration: wire effects to pure logic.

    Flow:
    1. Read input (effect)
    2. Parse input (pure)
    3. Get file info (effect: line count)
    4. Decide output (pure)
    5. Render output (pure)
    6. Write output (effect)
    """
    # Effect: read
    raw_input = read_stdin()

    # Pure: parse
    hook_input = parse_hook_input(raw_input)
    extension = extract_extension(hook_input.file_path)

    # Short-circuit: not a structured file
    if not is_structured_file(extension):
        return 0

    # Effect: get file metadata
    line_count = get_line_count(hook_input.file_path)

    # Pure: build domain object
    file_info = FileInfo(
        path=hook_input.file_path,
        extension=extension,
        line_count=line_count,
    )

    # Pure: decide
    hook_output = decide_hook_output(file_info)

    # Pure: render
    rendered = render_output(hook_output)

    # Effect: write
    if rendered:
        write_stdout(rendered)

    return 0


if __name__ == "__main__":
    sys.exit(main())
