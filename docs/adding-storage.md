# Add a Storage Backend

A storage backend persists complete skill packages behind the `Storage`
interface. Use `evolva/storage/git.py` as a reference; keep backend details out of
the MCP server and agent adapters.

## 1. Implement the interface

Create `evolva/storage/example.py`. Subclass `Storage` from
`evolva.storage.interface`, decorate it with `@register_storage`, and set a unique
`type`, such as `"example"`.

Declare `options` for the TUI to prompt for configuration:

```python
type = "example"
options = [{"name": "root", "prompt": "Storage root", "default": "~/skills"}]
```

The CLI supplies options as strings from `key=value` arguments. Validate and
convert them in the `from_dict` class method, then return a usable instance.
Do not assume the TUI's optional `default` values are supplied by the CLI.

| Method | Contract |
| --- | --- |
| `list_skills()` | Return dictionaries containing `name` and `description`. |
| `search_skills(keywords)` | Match any keyword against names or descriptions, using case-insensitive substrings. |
| `read_skill(skill_name, save_dir)` | Copy the whole package to `<save_dir>/<skill_name>`; return `None`. |
| `upsert_skill(skill_name, upload_dir, message)` | Create or replace the whole package from `upload_dir`; return `None`. |
| `delete_skill(skill_name, message)` | Remove the named package; return `None`. |

## 2. Preserve package semantics

- Keep `SKILL.md` and all supporting files together. Use `Skill.from_dir()` for
  metadata validation; its parser requires closed frontmatter and a description.
- Treat skill names as single directory names; prevent access outside the root.
- Make an upsert replace stale files as well as add new ones.
- Define sync, caching, and failure recovery inside the backend. Report failed
  publication; do not return success after only saving a local copy.
- Use `ValueError` for invalid input or unknown skills and `RuntimeError` for
  operational failures that should become MCP tool errors.

## 3. Register and configure

Import the class in `evolva/storage/__init__.py` and add it to `__all__`:

```python
from evolva.storage.example import ExampleStorage
```

The import runs the decorator. The TUI uses the registry and `options`
automatically; CLI configuration uses the same factory:

```bash
evolva set storage example root=~/skills
```

Setup constructs the backend to validate it before saving configuration. The
existing MCP tools need no changes when the storage contract stays the same.

## 4. Verify the backend

Test factory registration, missing options, metadata, keyword matching, and all
read/write operations. Include nested supporting files, replacement of stale
files, invalid names, missing skills, and failure recovery. Use temporary storage
and local services or test doubles, then exercise the backend through
`MCPServer(storage)`. Run the checks in [AGENTS.md](../AGENTS.md#local-checks) and
document the new configuration options.
