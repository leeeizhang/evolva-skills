<div align="center">

<h1 align="center">Evolva: Shared intelligence that evolves.</h1>

[![Lint](https://github.com/leeeizhang/evolva-skills/actions/workflows/lint.yml/badge.svg)](https://github.com/leeeizhang/evolva-skills/actions/workflows/lint.yml)
[![Unit Tests](https://github.com/leeeizhang/evolva-skills/actions/workflows/test.yml/badge.svg)](https://github.com/leeeizhang/evolva-skills/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://github.com/leeeizhang/evolva-skills)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/leeeizhang/evolva-skills/blob/main/LICENSE)

</div>

## Overview

Evolva is a **shared skill and memory layer for agents**. Two ideas hold it
together: **shared** (one memory serves every agent) and **evolving** (every
reuse makes the skills better).

- ♻️ **Skills that iterate themselves**: an agent reuses a skill, improves it with
  what it just learned, and publishes it back, so knowledge compounds.
- 🌐 **Heterogeneous & distributed**: Codex, Claude, or anything that speaks MCP
  share a single repository across sessions and machines.
- 🕰 **Cross-session continuity**: nothing is lost when a session ends; the next
  session starts from everything the previous ones learned.
- 🏠 **Local-first & self-hosted**: skills live in your own Git repository: no
  hosted service, no vendor lock-in.

## Get started

### Installation

```bash
pip install --user git+https://github.com/leeeizhang/evolva-skills
```

### Usage

Two interfaces: pick either.

#### 1. Interactive

A guided flow that covers install, configuration, and uninstall:

```bash
evolva
```

#### 2. API

The same operations, scriptable:

**Step 1: attach the shared memory** (any Git remote works)

```bash
evolva set storage git url=git@github.com:<you>/skills.git branch=main
```

**Step 2: install it for your agents**

```bash
evolva set agent codex --enable
evolva set agent claude --enable
```

#### Uninstall

```bash
evolva set agent codex --disable
evolva set agent claude --disable
```

This removes the skill and the MCP configuration from that agent.

## Architecture

```text
   Codex        Claude        any agent
     │            │               │
     └────────────┼───────────────┘
                  │  MCP (stdio)
                  ▼
          ┌───────────────┐
          │    evolva     │   list · search · read · upsert · delete
          └───────┬───────┘
                  │  sync
                  ▼
        ┌───────────────────┐
        │      Storage      │   maintained in a Git skill repository
        └───────────────────┘
```

`evolva set agent` wires the skill and the MCP server (`evolva mcp`) into each
agent; `evolva set storage` points storage at your Git repository. Every skill is
a plain directory with a `SKILL.md`, so the shared memory stays readable,
diffable, and yours: configuration lives in `~/.evolva/config.yaml`.

## Contributing

Pull requests are welcome. For local development:

```bash
pip install -e ".[dev]"
pre-commit install
```

Pre-commit runs [ruff](https://docs.astral.sh/ruff/) for lint and format, and
`pytest` for tests.

## License

Check [MIT License](LICENSE) file for more information.
