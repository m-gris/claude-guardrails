"""
Install command - copies hooks to ~/.claude/ and optionally enables all.
"""

import importlib.resources
import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from claude_guardrails.paths import (
    GUARDRAILS_DIR,
    HOOKS_DIR,
    REMINDERS_CONFIG,
    REMINDERS_STATE_DIR,
    ensure_dirs,
)
from claude_guardrails.settings import HookSpec, is_hook_registered, register_hook

console = Console()

# Hook definitions
PERIODIC_REMINDERS_HOOK = HookSpec(
    event="UserPromptSubmit",
    matcher=None,
    command="~/.claude/hooks/periodic-reminders.sh",
)

PROGRESSIVE_DISCLOSURE_HOOK = HookSpec(
    event="PreToolUse",
    matcher="Read",
    command="~/.claude/hooks/structured-file-nudge.py",
)

URL_DISCIPLINE_HOOK = HookSpec(
    event="PreToolUse",
    matcher="WebFetch",
    command="~/.claude/hooks/webfetch-url-discipline.py",
)


def get_bundled_hooks_dir() -> Path:
    """Get path to bundled hooks in the package."""
    # Use importlib.resources for Python 3.9+
    import claude_guardrails.hooks as hooks_module

    return Path(hooks_module.__file__).parent


def copy_hooks() -> list[str]:
    """Copy bundled hooks to ~/.claude/hooks/. Returns list of copied files."""
    ensure_dirs()
    hooks_source = get_bundled_hooks_dir()
    copied = []

    for hook_file in hooks_source.iterdir():
        if hook_file.name.startswith("_"):
            continue
        if hook_file.suffix in (".py", ".sh"):
            dest = HOOKS_DIR / hook_file.name
            shutil.copy2(hook_file, dest)
            # Make executable
            dest.chmod(dest.stat().st_mode | 0o111)
            copied.append(hook_file.name)

    return copied


def copy_templates() -> list[str]:
    """Copy example config templates. Returns list of copied files."""
    ensure_dirs()
    import claude_guardrails.templates as templates_module

    templates_source = Path(templates_module.__file__).parent
    copied = []

    for template_file in templates_source.iterdir():
        if template_file.name.startswith("_"):
            continue
        if template_file.suffix in (".json", ".md", ".yaml", ".example"):
            # For .example files, copy without the .example suffix if target doesn't exist
            if template_file.name.endswith(".example"):
                dest_name = template_file.name.removesuffix(".example")
                dest = GUARDRAILS_DIR / dest_name
                if not dest.exists():
                    shutil.copy2(template_file, dest)
                    copied.append(dest_name)
            else:
                dest = GUARDRAILS_DIR / template_file.name
                if not dest.exists():
                    shutil.copy2(template_file, dest)
                    copied.append(template_file.name)

    return copied


def enable_all_guardrails() -> dict[str, bool]:
    """Enable all guardrails. Returns dict of guardrail -> was_newly_enabled."""
    results = {}
    results["reminders"] = register_hook(PERIODIC_REMINDERS_HOOK)
    results["progressive-disclosure"] = register_hook(PROGRESSIVE_DISCLOSURE_HOOK)
    results["url-discipline"] = register_hook(URL_DISCIPLINE_HOOK)
    return results


def run_install(enable_all: bool = False) -> None:
    """Main install routine."""
    console.print("\n[bold]Installing claude-guardrails...[/bold]\n")

    # Copy hooks
    copied_hooks = copy_hooks()
    if copied_hooks:
        console.print(f"[green]✓[/green] Copied hooks: {', '.join(copied_hooks)}")
    else:
        console.print("[yellow]![/yellow] No hooks found to copy")

    # Copy templates
    copied_templates = copy_templates()
    if copied_templates:
        console.print(
            f"[green]✓[/green] Copied templates: {', '.join(copied_templates)}"
        )

    # Create state directory
    REMINDERS_STATE_DIR.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] Created state directory: {REMINDERS_STATE_DIR}")

    if enable_all:
        console.print("\n[bold]Enabling all guardrails...[/bold]")
        results = enable_all_guardrails()
        for name, was_new in results.items():
            if was_new:
                console.print(f"[green]✓[/green] Enabled: {name}")
            else:
                console.print(f"[dim]○[/dim] Already enabled: {name}")
    else:
        console.print(
            "\n[dim]Hooks copied but not enabled. Use individual enable commands:[/dim]"
        )
        console.print("  claude-guardrails reminders enable")
        console.print("  claude-guardrails progressive-disclosure enable")
        console.print("  claude-guardrails url-discipline enable")

    console.print("\n[green]Installation complete![/green]\n")


def show_status() -> None:
    """Show status of all guardrails."""
    table = Table(title="Claude Guardrails Status")
    table.add_column("Guardrail", style="cyan")
    table.add_column("Hook Installed", style="dim")
    table.add_column("Hook Enabled", style="bold")

    # Check each guardrail
    guardrails = [
        ("Periodic Reminders", "periodic-reminders.sh", PERIODIC_REMINDERS_HOOK),
        (
            "Progressive Disclosure",
            "structured-file-nudge.py",
            PROGRESSIVE_DISCLOSURE_HOOK,
        ),
        ("URL Discipline", "webfetch-url-discipline.py", URL_DISCIPLINE_HOOK),
    ]

    for name, hook_file, hook_spec in guardrails:
        installed = (HOOKS_DIR / hook_file).exists()
        enabled = is_hook_registered(hook_spec)

        installed_str = "[green]Yes[/green]" if installed else "[red]No[/red]"
        enabled_str = "[green]Yes[/green]" if enabled else "[dim]No[/dim]"

        table.add_row(name, installed_str, enabled_str)

    console.print()
    console.print(table)
    console.print()
