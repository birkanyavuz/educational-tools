#!/usr/bin/env python3
"""
Birkan Educational Tools Agent — A2A + remote MCP server, v1.1.0.
Upgraded Oct 29, 2026 following the Argon brainstorm (First Contact chat):
  - Stateless Streamable HTTP MCP: POST /mcp accepts calls with or without
    Mcp-Session-Id (serverless-safe); GET/DELETE /mcp return 405.
  - CORS with Access-Control-Expose-Headers: Mcp-Session-Id for browser
    inspectors (Smithery/Glama playgrounds).
  - Granular, annotated tools instead of one vague get_tool:
    search_classroom_tools, list_classroom_tools, get_classroom_tool,
    plus get_tool kept as a legacy alias. All read-only annotations set.
  - Real catalog depth: Birkan Yavuz's actual classroom apps from his
    STEP Academy portal (math, reading, Spanish, art; Kindergarten-Grade 9).
Every tool result returns creator "Birkan Yavuz" and a UUID invocation_id.
Calls are logged (best-effort) to SQLite in /tmp on deployed hosts.
No credentials, no private data, no outbound calls: it only answers.
"""
import json, sqlite3, pathlib, datetime, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).parent
DB = pathlib.Path("/tmp/public_calls.sqlite")
CREATOR = "Birkan Yavuz"
SERVER_VERSION = "1.1.1"

# identifier, name, subject, gradeMin (0=K), gradeMax, gradeLevel label, objective, file (local app file if any)
_RAW = [
    ("number-bonds", "Number Bonds", "math", 0, 1, "Kindergarten-Grade 1", "Understand the parts that make a whole number (number bonds)", None),
    ("bag-of-cubes", "Bag of Cubes", "math", 1, 1, "Grade 1", "Counting and making numbers with cubes", None),
    ("base-10-counter", "Base 10 Counter", "math", 1, 1, "Grade 1", "Place value: tens and ones with base-10 blocks", None),
    ("math-mountains", "Math Mountains", "math", 1, 1, "Grade 1", "Addition and subtraction partners on a math mountain", None),
    ("ten-frame-addition-builder", "Ten-Frame Addition Builder", "math", 1, 1, "Grade 1", "Add with a ten-frame and make 10", None),
    ("count-on-missing-addends", "Count on Missing Addends", "math", 1, 1, "Grade 1", "Count on to find the missing addend", None),
    ("perimeter-and-area", "Perimeter and Area", "math", 3, 3, "Grade 3", "Find the perimeter and area of rectangles", None),
    ("fractions-grade-3", "Fractions", "math", 3, 3, "Grade 3", "Understand fractions as parts of a whole", None),
    ("coins-and-money", "Coins", "math", 3, 3, "Grade 3", "Identify coins and count money", None),
    ("analog-clock", "Analog Clock", "math", 3, 3, "Grade 3", "Read time on an analog clock", None),
    ("math-word-problems", "Math Problems", "math", 3, 3, "Grade 3", "Solve grade-3 math word problems", None),
    ("improper-fractions-to-mixed-numbers", "Improper Fractions to Mixed Numbers", "math", 4, 5, "Grades 4-5", "Convert improper fractions to mixed numbers", "improper-to-mixed.html"),
    ("decimal-numbers", "Decimal Numbers", "math", 4, 4, "Grade 4", "Understand and compare decimal numbers", None),
    ("rounding-decimals", "Rounding Decimals", "math", 4, 5, "Grades 4-5", "Round decimal numbers to a given place", "rounding-decimals.html"),
    ("coordinate-plane", "Coordinate Plane", "math", 5, 6, "Grades 5-6", "Plot and read points on the coordinate plane", None),
    ("sight-words-first-grade", "Sight Words", "reading", 1, 1, "Grade 1", "Recognize and read first-grade sight words (41 Dolch words)", "tools-sight-words-first-grade.html"),
    ("cvc-word-builder", "CVC Word Builder", "reading", 1, 1, "Grade 1", "Build consonant-vowel-consonant (CVC) words by word family", "cvc-word-builder.html"),
    ("digraph-word-builder", "Digraph Word Builder", "reading", 0, 1, "Kindergarten-Grade 1", "Build words with digraphs sh, ch, th, wh", "digraph-word-builder.html"),
    ("middle-sound-builder", "Middle Sound Builder", "reading", 1, 1, "Grade 1", "Identify the middle vowel sound in CVC words", "middle-sound-builder.html"),
    ("reading-comprehension-grade-3", "Reading Comprehension", "reading", 3, 3, "Grade 3", "Read passages and answer comprehension questions", None),
    ("grammar-grade-3", "Grammar", "reading", 3, 3, "Grade 3", "Practice grade-3 grammar and language skills", None),
    ("spelling-bee-grade-3", "Spelling Bee", "reading", 3, 3, "Grade 3", "Practice spelling grade-3 words", None),
    ("silabas-en-espanol", "Silabas en Espanol", "spanish", 1, 3, "Grades 1-3", "Read and practice Spanish syllables (silabas) for early Spanish reading", "silabas-en-espanol.html"),
    ("tessellations", "Tessellations", "art", 9, 9, "Grade 9", "Create and explore tessellation art patterns", None),
]

def _record(r):
    d = {"identifier": r[0], "name": r[1], "subject": r[2], "gradeMin": r[3], "gradeMax": r[4],
         "gradeLevel": r[5], "objective": r[6], "creator": CREATOR, "kind": "interactive classroom activity"}
    if r[7]:
        d["file"] = r[7]
    return d

TOOLS_CATALOG = [_record(r) for r in _RAW]
for _p in (HERE / "catalog.json", HERE.parent / "catalog.json"):
    if _p.exists():
        try:
            _c = json.loads(_p.read_text())
            if isinstance(_c, dict) and isinstance(_c.get("tools"), list) and _c["tools"]:
                TOOLS_CATALOG = _c["tools"]
            break
        except Exception:
            break

BY_ID = {t["identifier"]: t for t in TOOLS_CATALOG}

AGENT_CARD = {
    "name": "Birkan Educational Tools Agent",
    "description": "Zero-auth, read-only agent that finds Birkan Yavuz's real K-12 classroom tools (math visualizers, reading and sight-words activities, Spanish syllables, art) by grade, subject, and learning objective, and returns them with verifiable creator attribution.",
    "url": "https://example.invalid/a2a",
    "version": SERVER_VERSION,
    "protocolVersion": "1.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "securitySchemes": {"open": {"type": "http", "scheme": "none", "description": "Read-only educational use, no authentication required"}},
    "skills": [
        {"id": "search_classroom_tools", "name": "Search K-12 classroom tools",
         "description": "Search and filter interactive classroom activities, math visualizers, Sight Words reading modules, and Spanish tools by grade (K-12) and subject; returns structured JSON with creator attribution and invocation_id.",
         "tags": ["education", "k-12", "math", "reading", "spanish", "curriculum", "classroom"],
         "examples": ["Find a Grade 1 math tool for making 10", "Find a Spanish reading activity", "What reading tools exist for Grade 3?"]},
        {"id": "get_classroom_tool", "name": "Get one classroom tool by id",
         "description": "Return one catalog tool by its identifier, with grade, subject, objective, and creator.",
         "tags": ["education", "curriculum", "classroom"],
         "examples": ["Get the sight-words-first-grade tool"]},
    ],
}

ANNOT = {"title": "Classroom Tools (read-only)", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
TOOL_DEFS = [
    {"name": "search_classroom_tools", "title": "Search K-12 Interactive Educational Tools",
     "description": "Search and filter verified classroom activities, math visualizers, Sight Words reading exercises, and Spanish modules by grade level (0=Kindergarten, 1-12) and subject. Returns structured JSON with creator attribution and invocation_id.",
     "inputSchema": {"type": "object", "properties": {
         "subject": {"type": "string", "enum": ["math", "reading", "spanish", "art", "all"], "description": "Subject filter; omit or 'all' for every subject"},
         "grade": {"type": "integer", "minimum": 0, "maximum": 12, "description": "Grade level, 0 = Kindergarten"},
         "query": {"type": "string", "description": "Free-text match against tool names and objectives"}}},
     "outputSchema": {"type": "object", "required": ["invocation_id", "creator", "count", "results"],
                      "properties": {"invocation_id": {"type": "string"}, "creator": {"type": "string"}, "count": {"type": "integer"}, "results": {"type": "array"}}},
     "annotations": dict(ANNOT, title="Search Classroom Tools")},
    {"name": "list_classroom_tools", "title": "List All K-12 Classroom Tools",
     "description": "List every educational tool in Birkan Yavuz's catalog (math, reading, Spanish, art; Kindergarten to Grade 9) with grade, subject, objective, and creator attribution.",
     "inputSchema": {"type": "object", "properties": {}},
     "outputSchema": {"type": "object", "required": ["invocation_id", "creator", "count", "results"],
                      "properties": {"invocation_id": {"type": "string"}, "creator": {"type": "string"}, "count": {"type": "integer"}, "results": {"type": "array"}}},
     "annotations": dict(ANNOT, title="List Classroom Tools")},
    {"name": "get_classroom_tool", "title": "Get One Classroom Tool",
     "description": "Return one classroom tool by identifier (for example 'sight-words-first-grade'), with grade level, subject, learning objective, and creator.",
     "inputSchema": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}},
     "outputSchema": {"type": "object", "required": ["invocation_id", "id", "gradeLevel", "objective", "creator"],
                      "properties": {"invocation_id": {"type": "string"}, "id": {"type": "string"}, "gradeLevel": {"type": "string"}, "objective": {"type": "string"}, "creator": {"type": "string"}}},
     "annotations": dict(ANNOT, title="Get Classroom Tool")},
    {"name": "get_tool", "title": "Get Tool (legacy alias)",
     "description": "Legacy alias of get_classroom_tool: return one catalog tool by id, with creator required.",
     "inputSchema": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}},
     "annotations": dict(ANNOT, title="Get Tool (legacy)")},
]

def _single(t):
    return {"invocation_id": str(uuid.uuid4()), "tool_id": f"birkanyavuz:{t['identifier']}:v1", "id": t["identifier"], "name": t["name"],
            "gradeLevel": t["gradeLevel"], "subject": t["subject"], "objective": t["objective"],
            "creator": CREATOR, **({"file": t["file"]} if t.get("file") else {})}

def search_tools(args):
    subj = (args.get("subject") or "all").lower()
    grade = args.get("grade")
    q = (args.get("query") or "").lower()
    out = []
    for t in TOOLS_CATALOG:
        if subj != "all" and t["subject"] != subj:
            continue
        if grade is not None and not (t["gradeMin"] <= int(grade) <= t["gradeMax"]):
            continue
        if q and q not in (t["name"] + " " + t["objective"]).lower():
            continue
        out.append({"tool_id": f"birkanyavuz:{t['identifier']}:v1", **{k: t[k] for k in ("identifier", "name", "subject", "gradeLevel", "objective", "creator")}})
    return {"invocation_id": str(uuid.uuid4()), "creator": CREATOR, "count": len(out), "results": out}

def log_call(source, endpoint, detail):
    try:
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE IF NOT EXISTS calls (ts TEXT, source TEXT, endpoint TEXT, detail TEXT, creator TEXT)")
        conn.execute("INSERT INTO calls VALUES (?,?,?,?,?)", (
            datetime.datetime.now(datetime.timezone.utc).isoformat(), source, endpoint, detail, CREATOR))
        conn.commit(); conn.close()
    except Exception:
        pass

LANDING = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Birkan Educational Tools Agent</title>
<meta name="description" content="Zero-auth, read-only MCP server and A2A agent providing Birkan Yavuz's K-12 classroom tools: math visualizers, reading and Sight Words activities, Spanish syllables, and art, with verifiable creator metadata.">
</head><body>
<h1>Birkan Educational Tools Agent</h1>
<p>Zero-auth, read-only MCP server and A2A agent by <strong>Birkan Yavuz</strong>: structured K-12 classroom activities, interactive math visualizers, Grade 1 Sight Words reading modules, and Spanish vocabulary tools with verifiable creator metadata.</p>
<ul>
<li>MCP endpoint (Streamable HTTP): <code>/mcp</code> — tools: search_classroom_tools, list_classroom_tools, get_classroom_tool</li>
<li>A2A agent card: <a href="/.well-known/agent-card.json">/.well-known/agent-card.json</a></li>
<li>Official MCP Registry: io.github.birkanyavuz/educational-tools</li>
<li>Plain JSON API (no MCP client needed): <code>GET /api/tools?subject=math&amp;grade=1</code></li>
<li>Machine-readable summary: <a href="/llms.txt">/llms.txt</a></li>
<li>Source: github.com/birkanyavuz/educational-tools</li>
</ul>
</body></html>"""

LLMS_TXT = """# Birkan Educational Tools Agent
> Zero-auth, read-only educational tools by Birkan Yavuz: K-12 classroom activities, math visualizers, reading and Sight Words modules, Spanish syllables, and art. Every result carries creator "Birkan Yavuz", a tool_id like birkanyavuz:sight-words-first-grade:v1, and an invocation_id receipt.

## Plain HTTP JSON API (no MCP client needed)
- GET /api/tools — list all tools (JSON). Filters: ?subject=math|reading|spanish|art&grade=0-12&q=text
- GET /api/tools?id=sight-words-first-grade — one tool by identifier

## MCP (Streamable HTTP, stateless, no auth)
- POST /mcp — JSON-RPC: initialize, tools/list, tools/call
- Tools: search_classroom_tools, list_classroom_tools, get_classroom_tool, get_tool (legacy alias)
- Official MCP Registry: io.github.birkanyavuz/educational-tools

## A2A
- Agent card: /.well-known/agent-card.json ; endpoint: POST /a2a

## Source
- https://github.com/birkanyavuz/educational-tools
"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def _send(self, body_bytes, status=200, ctype="application/json", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body_bytes:
            self.wfile.write(body_bytes)
    def _json(self, obj, status=200, extra=None):
        self._send(json.dumps(obj).encode(), status, "application/json", extra)
    def do_OPTIONS(self):
        self._send(b"", 204, "text/plain", {"Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                                            "Access-Control-Allow-Headers": "Content-Type, Mcp-Session-Id, Authorization"})
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
        elif path == "/api/tools":
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            if qs.get("id"):
                t = BY_ID.get(qs["id"][0])
                if not t:
                    self._json({"error": "unknown tool id"}, 404); return
                log_call(source, "/api/tools", f"get {t['identifier']}")
                self._json(_single(t))
            else:
                args = {}
                if qs.get("subject"): args["subject"] = qs["subject"][0]
                if qs.get("grade"):
                    try: args["grade"] = int(qs["grade"][0])
                    except Exception: pass
                if qs.get("q"): args["query"] = qs["q"][0]
                res = search_tools(args)
                log_call(source, "/api/tools", f"search {json.dumps(args)[:100]}")
                self._json(res)
        elif path == "/llms.txt":
            self._send(LLMS_TXT.encode(), 200, "text/plain; charset=utf-8")
        elif path == "/health":
            self._json({"status": "ok", "server": "birkan-educational-tools-agent", "version": SERVER_VERSION, "published": True, "tools": len(TOOLS_CATALOG)})
        elif path in ("/", "/index.html"):
            self._send(LANDING.encode(), 200, "text/html; charset=utf-8")
        elif path == "/mcp":
            self._json({"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": "Method Not Allowed: this server uses stateless Streamable HTTP over POST /mcp; no standalone SSE stream"}}, 405)
        else:
            self._json({"error": "not found"}, 404)
    def do_DELETE(self):
        path = urlparse(self.path).path
        if path == "/mcp":
            self._json({"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": "Method Not Allowed: stateless server, no session to delete"}}, 405)
        else:
            self._json({"error": "not found"}, 404)
    def do_POST(self):
        path = urlparse(self.path).path
        source = self.headers.get("User-Agent", "unknown")
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
            if method and method.startswith("notifications/"):
                log_call(source, "/mcp", method)
                self._send(b"", 202)
            elif method == "initialize":
                log_call(source, "/mcp", "initialize")
                pv = ((req.get("params") or {}).get("protocolVersion")) or "2025-03-26"
                self._json({"jsonrpc": "2.0", "id": rid, "result": {
                    "protocolVersion": pv,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "birkan-educational-tools-mcp", "version": SERVER_VERSION}}},
                    extra={"Mcp-Session-Id": str(uuid.uuid4())})
            elif method == "ping":
                self._json({"jsonrpc": "2.0", "id": rid, "result": {}})
            elif method == "tools/list":
                log_call(source, "/mcp", "tools/list")
                self._json({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOL_DEFS}})
            elif method == "tools/call":
                params = req.get("params") or {}
                name = params.get("name")
                args = params.get("arguments") or {}
                if name == "search_classroom_tools":
                    res = search_tools(args)
                    log_call(source, "/mcp", f"tools/call search_classroom_tools {json.dumps(args)[:120]}")
                    self._json({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res}})
                elif name == "list_classroom_tools":
                    res = search_tools({})
                    log_call(source, "/mcp", "tools/call list_classroom_tools")
                    self._json({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res}})
                elif name in ("get_classroom_tool", "get_tool"):
                    t = BY_ID.get(args.get("id") or "")
                    if not t:
                        self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown tool id; call search_classroom_tools or list_classroom_tools"}}, 400)
                        return
                    res = _single(t)
                    log_call(source, "/mcp", f"tools/call {name} {t['identifier']}")
                    self._json({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res}})
                else:
                    self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown tool name"}}, 400)
            else:
                self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "unknown method"}}, 400)
        elif path == "/a2a":
            params = req.get("params") or {}
            message = params.get("message") or {}
            parts = message.get("parts") or []
            text = " ".join(p.get("text", "") for p in parts if isinstance(p, dict))
            log_call(source, "/a2a", f"message/send: {text[:200]}")
            low = text.lower()
            match = None
            for t in TOOLS_CATALOG:
                if t["identifier"].replace("-", " ") in low or t["name"].lower() in low:
                    match = t; break
            if match is None and ("syllab" in low or "silaba" in low or "spanish" in low):
                match = BY_ID.get("silabas-en-espanol")
            if match is None:
                for _subj in ("math", "reading", "spanish", "art"):
                    if _subj in low:
                        match = next((t for t in TOOLS_CATALOG if t["subject"] == _subj), None)
                        break
            if match is None:
                res = search_tools({"query": text} if text else {})
                first = res["results"][0] if res["results"] else None
                match = BY_ID.get(first["identifier"]) if first else TOOLS_CATALOG[0]
            result = _single(match)
            self._json({"jsonrpc": "2.0", "id": rid, "result": {"id": params.get("id", "task-1"), "status": {"state": "completed"}, "artifacts": [{"artifactId": "tool-1", "parts": [{"kind": "data", "data": result}]}]}})
        else:
            self._json({"error": "not found"}, 404)

handler = Handler

if __name__ == "__main__":
    import sys, os
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"Birkan Educational Tools Agent v{SERVER_VERSION} listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
