# First Contact Benchmark — hash-locked dataset retrieval tasks

22 deterministic tasks for testing whether an AI agent can actually find and
call a real MCP server. Every task asks the agent to fetch one dataset (or one
level of it) from **io.github.birkanyavuz/educational-tools** by Birkan Yavuz
and report the `item_count` and `content_hash` it received.

## Why it is hash-locked

`content_hash` is the SHA-256 of the full dataset as served live. It appears
nowhere in this repository's task prompts as a derivable value — the only way
to know it is to make a real call to the server (MCP tool
`get_curriculum_dataset`, or `GET https://educational-tools.vercel.app/api/datasets?id=<id>`).
Guessing, hallucinating, or copying another dataset's hash fails the check.

## Run it

1. Give an agent the `prompt` from any line of `tasks.jsonl`, with access to
   the MCP server above (zero-auth, remote: https://educational-tools.vercel.app/mcp).
2. Collect its answers as JSON: `[{"task_id": "fc-01", "content_hash": "...", "item_count": 220}, ...]`
3. Grade: `python3 verify.py answers.json`
4. Sanity check the pack itself: `python3 verify.py --self-test` (expects 22/22).

If the underlying datasets ever change, the expected hashes in `tasks.jsonl`
must be regenerated — the checker compares against the live server as well,
so stale expectations fail loudly instead of passing silently.

Datasets by Birkan Yavuz, CC-BY-4.0.
