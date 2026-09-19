from __future__ import annotations

import sys

import questionary
from rich.console import Console

from evolva.agents.interface import create_agent, list_agents
from evolva.config import CONFIG_PATH, load_config, save_config, set_agent_enabled
from evolva.storage.interface import create_storage, get_storage_class, list_storages

console = Console()
error_console = Console(stderr=True)


def run_tui() -> None:
    """Ask what to do and walk the user through it."""
    if not sys.stdin.isatty():
        error_console.print(
            "[red]The interactive UI needs a terminal.[/red] "
            "Use [bold]evolva set[/bold] for scripted use."
        )
        return

    console.rule("[bold]Evolva[/bold]")

    while True:
        action = questionary.select(
            "What would you like to do?",
            choices=["install", "configure", "uninstall", "exit"],
        ).ask()
        if action in (None, "exit"):
            return

        try:
            if action == "install":
                _manage_agents("install")
            elif action == "uninstall":
                _manage_agents("uninstall")
            else:
                _configure_storage()
        except (ValueError, RuntimeError, OSError) as error:
            error_console.print(f"[red]{error}[/red]")


def _manage_agents(action: str) -> None:
    """Install or uninstall the agent the user picks."""
    if action == "install" and not load_config().get("storage"):
        console.print(
            "[yellow]Storage is not configured yet.[/yellow] Let's set it up first."
        )
        _configure_storage()
        if not load_config().get("storage"):
            return

    installed = load_config().get("agents", [])
    verb = "Install into" if action == "install" else "Uninstall from"
    choices = [
        questionary.Choice(f"{'✓' if name in installed else ' '} {name}", value=name)
        for name in list_agents()
    ]
    target = questionary.select(f"{verb} which agent?", choices=choices).ask()
    if target is None:
        return

    if action == "uninstall" and target not in installed:
        console.print(f"[yellow]{target} is not installed.[/yellow]")
        return

    agent = create_agent({"type": target})
    if action == "install":
        agent.install()
        set_agent_enabled(target, True)
        console.print(f"[green]Installed[/green] into [bold]{target}[/bold]")
    else:
        agent.uninstall()
        set_agent_enabled(target, False)
        console.print(f"[green]Uninstalled[/green] from [bold]{target}[/bold]")


def _configure_storage() -> None:
    """Collect storage options, validate them, and save the config."""
    storage_type = questionary.select("Storage type", choices=list_storages()).ask()
    if storage_type is None:
        return

    values = _ask_storage_options(storage_type)
    if values is None:
        return

    storage = {"type": storage_type, **values}

    create_storage(storage)

    config = load_config()
    config["storage"] = storage
    save_config(config)

    console.print(f"[green]Storage saved[/green] to {CONFIG_PATH.expanduser()}")
    for key, value in storage.items():
        console.print(f"  {key}: {value}")


def _ask_storage_options(storage_type: str) -> dict[str, str] | None:
    """Ask for every config field the storage implementation declares."""
    values: dict[str, str] = {}
    for field in get_storage_class(storage_type).options:
        answer = questionary.text(
            field["prompt"],
            default=field.get("default", ""),
            validate=_not_empty,
        ).ask()
        if answer is None:
            return None
        values[field["name"]] = answer

    return values


def _not_empty(value: str) -> bool | str:
    """Require a non-empty answer."""
    return bool(value) or "Please enter a value."
