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


def _tool_errors(tool: Callable) -> Callable:
    """Report storage errors to the agent instead of as server crashes."""

    @wraps(tool)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return tool(*args, **kwargs)
        except (ValueError, RuntimeError) as error:
            raise ToolError(str(error)) from error

    return wrapper


class MCPServer:
    """Bridge between an MCP client and a Storage implementation."""

    def __init__(self, storage: Storage):
        self.storage = storage
        self.server = SDKServer(
            "evolva",
            instructions=(
                "Evolva is a shared skills and memory layer for agents. Read skills "
                "to reuse what other agents have learned, and save your own reusable "
                "experience back as a skill so the shared memory keeps evolving."
            ),
        )

        @self.server.tool(
            description="List every skill shared in the repository (name, description).",
            annotations=ToolAnnotations(read_only_hint=True),
        )
        @_tool_errors
        def list_skills() -> list[dict[str, Any]]:
            return self.storage.list_skills()

        @self.server.tool(
            description="Find shared skills by keyword before reading or updating one.",
            annotations=ToolAnnotations(read_only_hint=True),
        )
        @_tool_errors
        def search_skills(
            keywords: Annotated[
                list[str],
                Field(
                    description=(
                        'Separate words or short phrases to look for, e.g. ["pdf", '
                        '"forms"]. Matching is case-insensitive substring matching '
                        "against skill names and descriptions, and a skill is returned "
                        "if any keyword occurs in it."
                    )
                ),
            ],
        ) -> list[dict[str, Any]]:
            return self.storage.search_skills(keywords)

        @self.server.tool(
            description=(
                "Copy a shared skill into a temporary directory for the current task "
                "and return the written path."
            ),
            annotations=ToolAnnotations(read_only_hint=True),
        )
        @_tool_errors
        def read_skill(
            skill_name: Annotated[
                str,
                Field(
                    description=(
                        "Skill name, as returned by list_skills or search_skills."
                    )
                ),
            ],
            save_dir: Annotated[
                str,
                Field(
                    description=(
                        "Temporary directory for this task's copy of the skill; pass "
                        "the parent directory, the skill is written to "
                        "<save_dir>/<skill_name>. Do not point this at the agent's own "
                        "skills folder: the copy is only meant for the current task."
                    )
                ),
            ],
        ) -> str:
            self.storage.read_skill(skill_name, save_dir)
            return str(Path(save_dir).expanduser() / skill_name)

        @self.server.tool(
            description=(
                "Publish a local skill directory, replacing the shared copy. Fails if "
                "the shared copy changed first; the local change is rolled back, so "
                "read the latest version, re-apply it and retry."
            ),
            annotations=ToolAnnotations(destructive_hint=True, idempotent_hint=True),
        )
        @_tool_errors
        def upsert_skill(
            skill_name: Annotated[
                str,
                Field(
                    description=(
                        "Skill name, as returned by list_skills or search_skills."
                    )
                ),
            ],
            upload_dir: Annotated[
                str,
                Field(
                    description=(
                        "Local skill directory to publish; it must contain a SKILL.md "
                        "with a description."
                    )
                ),
            ],
            message: Annotated[
                str, Field(description="Commit message describing the change.")
            ] = "",
        ) -> str:
            self.storage.upsert_skill(skill_name, upload_dir, message)
            return f"upserted {skill_name}"

        @self.server.tool(
            description=(
                "Delete a skill from the shared repository. Fails if the shared copy "
                "changed first; the local change is rolled back."
            ),
            annotations=ToolAnnotations(destructive_hint=True, idempotent_hint=True),
        )
        @_tool_errors
        def delete_skill(
            skill_name: Annotated[
                str,
                Field(
                    description=(
                        "Skill name, as returned by list_skills or search_skills."
                    )
                ),
            ],
            message: Annotated[
                str, Field(description="Commit message describing the change.")
            ] = "",
        ) -> str:
            self.storage.delete_skill(skill_name, message)
            return f"deleted {skill_name}"

    def run(self) -> None:
        self.server.run()
