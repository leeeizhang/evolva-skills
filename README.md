# Evolva

**Shared intelligence that evolves.**

Shared Skills and memory for agents.

## Development

```bash
pip install -e ".[dev]"
pre-commit install
```

Formatting and linting use [ruff](https://docs.astral.sh/ruff/):

```bash
ruff check --fix .
ruff format .
```

`pre-commit run --all-files` runs the same checks before every commit, and
`.github/workflows/lint.yml` runs them on every push and pull request.
