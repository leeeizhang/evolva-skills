# Why Evolva Exists

Agents often solve the same problem again because useful knowledge stays inside
one conversation or one tool. Evolva gives that knowledge a shared, durable home.

## Shared knowledge

An insight learned by one agent should help another. Skills travel across agent
products, sessions, and machines through a common library and MCP interface.
The installed Evolva skill teaches an agent how to use this shared library.

## Knowledge that improves

Reuse is the start, not the end. Agents should check instructions against real
results, repair verified mistakes, and publish useful methods from successful
work. The loop is simple: discover, reuse, verify, improve, share.

Save reusable procedures with clear scope and prerequisites. Avoid transcripts,
temporary task state, secrets, and unsupported claims. If a task teaches nothing
useful for future work, there is nothing to publish.

## Ownership and continuity

Skills are plain directories with readable Markdown and supporting files. Users
control where they live. Git provides history and sharing without requiring a
hosted Evolva service. Other backends can implement the same storage interface.

## A small connecting layer

Evolva connects existing agents to reusable knowledge. It does not run their
reasoning or task workflows. Agent adapters handle integration, storage backends
handle persistence, and MCP gives them a common boundary. Keep that boundary
small so the library can outlast any individual agent.
