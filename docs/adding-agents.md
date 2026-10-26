# Add an Agent

An agent adapter installs Evolva into an existing agent product. Use
`evolva/agents/codex/` or `evolva/agents/pi/` as a reference.

## 1. Implement the interface

Create a package such as:

```text
evolva/agents/nova/
  __init__.py
  nova.py
  skill.jinja
  mcp.jinja
```

In `nova.py`, subclass `Agent` from `evolva.agents.interface`, decorate the class
with `@register_agent`, and give it a unique `type`, such as `"nova"`.

| Method | Required behavior |
| --- | --- |
| `from_dict(cls, data)` | Class method that validates configuration and returns an instance. |
| `install()` | Write the Evolva skill and register an MCP server running `evolva mcp`. |
| `uninstall()` | Remove only Evolva's skill and MCP entry. |
| `curation_command()` | Return a `list[str]` of command arguments that start a curation session. |

The TUI currently constructs agents with only `{"type": name}`. Use sensible
defaults or environment settings; extend configuration explicitly if more fields
are required. The TUI prints the curation command for the user to run.

## 2. Add templates and registration

Adapt `skill.jinja` from an existing integration. Preserve discovery, verified
learning, and complete-package publication guidance; adjust agent-specific syntax.
Make `mcp.jinja` match the target agent's configuration format.

Import the class in `evolva/agents/__init__.py` and add it to `__all__`:

```python
from evolva.agents.nova.nova import NovaAgent
```

The import executes the registration decorator. `__all__` alone does not register
the class. Add template packaging under `[tool.setuptools.package-data]`:

```toml
"evolva.agents.nova" = ["*.jinja"]
```

## 3. Verify the integration

- Check `list_agents()` includes `nova` and `create_agent({"type": "nova"})` works.
- Test install/uninstall twice, missing files, and existing unrelated settings.
  Redirect all profile paths to temporary directories.
- Check the rendered MCP entry and the curation command's argument list.
- Build a wheel and check that it contains both templates.
- Try install, curate, and uninstall through `evolva` in a disposable profile.

The TUI discovers registered agents automatically. The CLI agent handler is
currently a stub, so do not rely on `evolva set agent` for verification. Run the
checks in [AGENTS.md](../AGENTS.md#local-checks) and document the new integration.
