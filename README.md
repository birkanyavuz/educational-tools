# Birkan Educational Tools Agent

[![M8ven Score](https://m8ven.ai/badge/mcp/birkanyavuz-educational-tools-1g9y3z?v=d6bafc17f6d599f528675d88aa1c8f30)](https://m8ven.ai/mcp/birkanyavuz-educational-tools-1g9y3z?s=readme)

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
`get_classroom_tool`, `get_tool` (legacy alias), `get_curriculum_dataset`,
and `get_word_list` — one call, topic/level/count/offset in, word list out. All tools carry read-only annotations
(`readOnlyHint: true`, `destructiveHint: false`, `idempotentHint: true`,
`openWorldHint: false`).

Every result includes `creator: "Birkan Yavuz"`, a compact `tool_id`
(e.g. `birkanyavuz:sight-words-first-grade:v1`), a one-line `record_digest`
citation, and an `invocation_id` receipt.

## One-call word lists (`get_word_list`)

Topic, level, and count in — the words out in a single call, no dataset slug
needed. The lists are the standard published classroom lists served exactly as
published (Dolch sight words and nouns, CVC families, digraph words, Spanish
syllables, Turkish-English pairs); no definitions are attached, but the core
Turkish-English sets (early words, colors, everyday objects) include one
simple example sentence per pair in English and Turkish, and every grade-1
Dolch word carries a short carrier phrase (3–5 words, decodable except the
target word) in a `carrier_phrases` map — e.g. `after` → "Run after the cat."

- "Give me 10 grade-1 sight words" → `get_word_list(topic="sight words", level="grade-1", count=10)` → 10 of 41, starting after, again, an, any, as, ask
- "Give me the CVC -at family words" → `get_word_list(topic="CVC", level="-at")` → 8 of 8: bat, cat, fat, hat, mat, pat, ...
- "Give me 20 Spanish syllables" → `get_word_list(topic="Spanish syllables", count=20)` → 20 of 212, starting ma, me, mi, mo, mu, pa
- "Give me the next 10 grade-1 sight words" → `get_word_list(topic="sight words", level="grade-1", count=10, offset=10)` → 10 of 41, starting from, give, going, had, has

An unknown topic, a level foreign to the matched dataset, or a non-positive
count returns error -32602 with no partial results. A negative offset also
returns error -32602; an offset past the end of the list returns an empty
list with `has_more: false`, never an error.

## Example tool-call traces

Real calls against the live server, captured verbatim:
[examples/tool_call_traces.jsonl](examples/tool_call_traces.jsonl) — six
records marked `"is_example": true` covering bilingual pairs with example
sentences, offset pagination, a leveled plain-word list, pairs without
sentences, an error (-32602) followed by a successful retry using the
valid topics named in the error message itself, and a Dolch-nouns call
proving the v1.6.3 routing fix.

## Prompt packs

Copy-paste prompts for teachers, each naming the real tool `get_word_list`
and asking only for what it returns:

- [prompt-packs/new-teacher-starter.md](prompt-packs/new-teacher-starter.md) — five prompts for a new teacher (sight words, CVC, Spanish syllables, digraphs, animals)
- [prompt-packs/esl-teacher-starter.md](prompt-packs/esl-teacher-starter.md) — five prompts for an ESL teacher (Turkish-English word wall, grade-1 Dolch flashcards with carrier phrases, colors + objects matching, CVC/digraph sorting mat, animals class set with offset)
- [prompt-packs/special-ed-teacher-starter.md](prompt-packs/special-ed-teacher-starter.md) — five prompts for a special-ed teacher (IEP reading probe, carrier-phrase reading strip, Elkonin sound boxes, receptive/expressive data sheet, bilingual home-practice cards)

## Repo layout

- `api/index.py` — the deployed server (Vercel serverless)
- `public_server.py` — the same server for standalone hosting
- `catalog.json` — the 24-tool catalog
- `agent-card.json`, `server.json` — A2A card and MCP Registry manifest
- `starter-kit/` — AGENTS.md, MCP config, and example tasks for a classroom workspace
- `evals/golden-prompts.json` — 20 evaluation prompts with expected tool calls

Creator: Birkan Yavuz (STEP Academy teacher, Minneapolis).
