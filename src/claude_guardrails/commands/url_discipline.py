"""
URL Discipline CLI commands - manage WebFetch URL validation.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_guardrails.paths import HOOKS_DIR, URL_ALLOWLIST, ensure_dirs
from claude_guardrails.settings import HookSpec, is_hook_registered, register_hook, unregister_hook
from claude_guardrails.types import HookEvent

app = typer.Typer(no_args_is_help=True)
console = Console()

HOOK_SPEC = HookSpec(
    event=HookEvent.PRE_TOOL_USE,
    matcher="WebFetch",
    command="~/.claude/hooks/webfetch-url-discipline.py",
)


def load_allowlist() -> list[str]:
    """Load URL allowlist patterns."""
    if not URL_ALLOWLIST.exists():
        return []
    return [line.strip() for line in URL_ALLOWLIST.read_text().splitlines() if line.strip() and not line.startswith("#")]


def save_allowlist(patterns: list[str]) -> None:
    """Save URL allowlist patterns."""
    ensure_dirs()
    content = "# URL Allowlist Patterns\n"
    content += "# One pattern per line. Supports wildcards: *.example.com\n"
    content += "# Lines starting with # are comments\n\n"
    content += "\n".join(patterns) + "\n"
    URL_ALLOWLIST.write_text(content)


@app.command()
def enable() -> None:
    """Enable the URL discipline hook."""
    hook_file = HOOKS_DIR / "webfetch-url-discipline.py"
    if not hook_file.exists():
        console.print("[red]Error:[/red] Hook not installed. Run 'claude-guardrails install' first.")
        raise typer.Exit(1)

    if register_hook(HOOK_SPEC):
        console.print("[green]✓[/green] URL discipline hook enabled")
        console.print("  WebFetch calls to deep paths will now prompt for confirmation")
    else:
        console.print("[dim]○[/dim] URL discipline hook already enabled")


@app.command()
def disable() -> None:
    """Disable the URL discipline hook."""
    if unregister_hook(HOOK_SPEC):
        console.print("[green]✓[/green] URL discipline hook disabled")
    else:
        console.print("[dim]○[/dim] URL discipline hook was not enabled")


@app.command()
def status() -> None:
    """Show URL discipline status."""
    hook_file = HOOKS_DIR / "webfetch-url-discipline.py"
    installed = hook_file.exists()
    enabled = is_hook_registered(HOOK_SPEC)

    console.print("\n[bold]URL Discipline Status[/bold]")
    console.print(f"  Hook installed: {'[green]Yes[/green]' if installed else '[red]No[/red]'}")
    console.print(f"  Hook enabled: {'[green]Yes[/green]' if enabled else '[dim]No[/dim]'}")

    allowlist = load_allowlist()
    console.print(f"  Allowlist patterns: {len(allowlist)}")

    console.print("\n[dim]Safe entry points (always allowed):[/dim]")
    console.print("  /, /en/stable/, /en/latest/, /docs/, /sitemap.xml, /robots.txt")
    console.print("\n[dim]Deep paths trigger confirmation dialog[/dim]")
    console.print()


@app.command()
def allow(
    pattern: str = typer.Argument(..., help="URL pattern to allow (e.g., '*.github.com', 'docs.example.com/*')"),
) -> None:
    """Add a URL pattern to the allowlist."""
    patterns = load_allowlist()

    if pattern in patterns:
        console.print(f"[dim]○[/dim] Pattern already in allowlist: {pattern}")
        return

    patterns.append(pattern)
    save_allowlist(patterns)
    console.print(f"[green]✓[/green] Added to allowlist: {pattern}")


@app.command()
def deny(
    pattern: str = typer.Argument(..., help="URL pattern to remove from allowlist"),
) -> None:
    """Remove a URL pattern from the allowlist."""
    patterns = load_allowlist()

    if pattern not in patterns:
        console.print(f"[red]Error:[/red] Pattern not in allowlist: {pattern}")
        raise typer.Exit(1)

    patterns.remove(pattern)
    save_allowlist(patterns)
    console.print(f"[green]✓[/green] Removed from allowlist: {pattern}")


@app.command("list")
def list_patterns() -> None:
    """List all allowlist patterns."""
    patterns = load_allowlist()

    if not patterns:
        console.print("[dim]No allowlist patterns configured.[/dim]")
        console.print("Use [bold]url-discipline allow <pattern>[/bold] to add patterns.")
        return

    table = Table(title="URL Allowlist Patterns")
    table.add_column("#", style="dim", width=4)
    table.add_column("Pattern", style="cyan")

    for i, pattern in enumerate(patterns, 1):
        table.add_row(str(i), pattern)

    console.print()
    console.print(table)
    console.print()
