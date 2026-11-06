from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, ClassVar

from jinja2 import Template

from evolva.agents.interface import Agent, register_agent


@register_agent
class ClaudeAgent(Agent):
    """Install the Evolva Skill and MCP server into Claude Code."""

    type: ClassVar[str] = "claude"

    SKILL_DIR = Path("~/.claude/skills/evolva")
    CONFIG_PATH = Path("~/.claude.json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClaudeAgent:
        return cls()

    def install(self) -> None:
        """Write the Evolva Skill and merge the MCP server into .claude.json."""
        skill_dir = self.SKILL_DIR.expanduser()
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            self._render("skill.jinja"), encoding="utf-8"
        )

        config = self.CONFIG_PATH.expanduser()
        data = json.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
        data.setdefault("mcpServers", {})["evolva"] = json.loads(
            self._render("mcp.jinja")
        )
        config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def uninstall(self) -> None:
        """Remove the Skill and the MCP server entry from .claude.json."""
        shutil.rmtree(self.SKILL_DIR.expanduser(), ignore_errors=True)

        config = self.CONFIG_PATH.expanduser()
        if not config.exists():
            return

        data = json.loads(config.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", {})
        if "evolva" not in servers:
            return

        del servers["evolva"]
        config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _render(name: str) -> str:
        template = (Path(__file__).parent / name).read_text(encoding="utf-8")
        return Template(template).render()
