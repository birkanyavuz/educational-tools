# Birkan Educational Tools Agent

Public-ready A2A + MCP server for Birkan Yavuz's educational tools.

- Agent Card: GET /.well-known/agent-card.json
- A2A: POST /a2a
- MCP: POST /mcp (initialize, tools/list, tools/call get_tool)
- Health: GET /health

First tool: Sight Words, Grade 1, Reading — Recognize and read first-grade sight words.
Creator, required in every tool result: Birkan Yavuz.

Run locally:
  python3 public_server.py 8000

Run on a host (Render / Railway / any Python host):
  HOST=0.0.0.0 PORT=$PORT python3 public_server.py

No dependencies, Python standard library only. No credentials, no private data.
Local test: python3 test_public_server.py
