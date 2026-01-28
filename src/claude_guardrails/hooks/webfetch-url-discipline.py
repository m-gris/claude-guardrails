#!/usr/bin/env python3
"""
WebFetch URL Discipline Hook

Intercepts WebFetch tool calls and prompts reflection on URL origin.
URLs should be discovered (from previous fetches, user input, or known roots),
not invented from assumptions about path structure.

Architecture: Functional core, imperative shell
"""

import json
import sys
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


# =============================================================================
# CONFIGURATION (Data)
# =============================================================================

# URL patterns that are safe "entry points" - no previous fetch needed
ROOT_PATH_PATTERNS = frozenset({
    "/",
    "",
    "/en/stable/",
    "/en/latest/",
    "/docs/",
    "/sitemap.xml",
    "/robots.txt",
})


# =============================================================================
# DOMAIN TYPES (Data)
# =============================================================================

class UrlOrigin(Enum):
    ROOT_ENTRY = "root_entry"        # Known safe entry point
    DEEP_PATH = "deep_path"          # Could be constructed/guessed


@dataclass(frozen=True)
class UrlInfo:
    full_url: str
    host: str
    path: str


@dataclass(frozen=True)
class HookInput:
    tool_name: str
    url: str
    prompt: str


@dataclass(frozen=True)
class HookOutput:
    should_add_context: bool
    context_message: str | None
    permission_decision: str  # "allow" | "ask"


# =============================================================================
# PURE FUNCTIONS (Logic)
# =============================================================================

def parse_hook_input(raw: dict) -> HookInput:
    """Extract relevant fields from hook stdin."""
    tool_input = raw.get("tool_input", {})
    return HookInput(
        tool_name=raw.get("tool_name", ""),
        url=tool_input.get("url", ""),
        prompt=tool_input.get("prompt", ""),
    )


def parse_url(url: str) -> UrlInfo:
    """Parse URL into components."""
    parsed = urlparse(url)
    return UrlInfo(
        full_url=url,
        host=parsed.netloc,
        path=parsed.path,
    )


def is_root_entry_point(url_info: UrlInfo) -> bool:
    """Check if URL is a known safe entry point (root, sitemap, etc.)."""
    # Normalize path for comparison
    path = url_info.path.rstrip("/") + "/" if url_info.path else "/"
    path_without_slash = url_info.path.rstrip("/")

    return (
        path in ROOT_PATH_PATTERNS
        or path_without_slash in ROOT_PATH_PATTERNS
        or url_info.path == ""
    )


def classify_url(url_info: UrlInfo) -> UrlOrigin:
    """Classify URL by likely origin."""
    if is_root_entry_point(url_info):
        return UrlOrigin.ROOT_ENTRY
    return UrlOrigin.DEEP_PATH


def format_discipline_message(url_info: UrlInfo) -> str:
    """Generate the reflection prompt for deep paths."""
    return f"""URL Discipline Check: {url_info.full_url}

This is a deep path, not a root entry point.

Before proceeding, confirm this URL was:
  (a) Extracted from a previous fetch (link in ToC, sitemap, nav)
  (b) Provided by the user
  (c) From search results

If you're constructing this path from assumptions about URL structure,
STOP and fetch the sitemap or index page first:
  - {url_info.host}/sitemap.xml
  - {url_info.host}/ (then extract nav links)

URLs are discovered, not invented."""


def decide_hook_output(url_info: UrlInfo) -> HookOutput:
    """Main decision function: given URL info, produce hook output."""
    origin = classify_url(url_info)

    if origin == UrlOrigin.ROOT_ENTRY:
        return HookOutput(
            should_add_context=False,
            context_message=None,
            permission_decision="allow",
        )

    # Deep path: prompt for reflection
    return HookOutput(
        should_add_context=True,
        context_message=format_discipline_message(url_info),
        permission_decision="ask",
    )


def render_output(hook_output: HookOutput) -> str | None:
    """Serialize hook output to JSON for Claude Code."""
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


def write_stdout(content: str) -> None:
    """Effect: Write to stdout."""
    print(content)


# =============================================================================
# MAIN (Imperative shell)
# =============================================================================

def main() -> int:
    """
    Orchestration: wire effects to pure logic.
    """
    # Effect: read
    raw_input = read_stdin()

    # Pure: parse
    hook_input = parse_hook_input(raw_input)

    # Short-circuit: not WebFetch
    if hook_input.tool_name != "WebFetch":
        return 0

    # Pure: parse URL
    url_info = parse_url(hook_input.url)

    # Pure: decide
    hook_output = decide_hook_output(url_info)

    # Pure: render
    rendered = render_output(hook_output)

    # Effect: write and block if deep path
    if rendered:
        write_stdout(rendered)
        return 2  # block tool call

    return 0


if __name__ == "__main__":
    sys.exit(main())
