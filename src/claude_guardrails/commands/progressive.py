"""
Progressive Disclosure CLI commands - manage structured file nudges.
"""

import typer
from rich.console import Console

from claude_guardrails.paths import HOOKS_DIR, PROGRESSIVE_CONFIG, ensure_dirs
from claude_guardrails.settings import HookSpec, is_hook_registered, register_hook, unregister_hook
from claude_guardrails.types import HookEvent

app = typer.Typer(no_args_is_help=True)
console = Console()

HOOK_SPEC = HookSpec(
    event=HookEvent.PRE_TOOL_USE,
    matcher="Read",
    command="~/.claude/hooks/structured-file-nudge.py",
)

# Default configuration
DEFAULT_CONFIG = """\
# Progressive Disclosure Configuration
# Thresholds for nudging on structured file reads

extensions:
  - .json
  - .yaml
  - .yml

thresholds:
  # Lines below this: no nudge
  small: 100
  # Lines below this: gentle nudge
  medium: 250
  # Lines above medium: strong nudge (prompts for confirmation)
"""


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

    if PROGRESSIVE_CONFIG.exists():
        console.print(f"  Config file: {PROGRESSIVE_CONFIG}")
    else:
        console.print("  Config file: [dim]Using defaults[/dim]")

    console.print("\n[dim]Current thresholds (hardcoded in hook):[/dim]")
    console.print("  < 100 lines: No nudge")
    console.print("  100-250 lines: Gentle suggestion")
    console.print("  > 250 lines: Strong nudge (asks for confirmation)")
    console.print()


@app.command()
def config() -> None:
    """Show/create configuration file."""
    ensure_dirs()

    if PROGRESSIVE_CONFIG.exists():
        console.print(f"\n[bold]Current configuration ({PROGRESSIVE_CONFIG}):[/bold]\n")
        console.print(PROGRESSIVE_CONFIG.read_text())
    else:
        console.print("\n[dim]No configuration file. Creating default...[/dim]\n")
        PROGRESSIVE_CONFIG.write_text(DEFAULT_CONFIG)
        console.print(f"[green]✓[/green] Created: {PROGRESSIVE_CONFIG}")
        console.print("\n[yellow]Note:[/yellow] The hook currently uses hardcoded thresholds.")
        console.print("Edit the hook directly to customize, or wait for a future version")
        console.print("that reads from this config file.")
