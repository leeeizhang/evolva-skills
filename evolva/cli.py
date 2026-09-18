from __future__ import annotations

import argparse

from rich.console import Console

from evolva.config import CONFIG_PATH, load_config, save_config
from evolva.mcp.server import MCPServer
from evolva.storage.interface import create_storage

console = Console()
error_console = Console(stderr=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evolva",
        description="Shared skills and memory for agents.",
    )
    commands = parser.add_subparsers(required=True, dest="command")
    add_mcp_command(commands)
    add_set_command(commands)

    args = parser.parse_args(argv)
    args.handler(args)
    return 0


def add_mcp_command(commands: argparse._SubParsersAction) -> None:
    """evolva mcp"""
    parser = commands.add_parser("mcp", help="Run the Evolva MCP server on stdio.")
    parser.set_defaults(handler=run_mcp)


def add_set_command(commands: argparse._SubParsersAction) -> None:
    """evolva set storage|agent"""
    parser = commands.add_parser("set", help="Update the Evolva configuration.")
    settings = parser.add_subparsers(required=True, dest="setting")
    add_set_storage_command(settings)
    add_set_agent_command(settings)


def add_set_storage_command(settings: argparse._SubParsersAction) -> None:
    """evolva set storage <type> [key=value ...]"""
    parser = settings.add_parser("storage", help="Configure where skills are stored.")
    parser.add_argument("type", help="Storage type, e.g. git.")
    parser.add_argument(
        "options",
        nargs="*",
        metavar="key=value",
        help="Storage options, e.g. url=<repo> branch=<branch>.",
    )
    parser.set_defaults(handler=set_storage)


def add_set_agent_command(settings: argparse._SubParsersAction) -> None:
    """evolva set agent <target> --enable|--disable"""
    parser = settings.add_parser(
        "agent", help="Enable or disable an agent integration."
    )
    parser.add_argument("target", help="Agent integration, e.g. codex or claude.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--enable", action="store_true", help="Enable the agent.")
    action.add_argument("--disable", action="store_true", help="Disable the agent.")
    parser.set_defaults(handler=set_agent)


def run_mcp(args: argparse.Namespace) -> None:
    """Serve the Evolva tools on stdio, using the configured storage."""
    storage = load_config().get("storage")
    if not storage:
        error_console.print(
            "[red]No storage configured.[/red] Run [bold]evolva set storage "
            "git url=<repo> branch=<branch>[/bold] first."
        )
        raise SystemExit(1)

    MCPServer(create_storage(storage)).run()


def set_storage(args: argparse.Namespace) -> None:
    """Build the storage once to validate it, then write the config."""
    storage = {"type": args.type, **parse_options(args.options)}
    try:
        create_storage(storage)
    except (ValueError, RuntimeError) as error:
        error_console.print("[red]Storage setup failed.[/red]")
        error_console.print(str(error))
        raise SystemExit(1) from error

    config = load_config()
    config["storage"] = storage
    save_config(config)

    console.print(f"[green]Storage saved[/green] to {CONFIG_PATH.expanduser()}")
    for key, value in storage.items():
        console.print(f"  {key}: {value}")


def set_agent(args: argparse.Namespace) -> None:
    """Enable or disable an agent integration."""
    raise NotImplementedError("`evolva set agent` is not implemented yet.")


def parse_options(options: list[str]) -> dict[str, str]:
    """Turn ['url=<repo>', 'branch=main'] into {'url': '<repo>', 'branch': 'main'}."""
    parsed = {}
    for option in options:
        key, separator, value = option.partition("=")
        if not separator or not key:
            raise SystemExit(f"Invalid option {option!r}, expected key=value")
        parsed[key] = value

    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
