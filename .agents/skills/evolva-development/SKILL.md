---
name: evolva-development
description: Development process and conventions for the Evolva codebase (evolva-skills repository). Use when changing Evolva code, TUI, storage, agents, MCP or docs; it captures the working style, architecture principles, code and README conventions, TUI standards, commit and CI rules, and verification recipes expected by the maintainer.
---

# Developing Evolva

## Working style

- Small, reviewable steps: one concern per change. Read the existing code first. Never redesign the architecture or add abstraction layers unless asked: "keep it small" wins over elegance.
- Respect layer boundaries: CLI/TUI stay thin; Agents integrate with agent environments; MCP is a thin bridge; Storage owns skill persistence; Git logic only lives in `GitStorage`.
- Extend through the registries in `evolva/agents/interface.py` and `evolva/storage/interface.py` (`register_*`, `create_*`, `list_*`, `get_storage_class`). No hardcoded implementation names in upper layers.
- No custom exception classes; raise `ValueError` / `RuntimeError` with actionable messages. No silent no-ops: show feedback or fail loudly.

## Code conventions

- Python 3.11+, `from __future__ import annotations` at the top of every module, type hints on functions.
- ruff must pass: `ruff check --fix .` and `ruff format .` (88 cols, config in `pyproject.toml`).
- Registry contract attributes use lower_case `ClassVar`s (`type`, `options`); module constants stay local to the class or module that uses them.
- Comments only when they add information. Prefer removing decorative comments.

## Packaging

- New non-Python resources (for example `*.jinja`) must be declared in `[tool.setuptools.package-data]` and verified by building a wheel and listing its contents.

## TUI standards (`evolva/tui.py`, questionary)

- Actions are single-select lists: arrow keys plus Enter to confirm. Never checkboxes for actions, and never pre-select.
- Installed state is displayed automatically as `✓ name`, read from `~/.evolva/config.yaml`; it is display, not something the user toggles.
- Storage questions are asked field by field; the prompts come from `Storage.options` declarations. Never hardcode storage fields in the TUI.
- `install` requires a configured storage; install and uninstall update the `agents` list in `~/.evolva/config.yaml`; every action returns to the main menu; Ctrl+C exits cleanly; errors print in red and return to the menu.

## Commits, CI, README

- Conventional commits, split by concern: `feat(tui): ...`, `chore(tooling): ...`, `docs: ...`. pre-commit hooks must pass; never use `--no-verify`.
- CI runs `lint.yml` (ruff check plus format check) and `test.yml` (pytest). There is intentionally no `tests/` directory; pytest exit code 5 (no tests collected) is treated as a skip. Add tests only when explicitly asked.
- README: centered `<h1>` with the slogan, one badge row, then Overview / Get started / Architecture / Contributing / License. Never use em dashes; use ":" or restructure the sentence. Keep sections minimal.

## Verification recipes

- The TUI cannot be driven through piped stdin (it needs a TTY): use a pty harness (`pty.fork` plus timed key writes) or monkeypatch the `questionary` prompts.
- Storage and agent checks: use a temporary `HOME` and `git init --bare` as an offline remote.
- Install targets: Codex writes `$CODEX_HOME/skills/evolva/SKILL.md` plus `[mcp_servers.evolva]` in `$CODEX_HOME/config.toml`; Claude writes `~/.claude/skills/evolva/SKILL.md` plus `mcpServers.evolva` in `~/.claude.json`.
- Sandboxes: use `ruff --no-cache`, `pytest -p no:cacheprovider`, and expect that temp directories may be unavailable.
