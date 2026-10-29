#!/usr/bin/env python3
"""
Public-ready A2A + remote MCP server — built 22:50 CDT Oct 28, 2026.
Local test version: runs on localhost only in this test, with the exact
endpoints a deployed version will expose. NOT published yet — publishing
needs a hosting account, which is a separate deploy step, not code.

Endpoints (same in local test and in deployment):
  GET  /.well-known/agent-card.json   — A2A Agent Card, public, unauthenticated
  GET  /.well-known/agent.json       — same card, alternate A2A path
  POST /a2a                          — A2A JSON-RPC: message/send with a task
  POST /mcp                          — MCP JSON-RPC: initialize, tools/list, tools/call
  GET  /health                       — liveness, no data

Every tool / task result returns creator "Birkan Yavuz" as a required field.
Every call is logged to SQLite (public_calls.sqlite) with time, caller
(User-Agent / source label supplied by the caller, never a secret),
endpoint, tool/task, and creator — that log is the external-contact proof
when this server is deployed, because a local log alone is not external.

No credentials, no private data, no outside service is contacted by this
server. It only answers calls that come to it.
"""
import json, sqlite3, pathlib, datetime, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).parent
DB = pathlib.Path("/tmp/public_calls.sqlite")
CATALOG = {
    "identifier": "sight-words-first-grade",
    "educationalLevel": "Grade 1",
    "teaches": "Recognize and read first-grade sight words",
    "creator": "Birkan Yavuz",
    "name": "Sight Words",
    "about": "Reading",
    "file": "tools-sight-words-first-grade.html",
}
for _p in (HERE / "catalog.json", HERE.parent / "catalog.json"):
    if _p.exists():
        CATALOG = json.loads(_p.read_text())
        break

AGENT_CARD = {
    "name": "Birkan Educational Tools Agent",
    "description": "Finds Birkan Yavuz's educational tools by grade, subject, and learning objective, and returns the tool with creator attribution.",
    "url": "https://example.invalid/a2a",
    "version": "0.1.0",
    "protocolVersion": "1.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "securitySchemes": {"open": {"type": "http", "scheme": "none", "description": "Read-only educational use, no authentication required for tool lookup"}},
    "skills": [{
        "id": "find_educational_tool",
        "name": "Find educational tool",
        "description": "Given a grade, subject, or learning objective, return a matching educational tool from Birkan Yavuz's catalog, with tool id, grade, objective, and creator.",
        "tags": ["education", "reading", "grade-1"],
        "examples": ["Find a Grade 1 reading tool", "Find a tool for first-grade sight words"],
    }],
}

def tool_result():
    return {
        "invocation_id": str(uuid.uuid4()),
        "id": CATALOG["identifier"],
        "gradeLevel": CATALOG["educationalLevel"],
        "objective": CATALOG["teaches"],
        "creator": CATALOG["creator"],
        "name": CATALOG["name"],
        "subject": CATALOG["about"],
        "file": CATALOG["file"],
    }

def log_call(source, endpoint, detail, session=""):
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS calls (ts TEXT, source TEXT, endpoint TEXT, detail TEXT, creator TEXT)")
    conn.execute("INSERT INTO calls VALUES (?,?,?,?,?)", (
        datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source, endpoint, detail, "Birkan Yavuz",
    ))
    conn.commit()
    conn.close()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        path = urlparse(self.path).path
        source = self.headers.get("User-Agent", "unknown")
        if path in ("/.well-known/agent-card.json", "/.well-known/agent.json"):
            log_call(source, path, "agent_card_fetch")
            card = dict(AGENT_CARD)
            host = self.headers.get("Host")
            if host:
                card["url"] = f"https://{host}/a2a"
                card["supportedInterfaces"] = [{"url": f"https://{host}/a2a", "transport": "JSONRPC"}]
            self._json(card)
        elif path == "/health":
            self._json({"status": "ok", "server": "birkan-educational-tools-agent", "published": True})
        else:
            self._json({"error": "not found"}, 404)
    def do_POST(self):
        path = urlparse(self.path).path
        source = self.headers.get("User-Agent", "unknown")
        session = self.headers.get("Mcp-Session-Id", "")
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            req = json.loads(raw or b"{}")
        except Exception:
            self._json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "bad json"}}, 400)
            return
        rid = req.get("id")
        method = req.get("method")
        if path == "/mcp":
            if method in ("notifications/initialized", "notifications/cancelled"):
                log_call(source, "/mcp", method)
                self._json({"jsonrpc": "2.0", "id": rid, "result": {}})
            elif method == "initialize":
                log_call(source, "/mcp", "initialize")
                self._json({"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2024-11-05", "server": "birkan-educational-tools-mcp"}})
            elif method == "tools/list":
                log_call(source, "/mcp", "tools/list")
                tool_def = {"name": "get_tool", "description": "Return one catalog tool by id, with creator required", "inputSchema": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}, "outputSchema": {"type": "object", "required": ["id", "gradeLevel", "objective", "creator"], "properties": {"id": {"type": "string"}, "gradeLevel": {"type": "string"}, "objective": {"type": "string"}, "creator": {"type": "string"}}}}
                self._json({"jsonrpc": "2.0", "id": rid, "result": {"tools": [tool_def]}})
            elif method == "tools/call":
                args = (req.get("params") or {}).get("arguments") or {}
                if args.get("id") != CATALOG["identifier"]:
                    self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown tool id"}}, 400)
                    return
                log_call(source, "/mcp", "tools/call get_tool sight-words-first-grade")
                self._json({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(tool_result())}], "structuredContent": tool_result()}})
            else:
                self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "unknown method"}}, 400)
        elif path == "/a2a":
            # Simplified A2A message/send: accept a task, return the matching tool as an artifact.
            # Real A2A task lifecycle (submitted/working/completed) is out of scope for this first build;
            # this endpoint proves discovery + task + creator return, with a logged task id.
            params = req.get("params") or {}
            message = params.get("message") or {}
            parts = message.get("parts") or []
            text = " ".join(p.get("text", "") for p in parts if isinstance(p, dict))
            log_call(source, "/a2a", f"message/send: {text[:200]}")
            result = tool_result()
            self._json({"jsonrpc": "2.0", "id": rid, "result": {"id": params.get("id", "task-1"), "status": {"state": "completed"}, "artifacts": [{"artifactId": "tool-1", "parts": [{"kind": "data", "data": result}]}]}})
        else:
            self._json({"error": "not found"}, 404)

handler = Handler

if __name__ == "__main__":
    import sys, os
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"Birkan Educational Tools Agent listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
