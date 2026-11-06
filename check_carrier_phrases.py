#!/usr/bin/env python3
"""Check Dolch grade-1 carrier phrases against Argon's Nov 5 design rule:
3-5 words, 100% decodable except the target word, built only from
vocabulary the learner already has.

Allowed non-target words (all from this project's own published lists):
- Dolch pre-primer + primer sight words (learned by sight already)
- CVC word families (75 words, decodable)
- Dolch nouns that are phonetically regular with a single short vowel
  and no silent letters: CVC-shaped plus a hand-approved CVCC set
  (back, ball, bell, duck, fish [sh is in our digraph set], hand,
  hill, milk, nest, wind). 'fish' is allowed because sh is taught
  in our digraph-words-21 set.
Target word itself is exempt (it is the word being learned).
Also: phrase must contain the target word exactly once, and end with
a period or question mark.
"""
import json, re, sys, pathlib

HERE = pathlib.Path(__file__).parent
DS = json.loads((HERE / "datasets.json").read_text())
PHRASES = json.loads((HERE / "dolch-grade1-carrier-phrases.json").read_text())

sw = DS["dolch-sight-words-220"]["levels"]
pre_primer = set(sw["pre-primer"])
primer = set(sw["primer"])
cvc = {w for fam in DS["cvc-word-families-75"]["levels"].values() for w in fam}
nouns = set(DS["dolch-nouns-94"]["levels"]["all"])

# regular single-short-vowel nouns, explicit set (no regex guessing):
# CVC-shaped Dolch nouns, plus a hand-approved few whose spelling a
# grade-1 reader can sound out: back/duck (ck), ball (the primer word
# 'all' teaches -all), bell (ll), fish (sh is in our digraph set),
# hand/hill/milk/nest (short vowel + one final consonant cluster).
regular_nouns = {w for w in nouns
                 if re.fullmatch(r"[bcdfghjklmnpqrstvwxz]?[aeiou][bcdfghjklmnpqrstvwxz]{1,2}", w)
                 and not re.search(r"ar|er|ir|or|ur|ow|ou|oi|oy", w)}
regular_nouns |= {"back", "ball", "bell", "duck", "fish", "hand", "hill", "milk", "nest"}

ALLOWED = pre_primer | primer | cvc | regular_nouns
GRADE1 = sw["grade-1"]

errors = []
if set(PHRASES) != set(GRADE1):
    errors.append(f"phrase keys != grade-1 words: missing={set(GRADE1)-set(PHRASES)} extra={set(PHRASES)-set(GRADE1)}")
for word, phrase in sorted(PHRASES.items()):
    toks = re.findall(r"[A-Za-z']+", phrase)
    low = [t.lower() for t in toks]
    if not (3 <= len(toks) <= 5):
        errors.append(f"{word}: {len(toks)} words (want 3-5): {phrase!r}")
    if low.count(word) != 1:
        errors.append(f"{word}: target appears {low.count(word)}x: {phrase!r}")
    for t in low:
        if t == word:
            continue
        if t not in ALLOWED:
            errors.append(f"{word}: non-target word {t!r} not in allowed vocabulary: {phrase!r}")
    if not phrase.endswith((".", "?")):
        errors.append(f"{word}: no sentence-final punctuation: {phrase!r}")

print(f"grade-1 words: {len(GRADE1)}, phrases: {len(PHRASES)}")
print(f"allowed non-target vocabulary: {len(ALLOWED)} words "
      f"(pre-primer {len(pre_primer)} + primer {len(primer)} + CVC {len(cvc)} + regular nouns {len(regular_nouns)})")
print(f"regular nouns used as allowed: {sorted(regular_nouns)}")
if errors:
    print(f"FAIL ({len(errors)} problems):")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("PASS: all 41 carrier phrases meet the rule.")
