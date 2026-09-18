from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class Storage(ABC):
    type: ClassVar[str]

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Storage:
        """Create a Storage instance from configuration."""
        raise NotImplementedError

    @abstractmethod
    def list_skills(self) -> list[dict[str, Any]]:
        """List available skills."""
        raise NotImplementedError

    @abstractmethod
    def search_skills(
        self,
        keywords: list[str],
    ) -> list[dict[str, Any]]:
        """Search skills."""
        raise NotImplementedError

    @abstractmethod
    def read_skill(
        self,
        skill_name: str,
        save_dir: str,
    ) -> None:
        """Read a skill into the given directory."""
        raise NotImplementedError

    @abstractmethod
    def upsert_skill(
        self,
        skill_name: str,
        upload_dir: str,
        message: str,
    ) -> None:
        """Create or update a skill."""
        raise NotImplementedError

    @abstractmethod
    def delete_skill(
        self,
        skill_name: str,
        message: str,
    ) -> None:
        """Delete a skill."""
        raise NotImplementedError


_STORAGE_REGISTRY: dict[str, type[Storage]] = {}


def register_storage(storage_cls: type[Storage]) -> type[Storage]:
    """Register a Storage implementation."""
    if storage_cls.type in _STORAGE_REGISTRY:
        raise ValueError(
            f"Storage already registered: {storage_cls.type}"
        )

    _STORAGE_REGISTRY[storage_cls.type] = storage_cls
    return storage_cls


def create_storage(data: dict[str, Any]) -> Storage:
    """Create a Storage from configuration data."""
    storage_type = data.get("type")

    if not storage_type:
        raise ValueError("Storage type is required.")

    storage_cls = _STORAGE_REGISTRY.get(storage_type)

    if storage_cls is None:
        raise ValueError(f"Unknown storage type: {storage_type}")

    return storage_cls.from_dict(data)
