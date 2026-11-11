#!/usr/bin/env python3
"""
Test every MCP tool by name via tools/call, the way a real outside client would.

M8ven's audit (Nov 9, 2026) found 0/5 tools referenced in tests: the repo's only
test file called tools/call once, with the legacy alias "get_tool". This file
calls each of the five real tools by name and checks a real result, creator
attribution, and an invocation receipt on every call.

Run locally:  python3 test_tools_call.py   (starts public_server.py on port 8132)
It proves the code works. It does NOT prove external contact — these calls come
from localhost. External proof only exists after deployment, when outside
callers hit the public URL.
"""
import json, subprocess, sys, time, urllib.request, urllib.error, pathlib

HERE = pathlib.Path(__file__).parent
PORT = 8132
BASE = f"http://127.0.0.1:{PORT}"

TOOLS = ["search_classroom_tools", "list_classroom_tools", "get_classroom_tool",
         "get_curriculum_dataset", "get_word_list"]

def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=10))
    except urllib.error.HTTPError as e:
        return json.load(e)

def get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=10))

def call(name, args):
    r = post("/mcp", {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                      "params": {"name": name, "arguments": args}})
    assert "result" in r, r
    sc = r["result"]["structuredContent"]
    p = json.loads(sc) if isinstance(sc, str) else sc
    assert p.get("creator") == "Birkan Yavuz", (name, p)
    assert p.get("invocation_id"), (name, p)
    return p

def main():
    proc = subprocess.Popen([sys.executable, str(HERE / "public_server.py"), str(PORT)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        for _ in range(50):
            try:
                h = get("/health")
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise RuntimeError("server did not start")
        print("health:", h["version"], h["status"], "tools:", h["tools"])

        init = post("/mcp", {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                             "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                        "clientInfo": {"name": "test_tools_call", "version": "1"}}})
        assert init["result"]["serverInfo"]["version"] == h["version"]
        print("initialize OK:", h["version"])

        lst = post("/mcp", {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}})
        names = [t["name"] for t in lst["result"]["tools"]]
        assert names == TOOLS, names
        print("tools/list: all 5 tools present, in order")

        p = call("search_classroom_tools", {"subject": "math"})
        assert p["count"] > 0 and p["results"], p
        print("search_classroom_tools {subject: math} ->", p["count"], "tools OK")

        p = call("list_classroom_tools", {})
        assert p["count"] == 42 and len(p["results"]) == 42, p
        print("list_classroom_tools -> 42 tools OK")

        p = call("get_classroom_tool", {"id": "sight-words-first-grade"})
        assert p["id"] == "sight-words-first-grade", p
        print("get_classroom_tool sight-words-first-grade OK")

        p = call("get_curriculum_dataset", {"dataset_id": "dolch-nouns-94"})
        assert p["item_count"] == 94 and p["items"][:3] == ["apple", "baby", "back"], p
        print("get_curriculum_dataset dolch-nouns-94 -> 94 items OK")

        p = call("get_word_list", {"topic": "Dolch nouns", "count": 3})
        assert p["items"] == ["apple", "baby", "back"] and p["total_count"] == 94, p
        print("get_word_list 'Dolch nouns' count 3 -> apple, baby, back OK")

        print("ALL 5 TOOLS CALLED BY NAME — PASS")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    main()
