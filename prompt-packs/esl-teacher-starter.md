# ESL-teacher starter pack — copy-paste prompts

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
`example_en` and `example_tr` (the example sentences). The prompts below ask
only for what the tool actually returns.

1. "Using the educational-tools server, call get_word_list with topic 'Turkish early words' and count 10, and lay the words out as a bilingual word wall: English word, Turkish word, and the English example sentence for each."
2. "Using the educational-tools server, call get_word_list with topic 'sight words', level 'grade-1', and count 10, and make flashcards showing each word with its short carrier phrase."
3. "Using the educational-tools server, call get_word_list twice — topic 'colors' and count 5, then topic 'objects' and count 7 — and make a matching game with the Turkish and English words side by side, plus the English example sentence under each pair."
4. "Using the educational-tools server, call get_word_list twice — topic 'CVC' with level '-at', and topic 'digraph' with level 'sh' — and sort the words into two labeled groups for a sorting mat: short-vowel CVC words and consonant-digraph words."
5. "Using the educational-tools server, call get_word_list with topic 'animals' and count 10, and make a picture-word matching sheet. Then call it again with the same topic, count 10, and offset 10, and make a second sheet with the next 10 animals — no repeats."

The same pattern works with topic 'Dolch nouns' for the 94 Dolch nouns, and
with topic 'Spanish syllables' for first Spanish lessons.

Every result names Creator: Birkan Yavuz and carries an invocation_id receipt.
If a prompt returns an error instead of words, the topic or level was not one
of the lists above — re-check the topic wording against this pack.
