# get_word_list — example prompt → output pairs (SHIPPED in v1.5.0, Nov 4, 2026)

These pairs are in the repo README and the Hugging Face dataset card.
Verified against the live v1.5.0 server. They show the one-shot shape:
topic/level/count in, the words out in a single call. All outputs verified
against the local staged build (server_v2.py, port test); creator is
Birkan Yavuz in every result, with an invocation_id receipt.

## Example 1 — "Give me 10 grade-1 sight words"
Call: get_word_list(topic="sight words", level="grade-1", count=10)
Output: dataset birkanyavuz:dolch-sight-words-220:v1, item_count 10,
total_count 41, items start: after, again, an, any, as, ask, ...

## Example 2 — "Give me the CVC -at family words"
Call: get_word_list(topic="CVC", level="-at")
Output: dataset birkanyavuz:cvc-word-families-75:v1, item_count 8,
total_count 8, items start: bat, cat, fat, hat, mat, pat, ...

## Example 3 — "Give me 20 Spanish syllables"
Call: get_word_list(topic="Spanish syllables", count=20)
Output: dataset birkanyavuz:spanish-syllables-core:v1, item_count 20,
total_count 212, items start: ma, me, mi, mo, mu, pa, ...

## Example 4 — offset, the next batch (v1.6.1)
Call: get_word_list(topic="sight words", level="grade-1", count=10, offset=10)
Output: dataset birkanyavuz:dolch-sight-words-220:v1, item_count 10,
total_count 41, offset 10, has_more true, items: from, give, going, had, has,
her, him, his, how, just. No overlap with Example 1.
Call with offset=41 (past the end): item_count 0, items [], has_more false,
note "offset is past the end of the list; no more items" — a normal result,
never an error.

## Example 5 — carrier phrases on grade-1 sight words (v1.6.2)
Call: get_word_list(topic="sight words", level="grade-1", count=3)
Output: dataset birkanyavuz:dolch-sight-words-220:v1, item_count 3,
total_count 41, items: after, again, an (plain strings, unchanged), plus
carrier_phrases: {"after": "Run after the cat.", "again": "We can hop
again.", "an": "I see an egg."} — one short phrase per word, 3–5 words,
decodable except the target word. All 41 grade-1 words carry one; other
levels and datasets return no carrier_phrases field.

## Error behavior (no partial results)
- Unknown topic (e.g. "quantum physics") → error -32602 with the topic list.
- count 0 or non-integer → error -32602 (count must be a positive integer).
- offset negative or non-integer → error -32602 (offset must be a non-negative integer).
- A level foreign to the matched dataset → error -32602.
- Unknown dataset_id for get_curriculum_dataset → error -32602 that lists the valid dataset ids.

## Ship checklist (next round — do not skip)
- Port get_word_list (tool def, handler, agent-card skill) from server_v2.py
  to public_server.py, api/index.py (repo root), stdio_server.py, and the
  npm bridge if it mirrors tools; bump SERVER_VERSION; update server.json,
  README examples, llms.txt, and the HF dataset card with the pairs above.
- Push → verify Vercel live (tools/list shows 5) → registry republish →
  Glama release. Live/registry/Glama must all agree before reporting it shipped.
