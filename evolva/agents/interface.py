from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class Agent(ABC):
    type: ClassVar[str]

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Agent:
        """Create an Agent instance from configuration."""
        raise NotImplementedError

    @abstractmethod
    def install(self) -> None:
        """Install Evolva integration for this agent."""
        raise NotImplementedError

    @abstractmethod
    def uninstall(self) -> None:
        """Uninstall Evolva integration for this agent."""
        raise NotImplementedError


_AGENT_REGISTRY: dict[str, type[Agent]] = {}


def register_agent(agent_cls: type[Agent]) -> type[Agent]:
    """Register an Agent implementation."""
    if agent_cls.type in _AGENT_REGISTRY:
        raise ValueError(f"Agent already registered: {agent_cls.type}")

    _AGENT_REGISTRY[agent_cls.type] = agent_cls
    return agent_cls


def create_agent(data: dict[str, Any]) -> Agent:
    """Create an Agent from configuration data."""
    agent_type = data.get("type")

    if not agent_type:
        raise ValueError("Agent type is required.")

    agent_cls = _AGENT_REGISTRY.get(agent_type)

    if agent_cls is None:
        raise ValueError(f"Unknown agent type: {agent_type}")

    return agent_cls.from_dict(data)
