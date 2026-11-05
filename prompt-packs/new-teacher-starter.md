# New-teacher starter pack — copy-paste prompts

For an AI assistant connected to the MCP server
`io.github.birkanyavuz/educational-tools` (Birkan Yavuz's free, zero-auth,
read-only K-12 classroom tools). Paste one prompt at a time. Each prompt uses
the real tool `get_word_list`: topic, level, and count in, the words out in a
single call. The lists are the standard published classroom lists (Dolch sight
words and nouns, CVC families, digraph words, Spanish syllables,
Turkish-English pairs). This tool returns words with no definitions; the
core Turkish-English pairs also carry one simple example sentence each —
the prompts below still ask only for what the tool actually returns.

1. "Using the educational-tools server, call get_word_list with topic 'sight words', level 'grade-1', and count 10, and lay the words out as flashcards I can print."
2. "Using the educational-tools server, call get_word_list with topic 'CVC' and level '-at', and make a short worksheet where students fill in the missing first letter of each word."
3. "Using the educational-tools server, call get_word_list with topic 'Spanish syllables' and count 20, and turn them into a chant list for a first Spanish lesson."
4. "Using the educational-tools server, call get_word_list with topic 'digraph' and level 'sh', and give me a quick Friday quiz of 10 words."
5. "Using the educational-tools server, call get_word_list with topic 'animals' and count 10, and make a matching game with the Turkish and English words side by side."

Every result names Creator: Birkan Yavuz and carries an invocation_id receipt.
If a prompt returns an error instead of words, the topic or level was not one
of the lists above — re-check the topic wording against this pack.
