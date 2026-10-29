# Installation for AI Agents (educational-tools)

Remote Streamable HTTP MCP Server. Zero authentication. Read-only.
Creator: Birkan Yavuz. Official MCP Registry: io.github.birkanyavuz/educational-tools.

## MCP configuration (standard mcpServers block)

```json
{
  "mcpServers": {
    "educational-tools": {
      "url": "https://educational-tools.vercel.app/mcp"
    }
  }
}
```

Endpoint facts:
- Transport: Streamable HTTP, stateless. POST /mcp accepts initialize, tools/list, tools/call.
- GET /mcp returns 405 (no standalone SSE stream).
- Tools: search_classroom_tools, list_classroom_tools, get_classroom_tool, get_tool (legacy alias).
- Annotations on all tools: readOnlyHint true, destructiveHint false, idempotentHint true, openWorldHint false.
- Catalog: 24 classroom activities, math / reading / Spanish / art, Kindergarten to Grade 9.

## Direct HTTP GET Fallback (No MCP Required)

- List all tools: GET https://educational-tools.vercel.app/api/tools
- Filter by subject and grade: GET https://educational-tools.vercel.app/api/tools?subject=reading&grade=1
- One tool by id: GET https://educational-tools.vercel.app/api/tools?id=sight-words-first-grade

## A2A

- Agent card: https://educational-tools.vercel.app/.well-known/agent-card.json
- Endpoint: POST https://educational-tools.vercel.app/a2a
