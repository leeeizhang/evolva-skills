# Working on Evolva

## Project purpose

Evolva is a shared skill and memory layer for AI agents. It helps agents reuse
knowledge across tools, sessions, and machines, then publish verified improvements
for the next task. Codex, Claude Code, and Pi are the current integrations; Git is
the current storage backend.

A skill is a readable directory containing `SKILL.md` and optional supporting
files. Keep this knowledge portable, user-owned, and independent of any one agent.

## Architecture

| Area | Responsibility |
| --- | --- |
| `evolva/agents/` | Adapt each agent's skill installation, MCP configuration, and curation command. |
| `evolva/storage/` | Discover, read, publish, and delete complete skill packages. |
| `evolva/mcp/server.py` | Expose storage through five MCP tools over stdio. |
| `evolva/cli.py` | Parse commands, configure storage, and start the TUI or MCP server. |
| `evolva/tui.py` | Guide configuration, agent install/uninstall, and curation setup. |
| `evolva/config.py` | Read and write `~/.evolva/config.yaml`. |
| `evolva/types/skill.py` | Parse skill metadata and serialize catalog entries. |

Agent and storage implementations use abstract interfaces, decorator registries,
and factories. Import built-in implementations in their package's `__init__.py`
to register them. The MCP server depends on `Storage`, not a specific backend.
Keep agent-specific configuration in adapters and backend-specific behavior in
storage implementations.

## Development standards

- Target Python 3.11+. Follow existing type hints, small functions, and Ruff rules.
- Extend the existing interfaces before adding another abstraction or dependency.
- Keep CLI/TUI code focused on input and orchestration; keep MCP tools thin.
- Preserve unrelated user configuration. Make install/uninstall safe to repeat.
- Treat upserts as complete package replacement; preserve supporting files.
- Keep skill names within the storage root. Validate inputs before modifying data.
- Report publication failures clearly; local changes do not mean a shared write
  succeeded. Use `ValueError` for invalid input and `RuntimeError` for operational
  failures handled by the current CLI and MCP boundaries.
- Keep stdout reserved for protocol traffic when running `evolva mcp`; send
  diagnostics to stderr.
- Keep shared instructions in agent templates and MCP guidance consistent.
- Add focused tests for behavior changes. Use temporary directories and local
  Git remotes; never modify real agent profiles or require live services in tests.
- Update docs and package data when adding integrations or changing behavior.
  Keep Ruff versions aligned in `pyproject.toml` and `.pre-commit-config.yaml`.

## Local checks

```bash
pip install -e ".[dev]"
pre-commit install
ruff check .
ruff format --check .
pytest
```

The test directory currently has no tests; CI accepts pytest's no-tests exit
code. Pre-commit runs lint, formatting, and file checks; pytest runs separately.
The CLI agent enable/disable handler is currently a stub; use the TUI for that
workflow until it is implemented.

## Further reading

- [Purpose and principles](docs/philosophy.md)
- [Architecture and design patterns](docs/architecture.md)
- [Add an agent](docs/adding-agents.md)
- [Add a storage backend](docs/adding-storage.md)
