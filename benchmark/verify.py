#!/usr/bin/env python3
"""Hash-locked checker for the First Contact benchmark pack.

An answer passes only if it reports the live server's current content_hash
for the task's dataset — a value that can only be obtained by actually
calling the server (MCP tool get_curriculum_dataset or GET /api/datasets).

Usage:
  python3 verify.py answers.json     # [{"task_id": "fc-01", "content_hash": "...", "item_count": 220}, ...]
  python3 verify.py --self-test      # grade the expected answers (should be 100%)
"""
import json, sys, urllib.request

BASE = "https://educational-tools.vercel.app"

def live_payload(ds_id, level):
    url = f"{BASE}/api/datasets?id={ds_id}" + (f"&level={level}" if level else "")
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def main():
    tasks = [json.loads(l) for l in open("tasks.jsonl") if l.strip()]
    if "--self-test" in sys.argv:
        answers = {t["task_id"]: {"content_hash": t["expected_content_hash"],
                                  "item_count": t["expected_item_count"]} for t in tasks}
    else:
        raw = json.load(open(sys.argv[1]))
        answers = {a["task_id"]: a for a in raw}
    passed = 0
    for t in tasks:
        live = live_payload(t["dataset_id"], t["level"])
        a = answers.get(t["task_id"], {})
        ok = (a.get("content_hash") == live["content_hash"] == t["expected_content_hash"]
              and a.get("item_count") == live["item_count"] == t["expected_item_count"])
        print(f"{'PASS' if ok else 'FAIL'}  {t['task_id']}  {t['dataset_id']} level={t['level']} items={t['expected_item_count']}")
        passed += ok
    print(f"\n{passed}/{len(tasks)} passed")
    sys.exit(0 if passed == len(tasks) else 1)

if __name__ == "__main__":
    main()
