# Architecture

Evolva separates agent integration, skill persistence, and user interfaces.

```text
Setup:    CLI / TUI -> registries + factories -> agent adapters / storage
Runtime:  Agent -> MCP over stdio -> MCPServer -> Storage -> skill library
```

## Components

| Component | Role |
| --- | --- |
| `evolva/agents/` | Install an Evolva skill and MCP configuration for each agent; provide a curation command. |
| `evolva/storage/` | Implement the common skill operations; Git currently uses a local clone and remote sync. |
| `evolva/mcp/server.py` | Publish `list_skills`, `search_skills`, `read_skill`, `upsert_skill`, and `delete_skill`. |
| `evolva/cli.py` | Route commands, validate storage setup, and launch the MCP server or TUI. |
| `evolva/tui.py` | Discover registered implementations and guide setup, installation, removal, and curation. |
| `evolva/config.py` | Persist storage settings and enabled agent names in `~/.evolva/config.yaml`. |
| `evolva/types/skill.py` | Read `SKILL.md` frontmatter and provide name/description metadata. |

## Design patterns

- **Ports and adapters:** `Agent` and `Storage` define contracts; concrete
  integrations own product-specific configuration and persistence details.
- **Registry and factory:** decorators register classes by `type`; factories
  construct them from dictionaries. Package imports load built-ins explicitly.
- **Dependency injection:** `MCPServer(storage)` receives a `Storage` instance,
  so tools work without knowing how skills are stored.
- **Thin protocol facade:** MCP tools delegate operations and translate
  `ValueError` and `RuntimeError` into tool errors.
- **Template-based integration:** Jinja files hold agent instructions and MCP
  configuration snippets. Python handles their installation and removal.

These are ordinary Python modules and explicit imports. Adding a provider does
not require a separate plugin loader.

## Data flow

1. Setup validates storage settings before saving configuration. The TUI installs
   an agent adapter and records its enabled state.
2. The agent launches `evolva mcp`. The CLI loads configuration, creates storage,
   and injects it into `MCPServer`.
3. Catalog tools return names and descriptions. `read_skill` copies a complete
   package to `<save_dir>/<skill_name>` and returns that local path.
4. The agent reads and edits local files. `upsert_skill` publishes the complete
   directory; `delete_skill` removes a package.

Git reads attempt a sync and may use cached data with a warning. Writes commit
and push; failures are reported to the caller. Git owns this behavior, not MCP.

## Current boundaries

The TUI handles agent installation and removal. CLI storage setup and MCP startup
are implemented; `evolva set agent` currently raises `NotImplementedError`.
Curation refreshes an integration and prints a command for a new agent session.

See [agent extensions](adding-agents.md) and [storage extensions](adding-storage.md)
for the implementation steps.
