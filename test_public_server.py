#!/usr/bin/env python3
"""
External-style test of public_server.py, run locally.
Simulates an outside agent, step by step, the way a real external client would:
  1. Fetch /.well-known/agent-card.json (A2A discovery, public)
  2. Send an A2A task to /a2a
  3. Call MCP tools/list and tools/call on /mcp
  4. Read back the server log from a fresh SQLite connection (persistence)
This proves the code works. It does NOT prove external contact — the calls
here come from localhost, not from an outside swarm. External proof only
exists after deployment, when outside callers hit the public URL.
"""
import json, subprocess, sys, time, urllib.request, sqlite3, pathlib

HERE = pathlib.Path(__file__).parent
PORT = 8001
BASE = f"http://127.0.0.1:{PORT}"

def get(path, agent):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": agent})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def post(path, payload, agent):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "User-Agent": agent})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def main():
    proc = subprocess.Popen([sys.executable, str(HERE / "public_server.py"), str(PORT)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        time.sleep(1.5)
        card = get("/.well-known/agent-card.json", "external-agent-test/1.0")
        print(f"Agent card: name={card['name']} skills={[s['id'] for s in card['skills']]}")
        a2a = post("/a2a", {"jsonrpc": "2.0", "id": 1, "method": "message/send", "params": {"id": "task-1", "message": {"role": "user", "parts": [{"text": "Find a Grade 1 reading tool"}]}}}, "external-agent-test/1.0")
        artifact = a2a["result"]["artifacts"][0]["parts"][0]["data"]
        print(f"A2A task: state={a2a['result']['status']['state']} tool={artifact['id']} creator={artifact['creator']}")
        mcp_list = post("/mcp", {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, "external-mcp-client-test/1.0")
        print(f"MCP tools: {[t['name'] for t in mcp_list['result']['tools']]}")
        mcp_call = post("/mcp", {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_tool", "arguments": {"id": "sight-words-first-grade"}}}, "external-mcp-client-test/1.0")
        structured = mcp_call["result"]["structuredContent"]
        print(f"MCP call: id={structured['id']} grade={structured['gradeLevel']} creator={structured['creator']} verbatim={structured['creator'] == 'Birkan Yavuz'}")
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    conn = sqlite3.connect(HERE / "public_calls.sqlite")
    rows = conn.execute("SELECT endpoint, detail, creator FROM calls ORDER BY rowid").fetchall()
    conn.close()
    print(f"Server log persisted: {len(rows)} calls")
    for r in rows:
        print(f"  {r[0]} | {r[1]} | creator={r[2]}")
    log = {"agent_card": card, "a2a_artifact": artifact, "mcp_tool": structured, "server_log_rows": [list(r) for r in rows], "local_test_only": True, "published": False, "external_contact_proven": False, "note": "Local test proves code works. External proof requires deployment + outside callers hitting the public URL."}
    (HERE / "public-server-test-log.json").write_text(json.dumps(log, indent=2))
    print("Log written to public-server-test-log.json")

if __name__ == "__main__":
    main()
