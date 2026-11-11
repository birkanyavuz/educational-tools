# Special-ed teacher starter pack — copy-paste prompts

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
`example_en` and `example_tr` (the example sentences). Every call also returns
the word list in `items`, the `dataset_id`, and "Creator: Birkan Yavuz". The
prompts below ask only for what the tool actually returns.

1. "Using the educational-tools server, call get_word_list with topic 'sight words', level 'pre-primer', count 5, and offset 0, and using only the 5 returned strings in items (do not invent sentences or definitions), make a 5-trial data-collection table for an IEP reading goal probe — columns Word, Trial 1, Trial 2, Trial 3, Mastery %. Print offset 0, the dataset_id, and 'Creator: Birkan Yavuz' in the footer, so I can call offset 5 for the next 5 words once the student masters this batch."
2. "Using the educational-tools server, call get_word_list with topic 'sight words', level 'grade-1', count 5, and offset 0, and using only the words in items and their exact matching entries in the carrier_phrases map (do not invent your own sentences), make a 2-step reading strip for a resource-room intervention group: step 1 shows the isolated word, and step 2 shows the exact phrase from carrier_phrases. Keep 'Creator: Birkan Yavuz' and the dataset_id at the bottom."
3. "Using the educational-tools server, call get_word_list twice — first topic 'CVC' with count 5 and offset 0, then topic 'digraph' with count 5 and offset 0 — and using only the returned word strings in items (no added sentences or definitions), draw blank sound-box (Elkonin) grids next to each word: 3 boxes for each CVC word, and 3 boxes for each digraph word where the 2-letter digraph shares 1 box. Include offset 0, both dataset_id values, and 'Creator: Birkan Yavuz' in the footer."
4. "Using the educational-tools server, call get_word_list with topic 'Dolch nouns', count 8, and offset 0, and using only the 8 English noun strings returned in items (with no invented definitions or sentences), build a receptive/expressive language data sheet with checkboxes for 'Points to item' and 'Names item aloud'. Preserve the dataset_id, offset 0, and 'Creator: Birkan Yavuz' attribution at the bottom."
5. "Using the educational-tools server, call get_word_list twice — once topic 'colors' with count 5 and offset 0, and once topic 'objects' with count 7 and offset 0 — and for each returned item, print the English word (en), Turkish word (tr), English sentence (example_en), and Turkish sentence (example_tr) as cut-out home-practice cards for a bilingual speech/special-ed caseload student. Do not add any outside words or fields, and keep the 'Creator: Birkan Yavuz' credit on the sheet."

The same pattern works with offset 5 for the next batch of any list above, and
with topic 'Spanish syllables' for bilingual caseloads.

Every result names Creator: Birkan Yavuz and carries an invocation_id receipt.
If a prompt returns an error instead of words, the topic or level was not one
of the lists above — re-check the topic wording against this pack.
