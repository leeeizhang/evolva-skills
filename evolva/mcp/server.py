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


def build_instructions(storage: Storage, instruction: str = "") -> str:
    instructions = "\n".join(
        [
            "Evolva is a shared skill library and reusable memory across agents "
            "and sessions. Its catalog includes skills absent from the agent's "
            "installed skill list.",
            "Use Evolva through its MCP tools for shared-library operations. "
            "Discover relevant skills with list_skills or search_skills. "
            "read_skill downloads a complete package and returns its local path: "
            "open SKILL.md and needed supporting files. Apply guidance with "
            "judgment, checking assumptions against current evidence.",
            "Publishing is optional. "
            "Consider sharing durable, non-obvious insight that materially helps "
            "with similar problems.",
            "New skills should offer reusable capabilities comparable in "
            "generality and quality to established skills in the library. Search "
            "and read related skills before extending one or creating a distinct "
            "capability. Updates must preserve a skill's generality and valid "
            "approaches. Keep local constraints and user corrections scoped.",
            "Preserve reusable materials discovered during work, along with the "
            "context needed to understand and use them. Let the agent decide how "
            "to apply and combine these materials for the current task. "
            "Write for human readers, connecting the background, problem, and "
            "solution in a coherent narrative.",
            "When publishing, verify changed claims and read the latest package "
            "into a fresh temporary directory before updating. upsert_skill replaces the "
            "entire package: preserve supporting files. Confirm success and "
            "report blocked verification or publication; local edits alone are "
            "not published. Before using delete_skill, read the skill and confirm "
            "it is obsolete, invalid, or redundant; verify any replacement first.",
            f"Skills at connection: {_names(storage)}",
        ]
    )

    if instruction:
        instructions += f"\n\n{instruction}"
    return instructions


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

    def __init__(self, storage: Storage, instruction: str = "") -> None:
        self.storage = storage
        self.server = SDKServer(
            "evolva",
            instructions=build_instructions(storage, instruction),
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
                "List names and descriptions of all shared skills to discover "
                "capabilities relevant to the current task."
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
                "case-insensitive substrings. Use it to find relevant guidance "
                "or related capabilities before creating or updating a skill."
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
                "its path: open SKILL.md and needed supporting files locally. "
                "Check applicability against the current environment and evidence."
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
                        "Fresh temporary parent directory, for example under /tmp. "
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
                "Create or replace an entire shared skill directory. Publishing "
                "is optional: use for verified knowledge with durable reuse value. "
                "New capabilities should be comparable "
                "in generality and quality to established skills; updates must "
                "preserve existing scope and valid approaches. Explain the problem "
                "and reasoning for human readers. Search and read related skills "
                "first. For updates, read the latest package and preserve all "
                "supporting files; this replaces the entire package."
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
                "skill. Read it first to confirm the removal is appropriate. "
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
