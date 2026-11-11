#!/usr/bin/env python3
"""
Test the MCP Resources surface (v1.8.0): the 9 dataset resources plus the 42
classroom app files at edu://apps/<tool-id>, served verbatim.

Run locally:  python3 test_resources.py   (starts public_server.py on port 8133)
It proves the code works. It does NOT prove external contact — these calls
come from localhost. External proof only exists after deployment, when outside
callers hit the public URL.
"""
import hashlib, json, pathlib, subprocess, sys, time, urllib.request, urllib.error

HERE = pathlib.Path(__file__).parent
PORT = 8133
BASE = f"http://127.0.0.1:{PORT}"

def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=10))
    except urllib.error.HTTPError as e:
        return json.load(e)

def get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=10))

def get_raw(path):
    return urllib.request.urlopen(BASE + path, timeout=10).read()

def rpc(method, params=None, rid=1):
    return post("/mcp", {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})

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
        print("health:", h["version"], h["status"], "tools:", h["tools"], "app_resources:", h["app_resources"])
        assert h["app_resources"] == 42, h

        lst = rpc("resources/list", {}, rid=2)
        resources = lst["result"]["resources"]
        print("resources/list:", len(resources), "resources")
        assert len(resources) == 51, len(resources)  # 9 datasets + 42 apps
        by_uri = {r["uri"]: r for r in resources}
        assert len([u for u in by_uri if u.startswith("edu://birkanyavuz/datasets/")]) == 9
        app_uris = [u for u in by_uri if u.startswith("edu://apps/")]
        assert len(app_uris) == 42, len(app_uris)
        # the five hub-description entries have no app resource
        for generic in ("coins-and-money", "fractions-grade-3", "math-word-problems",
                        "decimal-numbers", "grammar-grade-3"):
            assert f"edu://apps/{generic}" not in by_uri, generic
        # cut science apps are not served either
        for cut in ("projectile-cannon-simulator", "molecule-builder", "food-chain"):
            assert f"edu://apps/{cut}" not in by_uri, cut
        nw = by_uri["edu://apps/nonsense-words"]
        assert nw["mimeType"] == "text/html", nw
        assert nw["_meta"]["creator"] == "Birkan Yavuz", nw
        assert nw["_meta"]["subject"] == "reading" and nw["_meta"]["gradeMin"] == 1, nw
        local = (HERE / "apps" / "nonsense-words.html").read_bytes()
        assert nw["_meta"]["byte_size"] == len(local), nw
        assert nw["_meta"]["content_sha256"] == hashlib.sha256(local).hexdigest(), nw
        print("resources/list: 9 datasets + 42 apps, generics and cut apps absent, _meta hash matches file")

        templates = rpc("resources/templates/list", {}, rid=3)
        tmpls = templates["result"]["resourceTemplates"]
        assert any(t["uriTemplate"] == "edu://apps/{tool_id}" for t in tmpls), tmpls
        assert any(t["uriTemplate"] == "edu://birkanyavuz/datasets/{dataset_id}" for t in tmpls), tmpls
        print("resources/templates/list: datasets + apps templates OK")

        # resources/read: an app file, verbatim
        read = rpc("resources/read", {"uri": "edu://apps/nonsense-words"}, rid=4)
        contents = read["result"]["contents"]
        assert len(contents) == 1 and contents[0]["mimeType"] == "text/html", read
        assert contents[0]["text"] == local.decode("utf-8"), "read text must equal the file exactly"
        assert "Nonsense Words" in contents[0]["text"]
        print("resources/read edu://apps/nonsense-words: verbatim file OK")

        # resources/read: a dataset still works
        read_ds = rpc("resources/read", {"uri": "edu://birkanyavuz/datasets/dolch-nouns-94"}, rid=5)
        payload = json.loads(read_ds["result"]["contents"][0]["text"])
        assert payload["item_count"] == 94 and payload["creator"] == "Birkan Yavuz", payload
        print("resources/read dataset dolch-nouns-94: still OK")

        # resources/read: unknown app uri -> -32602, no partial results
        bad = rpc("resources/read", {"uri": "edu://apps/no-such-app"}, rid=6)
        assert bad["error"]["code"] == -32602, bad
        print("resources/read unknown app uri -> -32602 OK")

        # plain-HTTP mirror: /api/apps list + single file
        listing = get("/api/apps")
        assert listing["count"] == 42 and len(listing["apps"]) == 42, listing
        raw = get_raw("/api/apps?id=cvc-word-builder")
        assert raw == (HERE / "apps" / "cvc-word-builder.html").read_bytes(), "api/apps file mismatch"
        print("GET /api/apps: list 42 + single file verbatim OK")

        # tools/list unchanged: still 5 tools
        tools = rpc("tools/list", {}, rid=7)
        assert [t["name"] for t in tools["result"]["tools"]] == [
            "search_classroom_tools", "list_classroom_tools", "get_classroom_tool",
            "get_curriculum_dataset", "get_word_list"], tools
        print("tools/list: still 5 tools OK")

        print("ALL RESOURCE CHECKS — PASS")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    main()
