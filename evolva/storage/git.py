from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import Any, ClassVar

from evolva.storage.interface import Storage, register_storage
from evolva.types.skill import SKILL_FILE, Skill


@register_storage
class GitStorage(Storage):
    """Store skills in a git repository."""

    type: ClassVar[str] = "git"
    options: ClassVar[list[dict[str, str]]] = [
        {
            "name": "url",
            "prompt": "Git repository URL (e.g. git@github.com:you/skills.git)",
        },
        {"name": "branch", "prompt": "Branch", "default": "main"},
    ]

    STORAGE_DIR = Path("~/.evolva/git-storage")
    GIT_USERNAME = os.environ.get("GIT_USERNAME", "evolva")
    GIT_USEREMAIL = os.environ.get("GIT_USEREMAIL", "evolva@localhost")
    GIT_TIMEOUT = int(os.environ.get("GIT_TIMEOUT", "30"))

    def __init__(self, url: str, branch: str):
        self.url = url
        self.branch = branch
        self.path = self.STORAGE_DIR.expanduser() / self._storage_key(url, branch)

        if self.path.exists() and not (self.path / ".git").exists():
            shutil.rmtree(self.path)

        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                self._git("clone", "--", self.url, str(self.path), cwd=self.path.parent)
            except RuntimeError:
                shutil.rmtree(self.path, ignore_errors=True)
                raise

        try:
            self._git("rev-parse", "--verify", "HEAD")
        except RuntimeError:
            self._git("checkout", "-B", self.branch)
            self._git(
                "-c",
                f"user.name={self.GIT_USERNAME}",
                "-c",
                f"user.email={self.GIT_USEREMAIL}",
                "commit",
                "--allow-empty",
                "-m",
                "evolva: initialize storage",
            )
        else:
            current = self._git("symbolic-ref", "--short", "HEAD").stdout.strip()
            if current != self.branch:
                self._git("checkout", self.branch)

        try:
            self._sync()
        except RuntimeError as error:
            warnings.warn(f"Sync failed, using the local cache: {error}", stacklevel=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GitStorage:
        url = data.get("url")
        if not url:
            raise ValueError("Git storage requires a 'url'.")

        branch = data.get("branch")
        if not branch:
            raise ValueError("Git storage requires a 'branch'.")

        return cls(url=str(url), branch=str(branch))

    def list_skills(self) -> list[dict[str, Any]]:
        try:
            self._sync()
        except RuntimeError as error:
            warnings.warn(
                f"Sync failed, listing local skills only: {error}", stacklevel=2
            )

        skills = []
        for entry in sorted(self.path.iterdir()):
            if not entry.is_dir() or not (entry / SKILL_FILE).is_file():
                continue

            try:
                skills.append(Skill.from_dir(entry))
            except (ValueError, OSError) as error:
                warnings.warn(f"Skipping skill '{entry.name}': {error}", stacklevel=2)

        return [skill.to_dict() for skill in skills]

    def search_skills(self, keywords: list[str]) -> list[dict[str, Any]]:
        try:
            self._sync()
        except RuntimeError as error:
            warnings.warn(
                f"Sync failed, searching local skills only: {error}", stacklevel=2
            )

        matches = []
        for entry in sorted(self.path.iterdir()):
            if not entry.is_dir() or not (entry / SKILL_FILE).is_file():
                continue

            try:
                skill = Skill.from_dir(entry)
            except (ValueError, OSError) as error:
                warnings.warn(f"Skipping skill '{entry.name}': {error}", stacklevel=2)
                continue

            haystack = f"{skill.name} {skill.description}".lower()
            if any(keyword.lower() in haystack for keyword in keywords):
                matches.append(skill.to_dict())

        return matches

    def read_skill(self, skill_name: str, save_dir: str) -> None:
        try:
            self._sync()
        except RuntimeError as error:
            warnings.warn(
                f"Sync failed, reading the local skill only: {error}", stacklevel=2
            )

        source = self.path / skill_name
        if not (source / SKILL_FILE).is_file():
            raise ValueError(f"Unknown skill: {skill_name}")

        target = Path(save_dir).expanduser() / skill_name
        shutil.copytree(source, target, dirs_exist_ok=True)

    def upsert_skill(self, skill_name: str, upload_dir: str, message: str) -> None:
        source = Path(upload_dir).expanduser()
        if not source.is_dir():
            raise ValueError(f"Skill directory not found: {source}")
        if not (source / SKILL_FILE).is_file():
            raise ValueError(f"Skill directory must contain {SKILL_FILE}: {source}")

        target = self.path / skill_name
        if (
            not skill_name
            or Path(skill_name).name != skill_name
            or skill_name in {".", ".."}
        ):
            raise ValueError(f"Invalid skill name: {skill_name!r}")

        Skill.from_dir(source)

        try:
            self._sync()
        except RuntimeError as error:
            warnings.warn(
                f"Sync failed, upserting on the local state: {error}", stacklevel=2
            )

        relative = target.relative_to(self.path).as_posix()
        previous = self._git("rev-parse", "--verify", "HEAD").stdout.strip()

        try:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target, ignore=shutil.ignore_patterns(".git"))

            self._git("add", "-A", "--", relative)
            if self._git("status", "--porcelain", "--", relative).stdout.strip():
                self._git(
                    "-c",
                    f"user.name={self.GIT_USERNAME}",
                    "-c",
                    f"user.email={self.GIT_USEREMAIL}",
                    "commit",
                    "-m",
                    f"upsert({skill_name}): {message}",
                    "--",
                    relative,
                )
            self._git("push", "-u", "origin", "HEAD")
        except RuntimeError as error:
            try:
                self._sync()
            except RuntimeError:
                self._git("reset", "--hard", previous)

            raise RuntimeError(
                f"Failed to upsert skill '{skill_name}', local changes were rolled back: "
                f"{error}\nThe skill you edited is most likely stale: pull the latest "
                "version and apply your update again."
            ) from error

    def delete_skill(self, skill_name: str, message: str) -> None:
        target = self.path / skill_name
        if (
            not skill_name
            or Path(skill_name).name != skill_name
            or skill_name in {".", ".."}
        ):
            raise ValueError(f"Invalid skill name: {skill_name!r}")

        try:
            self._sync()
        except RuntimeError as error:
            warnings.warn(
                f"Sync failed, deleting on the local state: {error}", stacklevel=2
            )

        if not (target / SKILL_FILE).is_file():
            raise ValueError(f"Unknown skill: {skill_name}")

        relative = target.relative_to(self.path).as_posix()
        previous = self._git("rev-parse", "--verify", "HEAD").stdout.strip()

        try:
            shutil.rmtree(target)
            self._git("add", "-A", "--", relative)
            if self._git("status", "--porcelain", "--", relative).stdout.strip():
                self._git(
                    "-c",
                    f"user.name={self.GIT_USERNAME}",
                    "-c",
                    f"user.email={self.GIT_USEREMAIL}",
                    "commit",
                    "-m",
                    f"delete({skill_name}): {message}",
                    "--",
                    relative,
                )
            self._git("push", "-u", "origin", "HEAD")
        except RuntimeError as error:
            try:
                self._sync()
            except RuntimeError:
                self._git("reset", "--hard", previous)

            raise RuntimeError(
                f"Failed to delete skill '{skill_name}', local changes were rolled back: "
                f"{error}\nThe skill was most likely stale: pull the latest version "
                "and try again."
            ) from error

    @staticmethod
    def _storage_key(url: str, branch: str) -> str:
        digest = hashlib.sha256(f"{url}\n{branch}".encode()).hexdigest()
        return digest[:12]

    def _sync(self) -> None:
        self._git("fetch", "origin")
        try:
            self._git("rev-parse", "--verify", f"origin/{self.branch}")
        except RuntimeError:
            return

        self._git("checkout", "-f", "-B", self.branch, f"origin/{self.branch}")
        self._git("clean", "-fdx")

    def _git(
        self,
        *args: str,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=cwd or self.path,
                capture_output=True,
                text=True,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
                timeout=self.GIT_TIMEOUT,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(
                f"git {' '.join(args)} timed out after {self.GIT_TIMEOUT}s"
            ) from error

        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")

        return result
