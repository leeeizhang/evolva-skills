from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer as SDKServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from evolva.storage.interface import Storage

MAX_NAMES = 20


def build_instructions(storage: Storage) -> str:
    return "\n".join(
        [
            "Evolva is shared memory for agents: the entry point to dynamic "
            "Skills that are not loaded into agent-installed skill hubs.",
            "Start every task by listing what Evolva Skills exist and may help; "
            "search it when you lack knowledge or experience, when something "
            "fails, or before solving from scratch.",
            f"Skills: {_names(storage)}",
            "Tools: list_skills (start here), search_skills, read_skill, "
            "upsert_skill, delete_skill.",
            "If you learn something reusable — a hard-won fix, an unexpected "
            "constraint, a workflow that worked — publish it with upsert_skill "
            "so the next agent does not rediscover it.",
        ]
    )


def _names(storage: Storage) -> str:
    """List Skill names, never failing the handshake over them.

    `list_skills` is named even when every Skill fits: it keeps the full catalog
    one call away, which is what makes the shipped names a starting point rather
    than the whole picture.
    """
    try:
        names = [str(skill.get("name", "?")) for skill in storage.list_skills()]
    except (OSError, RuntimeError, ValueError) as error:
        return f"unavailable ({error}); call list_skills to retry"

    if not names:
        return "none published yet, use upsert_skill to add the first one"

    shown = ", ".join(names[:MAX_NAMES])
    return f"{shown}, and more: list_skills has the full catalog"


def _handle_errors(tool: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(tool)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return tool(*args, **kwargs)
        except (ValueError, RuntimeError) as error:
            raise ToolError(str(error)) from error

    return wrapper


class MCPServer:
    """Expose Evolva shared Skills through MCP."""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage
        self.server = SDKServer(
            "evolva",
            instructions=build_instructions(storage),
        )

        self._register_tools()

    def _register_tools(self) -> None:
        self._register_list_skills()
        self._register_search_skills()
        self._register_read_skill()
        self._register_upsert_skill()
        self._register_delete_skill()

    def _register_list_skills(self) -> None:
        @self.server.tool(
            description=(
                "List all shared Skills. "
                "Use for broad discovery when you do not know what to search for."
            ),
            annotations=ToolAnnotations(read_only_hint=True),
        )
        @_handle_errors
        def list_skills() -> list[dict[str, Any]]:
            return self.storage.list_skills()

    def _register_search_skills(self) -> None:
        @self.server.tool(
            description=(
                "Search shared Skills by name or description. "
                "Use before reading or creating a Skill when the topic is known."
            ),
            annotations=ToolAnnotations(read_only_hint=True),
        )
        @_handle_errors
        def search_skills(
            keywords: Annotated[
                list[str],
                Field(
                    description="Keywords or short phrases describing the knowledge needed."
                ),
            ],
        ) -> list[dict[str, Any]]:
            return self.storage.search_skills(keywords)

    def _register_read_skill(self) -> None:
        @self.server.tool(
            description=(
                "Copy a shared Skill into the current task's local workspace for reuse. "
                "This only creates a local copy; the shared Skill is not modified."
            ),
            annotations=ToolAnnotations(read_only_hint=True),
        )
        @_handle_errors
        def read_skill(
            skill_name: Annotated[
                str,
                Field(
                    description="Exact Skill name from list_skills or search_skills."
                ),
            ],
            save_dir: Annotated[
                str,
                Field(
                    description=(
                        "Parent directory for the temporary copy. "
                        "The Skill is written to <save_dir>/<skill_name>."
                    )
                ),
            ],
        ) -> str:
            self.storage.read_skill(skill_name, save_dir)
            return str(Path(save_dir).expanduser() / skill_name)

    def _register_upsert_skill(self) -> None:
        @self.server.tool(
            description=(
                "Publish a complete Skill to shared memory. "
                "Use when creating reusable knowledge or improving an existing Skill. "
                "Read the latest shared copy before updating one."
            ),
            annotations=ToolAnnotations(
                destructive_hint=True,
                idempotent_hint=True,
            ),
        )
        @_handle_errors
        def upsert_skill(
            skill_name: Annotated[
                str,
                Field(description="Skill name to create or update."),
            ],
            upload_dir: Annotated[
                str,
                Field(
                    description=(
                        "Complete Skill directory to publish. Must contain SKILL.md."
                    )
                ),
            ],
            message: Annotated[
                str,
                Field(description="Short description of the change."),
            ] = "",
        ) -> str:
            self.storage.upsert_skill(skill_name, upload_dir, message)
            return f"upserted {skill_name}"

    def _register_delete_skill(self) -> None:
        @self.server.tool(
            description=(
                "Remove a shared Skill. "
                "Use only for obsolete, invalid, or duplicate knowledge."
            ),
            annotations=ToolAnnotations(
                destructive_hint=True,
                idempotent_hint=True,
            ),
        )
        @_handle_errors
        def delete_skill(
            skill_name: Annotated[
                str,
                Field(description="Exact Skill name to remove."),
            ],
            message: Annotated[
                str,
                Field(description="Short description of why it is being removed."),
            ] = "",
        ) -> str:
            self.storage.delete_skill(skill_name, message)
            return f"deleted {skill_name}"

    def run(self) -> None:
        self.server.run()
