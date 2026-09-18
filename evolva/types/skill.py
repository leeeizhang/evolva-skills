from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SKILL_FILE = "SKILL.md"


@dataclass
class Skill:
    """A skill directory following the Agent Skills format."""

    name: str
    description: str
    path: Path | None = None
    body: str = ""

    @classmethod
    def from_dir(cls, skill_dir: Path) -> Skill:
        text = (skill_dir / SKILL_FILE).read_text(encoding="utf-8")
        values, body = cls.parse_frontmatter(text)

        return cls(
            name=skill_dir.name,
            description=values["description"],
            path=skill_dir,
            body=body,
        )

    @staticmethod
    def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
        """Split SKILL.md into frontmatter values and markdown body.

        The frontmatter must be closed and provide `description`.
        Only top-level `key: value` pairs are read; nested maps are ignored.
        """
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            raise ValueError(f"{SKILL_FILE} must start with '---' frontmatter")

        values: dict[str, str] = {}
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                break
            if line.startswith((" ", "\t")):
                continue

            key, separator, value = line.partition(":")
            if separator:
                values[key.strip()] = value.strip().strip("\"'")
        else:
            raise ValueError(f"{SKILL_FILE} frontmatter is not closed by '---'")

        if not values.get("description"):
            raise ValueError(f"{SKILL_FILE} frontmatter requires 'description'")

        return values, "\n".join(lines[index + 1 :])

    def to_dict(self) -> dict[str, str]:
        """Serialize for skill listings and MCP output."""
        return {
            "name": self.name,
            "description": self.description,
        }
