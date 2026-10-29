#!/usr/bin/env python3
"""
Local MCP-style server — stdio JSON-RPC only, localhost / local process only.
No network, no outside contact, no publishing, no account.

Protocol (minimal, MCP-like):
  {"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
  {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
  {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_tool","arguments":{"id":"sight-words-first-grade"}}}

tools/call returns a typed result with outputSchema: creator is required.
If a caller asks for a tool id not in catalog.json, it returns an error, not a guess.
"""
import json, sys, pathlib

HERE = pathlib.Path(__file__).parent
CATALOG = json.loads((HERE / "catalog.json").read_text())

OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["id", "gradeLevel", "objective", "creator"],
    "properties": {
        "id": {"type": "string"},
        "gradeLevel": {"type": "string"},
        "objective": {"type": "string"},
        "creator": {"type": "string"},
    },
}

def tool_result():
    return {
        "id": CATALOG["identifier"],
        "gradeLevel": CATALOG["educationalLevel"],
        "objective": CATALOG["teaches"],
        "creator": CATALOG["creator"],
        "name": CATALOG["name"],
        "subject": CATALOG["about"],
        "file": CATALOG["file"],
    }

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}), flush=True)
            continue
        method = req.get("method")
        rid = req.get("id")
        if method == "initialize":
            result = {"protocolVersion": "local-1", "server": "first-contact-local-hub", "capabilities": ["tools"]}
        elif method == "tools/list":
            result = {"tools": [{"name": "get_tool", "description": "Return one catalog tool by id, with creator required", "inputSchema": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}, "outputSchema": OUTPUT_SCHEMA}]}
        elif method == "tools/call":
            args = (req.get("params") or {}).get("arguments") or {}
            if args.get("id") != CATALOG["identifier"]:
                print(json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown tool id"}}), flush=True)
                continue
            result = {"content": [{"type": "text", "text": json.dumps(tool_result())}], "structuredContent": tool_result(), "outputSchema": OUTPUT_SCHEMA}
        else:
            print(json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "unknown method"}}), flush=True)
            continue
        print(json.dumps({"jsonrpc": "2.0", "id": rid, "result": result}), flush=True)

if __name__ == "__main__":
    main()
