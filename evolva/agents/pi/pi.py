from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, ClassVar

from jinja2 import Template

from evolva.agents.interface import Agent, register_agent


@register_agent
class PiAgent(Agent):
    """Install the Evolva Skill and native MCP server into Pi."""

    type: ClassVar[str] = "pi"

    AGENT_DIR = Path(os.environ.get("PI_CODING_AGENT_DIR", "~/.pi/agent"))
    SKILL_DIR = AGENT_DIR / "skills/evolva"
    CONFIG_PATH = AGENT_DIR / "mcp.json"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PiAgent:
        return cls()

    def install(self) -> None:
        """Write the Evolva Skill and merge its server into mcp.json."""
        config = self.CONFIG_PATH.expanduser()
        data = json.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
        if not isinstance(data, dict):
            raise ValueError(f"Expected a JSON object in {config}")
        servers = data.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            raise ValueError(f"Expected an mcpServers object in {config}")
        servers["evolva"] = json.loads(self._render("mcp.jinja"))

        skill_dir = self.SKILL_DIR.expanduser()
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            self._render("skill.jinja"), encoding="utf-8"
        )

        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def uninstall(self) -> None:
        """Remove only the Evolva Skill and MCP server entry."""
        config = self.CONFIG_PATH.expanduser()
        if config.exists():
            data = json.loads(config.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError(f"Expected a JSON object in {config}")
            servers = data.get("mcpServers", {})
            if not isinstance(servers, dict):
                raise ValueError(f"Expected an mcpServers object in {config}")
            if "evolva" in servers:
                del servers["evolva"]
                config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        shutil.rmtree(self.SKILL_DIR.expanduser(), ignore_errors=True)

    def curation_command(self) -> list[str]:
        return ["pi", "/skill:evolva Curate the shared skill library."]

    @staticmethod
    def _render(name: str) -> str:
        template = (Path(__file__).parent / name).read_text(encoding="utf-8")
        return Template(template).render()
