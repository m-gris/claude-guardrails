"""
Main CLI entry point for claude-guardrails.

Usage:
    uvx claude-guardrails install [--all]
    uvx claude-guardrails reminders {enable,disable,list,add,remove,show,reset}
    uvx claude-guardrails progressive-disclosure {enable,disable,config}
    uvx claude-guardrails url-discipline {enable,disable,allow,list}
"""

import typer
from rich.console import Console

from claude_guardrails.commands import install, progressive, reminders, url_discipline

app = typer.Typer(
    name="claude-guardrails",
    help="Guardrails and hooks for Claude Code",
    no_args_is_help=True,
)
console = Console()

# Register command groups
app.add_typer(reminders.app, name="reminders", help="Manage periodic reminders")
app.add_typer(
    progressive.app, name="progressive-disclosure", help="Manage structured file nudges"
)
app.add_typer(url_discipline.app, name="url-discipline", help="Manage URL validation")


@app.command()
def install(
    all_guardrails: bool = typer.Option(
        False, "--all", help="Enable all guardrails after installation"
    ),
) -> None:
    """Install guardrails to ~/.claude/ (copies hooks, does NOT enable by default)."""
    from claude_guardrails.commands.install import run_install

    run_install(enable_all=all_guardrails)


@app.command()
def status() -> None:
    """Show status of all guardrails."""
    from claude_guardrails.commands.install import show_status

    show_status()


if __name__ == "__main__":
    app()
