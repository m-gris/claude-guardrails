"""
URL Discipline CLI commands - manage WebFetch URL validation.
"""

import typer
from rich.console import Console

from claude_guardrails.paths import HOOKS_DIR
from claude_guardrails.settings import HookSpec, is_hook_registered, register_hook, unregister_hook
from claude_guardrails.types import HookEvent

app = typer.Typer(no_args_is_help=True)
console = Console()

HOOK_SPEC = HookSpec(
    event=HookEvent.PRE_TOOL_USE,
    matcher="WebFetch",
    command="~/.claude/hooks/webfetch-url-discipline.py",
)


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

    console.print("\n[dim]Safe entry points (always allowed):[/dim]")
    console.print("  /, /en/stable/, /en/latest/, /docs/, /sitemap.xml, /robots.txt")
    console.print("\n[dim]Deep paths trigger confirmation dialog[/dim]")
    console.print()
