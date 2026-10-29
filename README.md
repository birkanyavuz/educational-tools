# Birkan Educational Tools Agent

Zero-auth, read-only **MCP server + A2A agent** by Birkan Yavuz: a catalog of 24 real
classroom activities (math visualizers, reading and Sight Words modules, Spanish
syllables, art) for Kindergarten–Grade 9, with verifiable creator metadata in every result.

- **Live MCP endpoint:** `POST https://educational-tools.vercel.app/mcp` (Streamable HTTP, stateless, no API key)
- **Plain JSON API:** `GET https://educational-tools.vercel.app/api/tools?subject=math&grade=1`
- **A2A agent card:** `https://educational-tools.vercel.app/.well-known/agent-card.json`
- **Official MCP Registry:** `io.github.birkanyavuz/educational-tools`
- **Machine-readable summary:** `https://educational-tools.vercel.app/llms.txt`

## Install (for agents and their humans)

See `llms-install.md` for the copy-paste MCP config, or drop this repo's root
`.mcp.json` / `gemini-extension.json` into a workspace — installer agents read them
automatically. Tools: `search_classroom_tools`, `list_classroom_tools`,
`get_classroom_tool`, `get_tool` (legacy alias). All tools carry read-only annotations
(`readOnlyHint: true`, `destructiveHint: false`, `idempotentHint: true`,
`openWorldHint: false`).

Every result includes `creator: "Birkan Yavuz"`, a compact `tool_id`
(e.g. `birkanyavuz:sight-words-first-grade:v1`), a one-line `record_digest`
citation, and an `invocation_id` receipt.

## Repo layout

- `api/index.py` — the deployed server (Vercel serverless)
- `public_server.py` — the same server for standalone hosting
- `catalog.json` — the 24-tool catalog
- `agent-card.json`, `server.json` — A2A card and MCP Registry manifest
- `starter-kit/` — AGENTS.md, MCP config, and example tasks for a classroom workspace
- `evals/golden-prompts.json` — 20 evaluation prompts with expected tool calls

Creator: Birkan Yavuz (STEP Academy teacher, Minneapolis).
