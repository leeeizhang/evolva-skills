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

MAX_NAMES = 32


def build_instructions(storage: Storage) -> str:
    return "\n".join(
        [
            "Evolva is a shared skill library and reusable memory across agents "
            "and sessions. Its catalog includes skills absent from the agent's "
            "installed skill list.",
            "At task start, call list_skills to discover related capabilities, "
            "even for familiar work. When relevance is uncertain, read the "
            "strongest candidate. Search before unfamiliar work or failure recovery.",
            "read_skill returns a local directory path: open SKILL.md and needed "
            "supporting files. Verify instructions against current evidence.",
            "During work, act on verified skill defects, missing steps, user "
            "workflow corrections, and reusable new methods; review again before "
            "your final response even if no skill was used. Smooth successes count.",
            "Publish verified additions or corrections that improve future tasks "
            "with upsert_skill. Repository-specific knowledge qualifies; state "
            "its scope and prerequisites. Preserve the scope of user corrections. "
            "Search and read likely matches first; extend existing capabilities. "
            "No useful new knowledge means no write.",
            "Before updating, read the latest package into a fresh directory. "
            "upsert_skill replaces the entire package: preserve supporting files. "
            "Local edits alone are not published. Complete verified repairs and "
            "useful captures before finishing; report blocked verification or "
            "publication. Curate the full library only when requested.",
            f"Skills at connection: {_names(storage)}",
        ]
    )


def _names(storage: Storage) -> str:
    """List skill names without failing the handshake over storage errors."""
    try:
        names = [str(skill.get("name", "?")) for skill in storage.list_skills()]
    except Exception as error:
        return f"unavailable (error: {error}); call list_skills to retry"

    if not names:
        return "none; call list_skills to refresh"

    shown = ", ".join(names[:MAX_NAMES])
    if len(names) > MAX_NAMES:
        return f"{shown}, and more; call list_skills for the full catalog"
    return f"{shown}; call list_skills for descriptions"


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
                "List names and descriptions of all shared skills. Call at task "
                "start to discover related capabilities, even for familiar work. "
                "Read the strongest candidate when relevance is uncertain."
            ),
            annotations=ToolAnnotations(read_only_hint=True),
        )
        @_handle_errors
        def list_skills() -> list[dict[str, Any]]:
            return self.storage.list_skills()

    def _register_search_skills(self) -> None:
        @self.server.tool(
            description=(
                "Match any keyword against skill names or descriptions using "
                "case-insensitive substrings. Search before solving unfamiliar "
                "problems or creating a skill; read likely matches."
            ),
            annotations=ToolAnnotations(read_only_hint=True),
        )
        @_handle_errors
        def search_skills(
            keywords: Annotated[
                list[str],
                Field(
                    description="Topic keywords or short phrases; any keyword may match."
                ),
            ],
        ) -> list[dict[str, Any]]:
            return self.storage.search_skills(keywords)

    def _register_read_skill(self) -> None:
        @self.server.tool(
            description=(
                "Copy a complete shared skill into a local directory. Returns "
                "its path: open SKILL.md and needed supporting files. Check for "
                "wrong or missing steps; publish verified corrections with "
                "upsert_skill before finishing. Reading alone does not change "
                "shared memory."
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
                        "Fresh task-local parent directory for this download. "
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
                "Create or replace an entire shared skill directory. Publish "
                "verified additions or repairs that improve future tasks, including "
                "smooth workflows and repository-specific knowledge. State scope "
                "and prerequisites. Save verified recovery steps, not temporary "
                "tool unavailability. Search and read likely matches first; extend "
                "existing capabilities. For updates, read the latest package and "
                "preserve supporting files."
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
                        "Complete directory to publish, including SKILL.md and "
                        "all supporting files. Replaces the entire shared directory."
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
                "Delete a confirmed obsolete, invalid, or redundant shared "
                "skill. Read it first; repair knowledge that remains useful. "
                "For merges or renames, publish and verify the replacement "
                "before deleting the source."
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
