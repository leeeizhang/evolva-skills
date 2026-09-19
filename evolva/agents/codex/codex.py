from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, ClassVar

from jinja2 import Template

from evolva.agents.interface import Agent, register_agent

MCP_SECTION = "[mcp_servers.evolva]"


@register_agent
class CodexAgent(Agent):
    """Install the Evolva Skill and MCP server into Codex."""

    type: ClassVar[str] = "codex"

    CODEX_HOME = Path(os.environ.get("CODEX_HOME", "~/.codex"))
    SKILL_DIR = CODEX_HOME / "skills/evolva"
    CONFIG_PATH = CODEX_HOME / "config.toml"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CodexAgent:
        return cls()

    def install(self) -> None:
        """Write the Evolva Skill and register the MCP server in config.toml."""
        skill_dir = self.SKILL_DIR.expanduser()
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            self._render("skill.jinja"), encoding="utf-8"
        )

        config = self.CONFIG_PATH.expanduser()
        text = config.read_text(encoding="utf-8") if config.exists() else ""
        if any(line.strip() == MCP_SECTION for line in text.splitlines()):
            return

        config.parent.mkdir(parents=True, exist_ok=True)
        block = self._render("mcp.jinja").strip()
        prefix = text.rstrip()
        config.write_text(
            f"{prefix}\n\n{block}\n" if prefix else f"{block}\n",
            encoding="utf-8",
        )

    def uninstall(self) -> None:
        """Remove the Skill and the MCP server section from config.toml."""
        shutil.rmtree(self.SKILL_DIR.expanduser(), ignore_errors=True)

        config = self.CONFIG_PATH.expanduser()
        if not config.exists():
            return

        text = config.read_text(encoding="utf-8")
        cleaned = _drop_section(text, MCP_SECTION)
        if cleaned != text:
            config.write_text(cleaned, encoding="utf-8")

    @staticmethod
    def _render(name: str) -> str:
        template = (Path(__file__).parent / name).read_text(encoding="utf-8")
        return Template(template).render()


def _drop_section(text: str, header: str) -> str:
    """Remove a TOML table and its keys from the config text."""
    lines = text.splitlines(keepends=True)
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == header), None
    )
    if start is None:
        return text

    end = start + 1
    while end < len(lines) and not lines[end].strip().startswith("["):
        end += 1

    return "".join(lines[:start] + lines[end:])
