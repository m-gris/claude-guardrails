"""
Reminders CLI commands - manage periodic reminders for Claude Code.
"""

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from claude_guardrails.paths import REMINDERS_CONFIG, REMINDERS_STATE_DIR, ensure_dirs
from claude_guardrails.settings import HookSpec, is_hook_registered, register_hook, unregister_hook
from claude_guardrails.types import HookEvent

app = typer.Typer(no_args_is_help=True)
console = Console()

HOOK_SPEC = HookSpec(
    event=HookEvent.USER_PROMPT_SUBMIT,
    matcher=None,
    command="~/.claude/hooks/periodic-reminders.sh",
)


@dataclass(frozen=True)
class Reminder:
    """A periodic reminder configuration."""

    id: str
    interval_turns: int
    interval_seconds: int
    message: str


def load_reminders() -> list[Reminder]:
    """Load reminders from config file."""
    if not REMINDERS_CONFIG.exists():
        return []
    data = json.loads(REMINDERS_CONFIG.read_text())
    return [Reminder(**r) for r in data.get("reminders", [])]


def save_reminders(reminders: list[Reminder]) -> None:
    """Save reminders to config file."""
    ensure_dirs()
    data = {"reminders": [asdict(r) for r in reminders]}
    REMINDERS_CONFIG.write_text(json.dumps(data, indent=2) + "\n")


@app.command()
def enable() -> None:
    """Enable the periodic reminders hook."""
    if register_hook(HOOK_SPEC):
        console.print("[green]✓[/green] Periodic reminders hook enabled")
    else:
        console.print("[dim]○[/dim] Periodic reminders hook already enabled")


@app.command()
def disable() -> None:
    """Disable the periodic reminders hook."""
    if unregister_hook(HOOK_SPEC):
        console.print("[green]✓[/green] Periodic reminders hook disabled")
    else:
        console.print("[dim]○[/dim] Periodic reminders hook was not enabled")


@app.command("list")
def list_reminders() -> None:
    """List all configured reminders."""
    reminders = load_reminders()

    if not reminders:
        console.print("[dim]No reminders configured.[/dim]")
        console.print("Use [bold]reminders add[/bold] to create one.")
        return

    table = Table(title="Configured Reminders")
    table.add_column("ID", style="cyan")
    table.add_column("Interval (turns)", justify="right")
    table.add_column("Interval (seconds)", justify="right")
    table.add_column("Message", max_width=50)

    for r in reminders:
        msg_preview = r.message[:47] + "..." if len(r.message) > 50 else r.message
        msg_preview = msg_preview.replace("\n", "\\n")
        table.add_row(
            r.id, str(r.interval_turns), str(r.interval_seconds), msg_preview
        )

    console.print()
    console.print(table)

    # Show hook status
    enabled = is_hook_registered(HOOK_SPEC)
    status = "[green]enabled[/green]" if enabled else "[red]disabled[/red]"
    console.print(f"\nHook status: {status}")
    console.print()


@app.command()
def add(
    id: str | None = typer.Option(None, "--id", "-i", help="Reminder ID (auto-generated if not provided)"),
    turns: int | None = typer.Option(None, "--turns", "-t", help="Trigger every N turns"),
    seconds: int | None = typer.Option(None, "--seconds", "-s", help="Trigger every N seconds"),
    message: str | None = typer.Option(None, "--message", "-m", help="Reminder message"),
) -> None:
    """Add a new reminder (interactive if options not provided)."""
    reminders = load_reminders()

    # Interactive prompts if not provided
    if id is None:
        default_id = f"reminder-{uuid.uuid4().hex[:6]}"
        id = Prompt.ask("Reminder ID", default=default_id)

    # Check for duplicate
    if any(r.id == id for r in reminders):
        console.print(f"[red]Error:[/red] Reminder with ID '{id}' already exists")
        raise typer.Exit(1)

    if turns is None:
        turns = IntPrompt.ask("Trigger every N turns", default=5)

    if seconds is None:
        seconds = IntPrompt.ask("Trigger every N seconds", default=600)

    if message is None:
        console.print("\nEnter reminder message (variables: $CUMULATIVE_TURNS, $PID, $NOW_ISO)")
        console.print("End with an empty line:")
        lines = []
        while True:
            line = Prompt.ask("", default="")
            if line == "":
                break
            lines.append(line)
        message = "\n".join(lines) if lines else f"<reminder id=\"{id}\"/>"

    reminder = Reminder(id=id, interval_turns=turns, interval_seconds=seconds, message=message)
    reminders.append(reminder)
    save_reminders(reminders)

    console.print(f"\n[green]✓[/green] Added reminder: {id}")
    console.print(f"  Triggers every {turns} turns OR {seconds} seconds")


@app.command()
def remove(reminder_id: str = typer.Argument(..., help="ID of reminder to remove")) -> None:
    """Remove a reminder by ID."""
    reminders = load_reminders()
    original_count = len(reminders)
    reminders = [r for r in reminders if r.id != reminder_id]

    if len(reminders) == original_count:
        console.print(f"[red]Error:[/red] No reminder found with ID '{reminder_id}'")
        raise typer.Exit(1)

    save_reminders(reminders)

    # Also clean up state file
    state_file = REMINDERS_STATE_DIR / f"{reminder_id}.state"
    if state_file.exists():
        state_file.unlink()

    console.print(f"[green]✓[/green] Removed reminder: {reminder_id}")


@app.command()
def show(reminder_id: str = typer.Argument(..., help="ID of reminder to show")) -> None:
    """Show details of a specific reminder."""
    reminders = load_reminders()
    reminder = next((r for r in reminders if r.id == reminder_id), None)

    if reminder is None:
        console.print(f"[red]Error:[/red] No reminder found with ID '{reminder_id}'")
        raise typer.Exit(1)

    console.print(f"\n[bold]Reminder: {reminder.id}[/bold]")
    console.print(f"  Interval (turns): {reminder.interval_turns}")
    console.print(f"  Interval (seconds): {reminder.interval_seconds}")
    console.print(f"  Message:")
    for line in reminder.message.split("\n"):
        console.print(f"    {line}")

    # Show state if exists
    state_file = REMINDERS_STATE_DIR / f"{reminder_id}.state"
    if state_file.exists():
        console.print(f"\n  [dim]State ({state_file}):[/dim]")
        for line in state_file.read_text().strip().split("\n"):
            console.print(f"    {line}")
    console.print()


@app.command()
def reset(
    reminder_id: str = typer.Argument(..., help="ID of reminder to reset, or 'all'"),
) -> None:
    """Reset state for a reminder (or all reminders)."""
    if reminder_id == "all":
        count = 0
        for state_file in REMINDERS_STATE_DIR.glob("*.state"):
            state_file.unlink()
            count += 1
        console.print(f"[green]✓[/green] Reset {count} reminder state files")
    else:
        state_file = REMINDERS_STATE_DIR / f"{reminder_id}.state"
        if state_file.exists():
            state_file.unlink()
            console.print(f"[green]✓[/green] Reset state for reminder: {reminder_id}")
        else:
            console.print(f"[dim]○[/dim] No state file found for: {reminder_id}")
