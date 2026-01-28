"""
Progressive Disclosure CLI commands - manage structured file nudges.
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
    matcher="Read",
    command="~/.claude/hooks/structured-file-nudge.py",
)


@app.command()
def enable() -> None:
    """Enable the progressive disclosure hook."""
    # Check hook file exists
    hook_file = HOOKS_DIR / "structured-file-nudge.py"
    if not hook_file.exists():
        console.print("[red]Error:[/red] Hook not installed. Run 'claude-guardrails install' first.")
        raise typer.Exit(1)

    if register_hook(HOOK_SPEC):
        console.print("[green]✓[/green] Progressive disclosure hook enabled")
        console.print("  Large JSON/YAML files will now trigger jq/yq suggestions")
    else:
        console.print("[dim]○[/dim] Progressive disclosure hook already enabled")


@app.command()
def disable() -> None:
    """Disable the progressive disclosure hook."""
    if unregister_hook(HOOK_SPEC):
        console.print("[green]✓[/green] Progressive disclosure hook disabled")
    else:
        console.print("[dim]○[/dim] Progressive disclosure hook was not enabled")


@app.command()
def status() -> None:
    """Show progressive disclosure status."""
    hook_file = HOOKS_DIR / "structured-file-nudge.py"
    installed = hook_file.exists()
    enabled = is_hook_registered(HOOK_SPEC)

    console.print("\n[bold]Progressive Disclosure Status[/bold]")
    console.print(f"  Hook installed: {'[green]Yes[/green]' if installed else '[red]No[/red]'}")
    console.print(f"  Hook enabled: {'[green]Yes[/green]' if enabled else '[dim]No[/dim]'}")

    console.print("\n[dim]Current thresholds (hardcoded in hook):[/dim]")
    console.print("  < 100 lines: No nudge")
    console.print("  100-250 lines: Gentle suggestion")
    console.print("  > 250 lines: Strong nudge (asks for confirmation)")
    console.print()
