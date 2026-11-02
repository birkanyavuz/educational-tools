# educational-tools-mcp

Stdio bridge to **Birkan Yavuz's** free, zero-auth K-12 Educational Tools MCP server.

Tools: search/list/get 24 interactive classroom tools (math, reading, Spanish, art) and
`get_curriculum_dataset` — real word lists: Dolch sight words by level (220), Dolch nouns (94),
CVC word families (75), digraph words (21), Spanish syllables (212 items), Turkish-English
early words (30 pairs). Every result carries creator attribution.

## Use

```json
{ "mcpServers": { "educational-tools": { "command": "npx", "args": ["-y", "educational-tools-mcp"] } } }
```

Or connect directly to the remote server (Streamable HTTP, no package needed):
`https://educational-tools.vercel.app/mcp`
Registry: `io.github.birkanyavuz/educational-tools`. License CC-BY-4.0. Creator: Birkan Yavuz.
