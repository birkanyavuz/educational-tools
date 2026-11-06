#!/usr/bin/env python3
"""
Birkan Educational Tools — stdio MCP transport.

Same tools and datasets as the hosted HTTP server (public_server.py), spoken
over stdin/stdout JSON-RPC for stdio hosts and directory build checks
(e.g. Glama releases). Prints nothing except JSON-RPC responses.
Creator: Birkan Yavuz. License: CC-BY-4.0.
"""
import sys, json

from public_server import (DATASETS, TOOL_DEFS, BY_ID, CREATOR, SERVER_VERSION,
                           dataset_payload, search_tools, _single, get_word_list_payload)

INSTRUCTIONS = ("Free, read-only, no-auth K-12 classroom tools and real curriculum datasets by Birkan Yavuz: "
                "Dolch sight words by level, CVC word families, digraph words, Spanish syllables, Turkish-English flashcards (animals, colors, objects), Turkish-English "
                "early words, plus 24 interactive math/reading/Spanish classroom tools with Common Core standard codes. "
                "Use search_classroom_tools to find interactive tools, get_curriculum_dataset for word lists, get_word_list for a one-call word list by topic, and "
                "resources/list to pin datasets into a workspace.")


def handle(req):
    """Return a JSON-RPC response dict, or None for notifications."""
    if not isinstance(req, dict):
        return None
    method = req.get("method") or ""
    rid = req.get("id")
    if method.startswith("notifications/"):
        return None
    params = req.get("params") or {}

    if method == "initialize":
        pv = params.get("protocolVersion") or "2025-03-26"
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": pv,
            "capabilities": {"tools": {"listChanged": False},
                             "resources": {"subscribe": False, "listChanged": False}},
            "serverInfo": {"name": "birkan-educational-tools-mcp", "version": SERVER_VERSION},
            "instructions": INSTRUCTIONS}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOL_DEFS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "search_classroom_tools":
            res = search_tools(args)
        elif name == "list_classroom_tools":
            res = search_tools({})
        elif name == "get_curriculum_dataset":
            ds_id = args.get("dataset_id") or ""
            if ds_id not in DATASETS:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown dataset_id; datasets: dolch-sight-words-220, dolch-nouns-94, cvc-word-families-75, digraph-words-21, spanish-syllables-core, turkish-english-early-words, turkish-english-animals, turkish-english-colors, turkish-english-objects"}}
            res = dataset_payload(ds_id, args.get("level_or_family") or None)
            if res is None:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown level_or_family for this dataset"}}
        elif name == "get_word_list":
            topic = args.get("topic") or ""
            count = args.get("count")
            if count is not None and (not isinstance(count, int) or isinstance(count, bool) or count <= 0):
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "count must be a positive integer"}}
            offset = args.get("offset", 0)
            if offset is None:
                offset = 0
            if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "offset must be a non-negative integer"}}
            res = get_word_list_payload(topic, args.get("level") or None, count, offset)
            if res is None:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown topic or level; topics: sight words, Dolch nouns, CVC, digraph, Spanish syllables, animals, colors, objects, Turkish early words"}}
        elif name in ("get_classroom_tool", "get_tool"):
            t = BY_ID.get(args.get("id") or "")
            if not t:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown tool id; call search_classroom_tools or list_classroom_tools"}}
            res = _single(t)
        else:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown tool name"}}
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res}}
    if method == "resources/list":
        res_list = [{"uri": f"edu://birkanyavuz/datasets/{k}", "name": v["title"], "mimeType": "application/json",
                     "description": f"Curriculum dataset by Birkan Yavuz: {v['title']}. License CC-BY-4.0."}
                    for k, v in DATASETS.items()]
        return {"jsonrpc": "2.0", "id": rid, "result": {"resources": res_list}}
    if method == "resources/templates/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"resourceTemplates": [
            {"uriTemplate": "edu://birkanyavuz/datasets/{dataset_id}", "name": "Curriculum Dataset",
             "mimeType": "application/json",
             "description": "A complete curriculum dataset by Birkan Yavuz (Dolch words, CVC families, digraphs, Spanish syllables, Turkish-English words)."}]}}
    if method == "resources/read":
        uri = params.get("uri") or ""
        ds_id = uri.rsplit("/", 1)[-1] if uri.startswith("edu://birkanyavuz/datasets/") else ""
        if ds_id not in DATASETS:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown resource uri"}}
        res = dataset_payload(ds_id)
        return {"jsonrpc": "2.0", "id": rid, "result": {"contents": [
            {"uri": uri, "mimeType": "application/json", "text": json.dumps(res)}]}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "unknown method"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        resp = handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
