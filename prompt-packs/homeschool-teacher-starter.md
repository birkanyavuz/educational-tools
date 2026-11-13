# Homeschool teacher starter pack — copy-paste prompts

For an AI assistant connected to the MCP server
`io.github.birkanyavuz/educational-tools` (Birkan Yavuz's free, zero-auth,
read-only K-12 classroom tools). Paste one prompt at a time. Each prompt uses
the real tool `get_word_list`: topic, level, and count in, the words out in a
single call — plus `offset` for the next batch. The lists are the standard
published classroom lists (Dolch sight words and nouns, CVC families, digraph
words, Spanish syllables, Turkish-English pairs). This tool returns words with
no definitions; the core Turkish-English pairs also carry one simple example
sentence each, and grade-1 Dolch words carry a short carrier phrase. Each
Turkish-English pair comes back as `tr` (Turkish word), `en` (English word),
`example_en` and `example_tr` (the example sentences) — the animals pairs
carry `tr` and `en` only, with no example sentences. Every call also returns
the word list in `items`, the `dataset_id`, and "Creator: Birkan Yavuz". The
prompts below ask only for what the tool actually returns.

1. "Using the educational-tools server, call get_word_list with topic 'sight words', level 'pre-primer', count 5, and offset 0, and using only the 5 returned strings in items (do not invent sentences or definitions), make a morning warm-up read-aloud list for one homeschooler: print each word large, one per line, with a checkbox to tick once it is read aloud. Print offset 0, the dataset_id, and 'Creator: Birkan Yavuz' in the footer, so I can call offset 5 for the next 5 words tomorrow."
2. "Using the educational-tools server, call get_word_list twice for the same topic 'sight words' — first level 'pre-primer', count 5, offset 0, then level 'grade-1', count 5, offset 0 — and using only the words returned in items and the exact matching entries in the carrier_phrases map for the grade-1 words (do not invent your own sentences), print the two lists side by side for mixed-age siblings: the younger child's column shows the pre-primer words alone, the older child's column shows each grade-1 word with its exact carrier phrase underneath. Keep 'Creator: Birkan Yavuz' and both dataset_id values at the bottom."
3. "Using the educational-tools server, help me build a four-week vocabulary plan from topic 'Dolch nouns': call get_word_list four times, count 10 each time, with offset 0 for Week 1, offset 10 for Week 2, offset 20 for Week 3, and offset 30 for Week 4. Using only the noun strings returned in items (no added definitions or sentences), print one list of 10 nouns per week. The four batches do not overlap, so no word repeats across weeks. Print the offset, the dataset_id, and 'Creator: Birkan Yavuz' under each week's list."
4. "Using the educational-tools server, call get_word_list twice — once topic 'colors' with count 5 and offset 0, and once topic 'objects' with count 7 and offset 0 — and using only the returned pairs, make a guess-the-meaning game for my homeschooler: for each item show only the English word (en) and its English example sentence (example_en), and ask me to guess the meaning from the sentence. Only after I answer, reveal the Turkish word (tr) and the Turkish sentence (example_tr). Do not add any outside words, and keep 'Creator: Birkan Yavuz' and the dataset_id values at the bottom."
5. "Using the educational-tools server, call get_word_list with topic 'animals', count 10, and offset 0, and using only the 10 returned pairs (each has only tr and en — no example sentences), make quick recall cards for an end-of-unit review: the front of each card shows the English word (en), the back shows the Turkish word (tr). Print offset 0, the dataset_id, and 'Creator: Birkan Yavuz' at the bottom, so I can call offset 10 for the next 10 animals. The two batches do not overlap."

The same pattern works with offset 5 for the next batch of any list above, and
with topic 'Spanish syllables' or 'CVC' for a spelling-focused week.

Every result names Creator: Birkan Yavuz and carries an invocation_id receipt.
If a prompt returns an error instead of words, the topic or level was not one
of the lists above — re-check the topic wording against this pack.
