#!/usr/bin/env python3
"""
Birkan Educational Tools Agent — A2A + remote MCP server, v1.1.0.
Upgraded Oct 29, 2026 following the Argon brainstorm (First Contact chat):
  - Stateless Streamable HTTP MCP: POST /mcp accepts calls with or without
    Mcp-Session-Id (serverless-safe); GET/DELETE /mcp return 405.
  - CORS with Access-Control-Expose-Headers: Mcp-Session-Id for browser
    inspectors (Smithery/Glama playgrounds).
  - Granular, annotated tools instead of one vague get_tool:
    search_classroom_tools, list_classroom_tools, get_classroom_tool,
    plus get_tool kept as a legacy alias. All read-only annotations set.
  - Real catalog depth: Birkan Yavuz's actual classroom apps from his
    STEP Academy portal (math, reading, Spanish, art; Kindergarten-Grade 9).
Every tool result returns creator "Birkan Yavuz" and a UUID invocation_id.
Calls are logged (best-effort) to SQLite in /tmp on deployed hosts.
No credentials, no private data, no outbound calls: it only answers.
"""
import json, sqlite3, pathlib, datetime, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).parent
DB = pathlib.Path("/tmp/public_calls.sqlite")
CREATOR = "Birkan Yavuz"
SERVER_VERSION = "1.3.4"

# identifier, name, subject, gradeMin (0=K), gradeMax, gradeLevel label, objective, file (local app file if any)
_RAW = [
    ("number-bonds", "Number Bonds", "math", 0, 1, "Kindergarten-Grade 1", "Understand the parts that make a whole number (number bonds)", None),
    ("bag-of-cubes", "Bag of Cubes", "math", 1, 1, "Grade 1", "Counting and making numbers with cubes", None),
    ("base-10-counter", "Base 10 Counter", "math", 1, 1, "Grade 1", "Place value: tens and ones with base-10 blocks", None),
    ("math-mountains", "Math Mountains", "math", 1, 1, "Grade 1", "Addition and subtraction partners on a math mountain", None),
    ("ten-frame-addition-builder", "Ten-Frame Addition Builder", "math", 1, 1, "Grade 1", "Add with a ten-frame and make 10", None),
    ("count-on-missing-addends", "Count on Missing Addends", "math", 1, 1, "Grade 1", "Count on to find the missing addend", None),
    ("perimeter-and-area", "Perimeter and Area", "math", 3, 3, "Grade 3", "Find the perimeter and area of rectangles", None),
    ("fractions-grade-3", "Fractions", "math", 3, 3, "Grade 3", "Understand fractions as parts of a whole", None),
    ("coins-and-money", "Coins", "math", 3, 3, "Grade 3", "Identify coins and count money", None),
    ("analog-clock", "Analog Clock", "math", 3, 3, "Grade 3", "Read time on an analog clock", None),
    ("math-word-problems", "Math Problems", "math", 3, 3, "Grade 3", "Solve grade-3 math word problems", None),
    ("improper-fractions-to-mixed-numbers", "Improper Fractions to Mixed Numbers", "math", 4, 5, "Grades 4-5", "Convert improper fractions to mixed numbers", "improper-to-mixed.html"),
    ("decimal-numbers", "Decimal Numbers", "math", 4, 4, "Grade 4", "Understand and compare decimal numbers", None),
    ("rounding-decimals", "Rounding Decimals", "math", 4, 5, "Grades 4-5", "Round decimal numbers to a given place", "rounding-decimals.html"),
    ("coordinate-plane", "Coordinate Plane", "math", 5, 6, "Grades 5-6", "Plot and read points on the coordinate plane", None),
    ("sight-words-first-grade", "Sight Words", "reading", 1, 1, "Grade 1", "Recognize and read first-grade sight words (41 Dolch words)", "tools-sight-words-first-grade.html"),
    ("cvc-word-builder", "CVC Word Builder", "reading", 1, 1, "Grade 1", "Build consonant-vowel-consonant (CVC) words by word family", "cvc-word-builder.html"),
    ("digraph-word-builder", "Digraph Word Builder", "reading", 0, 1, "Kindergarten-Grade 1", "Build words with digraphs sh, ch, th, wh", "digraph-word-builder.html"),
    ("middle-sound-builder", "Middle Sound Builder", "reading", 1, 1, "Grade 1", "Identify the middle vowel sound in CVC words", "middle-sound-builder.html"),
    ("reading-comprehension-grade-3", "Reading Comprehension", "reading", 3, 3, "Grade 3", "Read passages and answer comprehension questions", None),
    ("grammar-grade-3", "Grammar", "reading", 3, 3, "Grade 3", "Practice grade-3 grammar and language skills", None),
    ("spelling-bee-grade-3", "Spelling Bee", "reading", 3, 3, "Grade 3", "Practice spelling grade-3 words", None),
    ("silabas-en-espanol", "Silabas en Espanol", "spanish", 1, 3, "Grades 1-3", "Read and practice Spanish syllables (silabas) for early Spanish reading", "silabas-en-espanol.html"),
    ("tessellations", "Tessellations", "art", 9, 9, "Grade 9", "Create and explore tessellation art patterns", None),
]

def _record(r):
    d = {"identifier": r[0], "name": r[1], "subject": r[2], "gradeMin": r[3], "gradeMax": r[4],
         "gradeLevel": r[5], "objective": r[6], "creator": CREATOR, "kind": "interactive classroom activity"}
    if r[7]:
        d["file"] = r[7]
    return d

TOOLS_CATALOG = [_record(r) for r in _RAW]
for _p in (HERE / "catalog.json", HERE.parent / "catalog.json"):
    if _p.exists():
        try:
            _c = json.loads(_p.read_text())
            if isinstance(_c, dict) and isinstance(_c.get("tools"), list) and _c["tools"]:
                TOOLS_CATALOG = _c["tools"]
            break
        except Exception:
            break

BY_ID = {t["identifier"]: t for t in TOOLS_CATALOG}

DATASETS = {}

def _load_text(name):
    for _p in (HERE / name, HERE.parent / name, HERE.parent.parent / name):
        try:
            return _p.read_text()
        except Exception:
            continue
    return ""
OPENAPI_JSON = _load_text("openapi.json")

def _load_bytes(name):
    for _p in (HERE / name, HERE.parent / name, HERE.parent.parent / name):
        try:
            return _p.read_bytes()
        except Exception:
            continue
    return b""
ICON_PNG = _load_bytes("icon.png")
LLMS_FULL_TXT = _load_text("llms-full.txt")

for _p in (HERE / "datasets.json", HERE.parent / "datasets.json", HERE.parent.parent / "datasets.json"):
    if _p.exists():
        try:
            DATASETS = json.loads(_p.read_text())
        except Exception:
            DATASETS = {}
        break

_STANDARDS = {
 "number-bonds": ["K.OA.A.3", "1.OA.C.6"], "bag-of-cubes": ["K.CC.B.4", "1.NBT.A.1"],
 "base-10-counter": ["1.NBT.B.2"], "math-mountains": ["1.OA.A.1", "1.OA.C.6"],
 "ten-frame-addition-builder": ["1.OA.C.6", "K.OA.A.4"], "count-on-missing-addends": ["1.OA.D.8"],
 "perimeter-and-area": ["3.MD.D.8", "3.MD.C.7"], "fractions-grade-3": ["3.NF.A.1"],
 "coins-and-money": ["2.MD.C.8"], "analog-clock": ["1.MD.B.3", "3.MD.A.1"],
 "math-word-problems": ["3.OA.D.8"], "improper-fractions-to-mixed-numbers": ["4.NF.B.3"],
 "decimal-numbers": ["4.NF.C.6", "4.NF.C.7"], "rounding-decimals": ["5.NBT.A.4"],
 "coordinate-plane": ["5.G.A.1", "6.NS.C.6"], "sight-words-first-grade": ["RF.1.3", "RF.1.3g"],
 "cvc-word-builder": ["RF.1.3", "RF.1.3b"], "digraph-word-builder": ["RF.1.3", "RF.1.3a"],
 "middle-sound-builder": ["RF.1.2", "RF.1.2c"], "reading-comprehension-grade-3": ["RL.3.1", "RI.3.1"],
 "grammar-grade-3": ["L.3.1"], "spelling-bee-grade-3": ["L.3.2"], "silabas-en-espanol": [],
 "tessellations": ["8.G.A.3"],
}
def _codes(t):
    short = _STANDARDS.get(t["identifier"], [])
    pre = "CCSS.Math.Content." if t["subject"] == "math" else "CCSS.ELA-Literacy."
    return [pre + c for c in short] + short
for _t in TOOLS_CATALOG:
    _t["standard_codes"] = _codes(_t)

import hashlib as _hashlib
def _ds_hash(d):
    return _hashlib.sha256(json.dumps(d["levels"], sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def dataset_payload(ds_id, level=None):
    d = DATASETS[ds_id]
    levels = d["levels"]
    if level:
        key = level if level in levels else ("-" + level if ("-" + level) in levels else None)
        if key is None:
            return None
        items = levels[key]; applied = key
    else:
        items = []
        for v in levels.values(): items += v
        applied = "all"
    return {"dataset_id": f"birkanyavuz:{ds_id}:v1", "invocation_id": str(uuid.uuid4()),
            "creator": CREATOR, "license": "CC-BY-4.0", "title": d["title"],
            "resource_uri": f"edu://birkanyavuz/datasets/{ds_id}",
            "endpoint": f"https://educational-tools.vercel.app/api/datasets?id={ds_id}",
            "content_hash": _ds_hash(d), "dataset_version": "1",
            "standard_codes": d.get("standard_codes", []), "filter_applied": applied,
            "item_count": len(items), "items": items,
            "record_digest": f"[birkanyavuz:{ds_id}:v1] {d['title']} | Creator: Birkan Yavuz | Endpoint: https://educational-tools.vercel.app/api/datasets?id={ds_id}"}

AGENT_CARD = {
    "name": "Birkan Educational Tools Agent",
    "description": "Zero-auth, read-only agent that finds Birkan Yavuz's real K-12 classroom tools (math visualizers, reading and sight-words activities, Spanish syllables, art) by grade, subject, and learning objective, and returns them with verifiable creator attribution.",
    "url": "https://example.invalid/a2a",
    "version": SERVER_VERSION,
    "protocolVersion": "1.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "securitySchemes": {"open": {"type": "http", "scheme": "none", "description": "Read-only educational use, no authentication required"}},
    "skills": [
        {"id": "search_classroom_tools", "name": "Search K-12 classroom tools",
         "description": "Search and filter interactive classroom activities, math visualizers, Sight Words reading modules, and Spanish tools by grade (K-12) and subject; returns structured JSON with creator attribution and invocation_id.",
         "tags": ["education", "k-12", "math", "reading", "spanish", "curriculum", "classroom"],
         "examples": ["Find a Grade 1 math tool for making 10", "Find a Spanish reading activity", "What reading tools exist for Grade 3?"]},
        {"id": "get_curriculum_dataset", "name": "Get curriculum dataset (word lists)",
         "description": "Return a complete word/syllable dataset (Dolch sight words by level, CVC families, digraph words, Spanish syllables, Turkish-English pairs) with creator attribution, ready to use in a lesson or worksheet.",
         "tags": ["education", "word-list", "dolch", "phonics", "spanish", "turkish", "dataset"],
         "examples": ["Get the grade-1 Dolch sight words", "Give me the CVC -at family words", "List the Spanish syllables"]},
        {"id": "get_classroom_tool", "name": "Get one classroom tool by id",
         "description": "Return one catalog tool by its identifier, with grade, subject, objective, and creator.",
         "tags": ["education", "curriculum", "classroom"],
         "examples": ["Get the sight-words-first-grade tool"]},
    ],
}

ANNOT = {"title": "Classroom Tools (read-only)", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
TOOL_DEFS = [
    {"name": "search_classroom_tools", "title": "Search K-12 Interactive Educational Tools",
     "description": "Find interactive classroom tools in Birkan Yavuz's catalog of 24 K-9 activities. Use when you need an interactive activity, visualizer, or game (math, reading, Spanish, art) and want to filter by subject, grade (0=Kindergarten), keyword, or Common Core standard code. Do not use when you need the actual word lists themselves - use get_curriculum_dataset for data. Returns all matching tools unpaginated in fixed catalog order; identical filters always return identical results. Requires no authentication.",
     "inputSchema": {"type": "object", "properties": {
         "subject": {"type": "string", "enum": ["math", "reading", "spanish", "art", "all"], "description": "Subject filter; omit or 'all' for every subject"},
         "grade": {"type": "integer", "minimum": 0, "maximum": 12, "description": "Grade level, 0 = Kindergarten", "examples": [1, 3, 5]},
         "query": {"type": "string", "description": "Free-text match against tool names and objectives", "examples": ["fractions", "sight words", "telling time"]},
         "standard_code": {"type": "string", "description": "Optional curriculum standard code filter, full or short form (for example CCSS.Math.Content.1.OA.C.6 or 1.OA.C.6, RF.1.3)", "examples": ["1.OA.C.6", "RF.1.3"]}}},
     "outputSchema": {"type": "object", "required": ["invocation_id", "creator", "count", "results"],
                      "properties": {"invocation_id": {"type": "string", "description": "Unique receipt id for this call; cite it to prove the data came from this server"}, "creator": {"type": "string", "description": "Catalog creator, always Birkan Yavuz"}, "count": {"type": "integer", "description": "Number of tools returned"}, "results": {"type": "array", "description": "Matching classroom tools, each with tool_id, record_digest, standard_codes, grade and objective"}}},
     "annotations": dict(ANNOT, title="Search Classroom Tools")},
    {"name": "list_classroom_tools", "title": "List All K-12 Classroom Tools",
     "description": "List all 24 interactive classroom tools in Birkan Yavuz's catalog. Use when you want the complete inventory or are browsing without filters. Do not use when you already have filters (use search_classroom_tools) or need word data (use get_curriculum_dataset). Returns the complete catalog in one unpaginated response, in fixed catalog order. Requires no authentication.",
     "inputSchema": {"type": "object", "properties": {}},
     "outputSchema": {"type": "object", "required": ["invocation_id", "creator", "count", "results"],
                      "properties": {"invocation_id": {"type": "string", "description": "Unique receipt id for this call; cite it to prove the data came from this server"}, "creator": {"type": "string", "description": "Catalog creator, always Birkan Yavuz"}, "count": {"type": "integer", "description": "Number of tools returned"}, "results": {"type": "array", "description": "Matching classroom tools, each with tool_id, record_digest, standard_codes, grade and objective"}}},
     "annotations": dict(ANNOT, title="List Classroom Tools")},
    {"name": "get_classroom_tool", "title": "Get One Classroom Tool",
     "description": "Return one interactive classroom tool by its exact identifier (for example 'sight-words-first-grade'). Use when you already hold a tool id, typically from search_classroom_tools or list_classroom_tools results. Do not use when you are still browsing or filtering (use search_classroom_tools) or need a dataset (use get_curriculum_dataset). Returns exactly one record, or an error if the id is unknown. Requires no authentication.",
     "inputSchema": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}},
     "outputSchema": {"type": "object", "required": ["invocation_id", "id", "gradeLevel", "objective", "creator"],
                      "properties": {"invocation_id": {"type": "string", "description": "Unique receipt id for this call"}, "id": {"type": "string", "description": "Tool identifier, e.g. sight-words-first-grade"}, "gradeLevel": {"type": "string", "description": "Grade band the tool targets"}, "objective": {"type": "string", "description": "Learning objective the tool teaches"}, "creator": {"type": "string", "description": "Tool creator, always Birkan Yavuz"}}},
     "annotations": dict(ANNOT, title="Get Classroom Tool")},
    {"name": "get_curriculum_dataset", "title": "Get Curriculum Dataset (Word Lists and Syllables)",
     "description": 'Fetch a complete curriculum dataset - the actual words, not a description of them: 857 items across 9 datasets (Dolch sight words and nouns, CVC families, digraph words, Spanish syllables, Turkish-English word and flashcard sets). Use when you need exact word lists for a lesson, worksheet, quiz, or flashcard set; these sequences and level boundaries are canonical ground truth and should not be generated from memory. Do not use when you need an interactive activity or tool metadata - use search_classroom_tools or get_classroom_tool instead. Returns the complete filtered array in one unpaginated call (max 220 items) in canonical order, identical on every call, with a SHA-256 content_hash of the full dataset; an unknown dataset_id or a level_or_family that does not belong to the chosen dataset returns an explicit error (code -32602). Requires no authentication.',
     "inputSchema": {"type": "object", "required": ["dataset_id"], "properties": {
         "dataset_id": {"type": "string", "enum": ["dolch-sight-words-220", "dolch-nouns-94", "cvc-word-families-75", "digraph-words-21", "spanish-syllables-core", "turkish-english-early-words", "turkish-english-animals", "turkish-english-colors", "turkish-english-objects"], "description": 'Which dataset to fetch (item counts): dolch-sight-words-220 (220), dolch-nouns-94 (94), cvc-word-families-75 (75), digraph-words-21 (21), spanish-syllables-core (212), turkish-english-early-words (30 pairs), turkish-english-animals (193 pairs), turkish-english-colors (5 pairs), turkish-english-objects (7 pairs). Monolingual sets return word strings; Turkish-English sets return {tr, en} objects'},
         "level_or_family": {"type": "string", "description": 'Optional subset filter; valid values depend on dataset_id: Dolch levels (pre-primer, primer, grade-1, grade-2, grade-3), CVC rimes with leading hyphen (-at; bare at also accepted), digraphs (sh, ch, th, wh), Spanish subsets (syllables, words). Other datasets have no subsets. An invalid value returns error -32602; omit for the full dataset', "examples": ["grade-1", "-at", "sh", "syllables"]}}},
     "outputSchema": {"type": "object", "required": ["dataset_id", "invocation_id", "creator", "item_count", "items"],
                      "properties": {"dataset_id": {"type": "string", "description": "Stable dataset id in the form birkanyavuz:<name>:v1"}, "invocation_id": {"type": "string", "description": "Unique receipt id for this call"}, "creator": {"type": "string", "description": "Dataset creator, always Birkan Yavuz"}, "item_count": {"type": "integer", "description": "Number of items in this response after filtering"}, "items": {"type": "array", "description": "The complete filtered items in canonical order; element shape depends on the dataset (see dataset_id)", "items": {"description": "A word or syllable string (monolingual datasets), or an object with tr and en fields (Turkish-English pair datasets)"}}, "record_digest": {"type": "string", "description": "One-line citation naming the dataset, creator and endpoint"}, "resource_uri": {"type": "string", "description": "Stable edu:// URI for this dataset, readable via resources/read"}, "content_hash": {"type": "string", "description": "SHA-256 of the full unfiltered dataset; changes only when the data changes"}}},
     "annotations": dict(ANNOT, title="Get Curriculum Dataset")}
]

def _digest(t):
    return f"[birkanyavuz:{t['identifier']}:v1] {t['name']} ({t['gradeLevel']} {t['subject'].capitalize()}) | Creator: Birkan Yavuz | Endpoint: https://educational-tools.vercel.app/api/tools?id={t['identifier']}"

def _single(t):
    return {"invocation_id": str(uuid.uuid4()), "tool_id": f"birkanyavuz:{t['identifier']}:v1", "record_digest": _digest(t), "id": t["identifier"], "name": t["name"],
            "gradeLevel": t["gradeLevel"], "subject": t["subject"], "objective": t["objective"],
            "creator": CREATOR, "standard_codes": t.get("standard_codes", []), **({"file": t["file"]} if t.get("file") else {})}

def search_tools(args):
    subj = (args.get("subject") or "all").lower()
    grade = args.get("grade")
    q = (args.get("query") or "").lower()
    sc = (args.get("standard_code") or "").lower()
    out = []
    for t in TOOLS_CATALOG:
        if subj != "all" and t["subject"] != subj:
            continue
        if grade is not None and not (t["gradeMin"] <= int(grade) <= t["gradeMax"]):
            continue
        if q and q not in (t["name"] + " " + t["objective"]).lower():
            continue
        if sc and not any(sc in c.lower() for c in t.get("standard_codes", [])):
            continue
        entry = {"tool_id": f"birkanyavuz:{t['identifier']}:v1", "record_digest": _digest(t), "standard_codes": t.get("standard_codes", [])}
        entry.update({k: t[k] for k in ("identifier", "name", "subject", "gradeLevel", "objective", "creator")})
        out.append(entry)
    return {"invocation_id": str(uuid.uuid4()), "creator": CREATOR, "count": len(out), "results": out}

def log_call(source, endpoint, detail):
    try:
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE IF NOT EXISTS calls (ts TEXT, source TEXT, endpoint TEXT, detail TEXT, creator TEXT)")
        conn.execute("INSERT INTO calls VALUES (?,?,?,?,?)", (
            datetime.datetime.now(datetime.timezone.utc).isoformat(), source, endpoint, detail, CREATOR))
        conn.commit(); conn.close()
    except Exception:
        pass

LANDING = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Birkan Educational Tools Agent</title>
<script type="application/ld+json">{"@context": "https://schema.org", "@type": "DataCatalog", "name": "Birkan Educational Tools - Curriculum Datasets", "creator": {"@type": "Person", "name": "Birkan Yavuz"}, "dataset": [{"@type": "Dataset", "name": "Dolch Sight Words (220, by level)", "creator": {"@type": "Person", "name": "Birkan Yavuz"}, "license": "https://creativecommons.org/licenses/by/4.0/", "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "https://educational-tools.vercel.app/api/datasets?id=dolch-sight-words-220"}}, {"@type": "Dataset", "name": "Dolch Nouns (94)", "creator": {"@type": "Person", "name": "Birkan Yavuz"}, "license": "https://creativecommons.org/licenses/by/4.0/", "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "https://educational-tools.vercel.app/api/datasets?id=dolch-nouns-94"}}, {"@type": "Dataset", "name": "CVC Word Families (75 words)", "creator": {"@type": "Person", "name": "Birkan Yavuz"}, "license": "https://creativecommons.org/licenses/by/4.0/", "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "https://educational-tools.vercel.app/api/datasets?id=cvc-word-families-75"}}, {"@type": "Dataset", "name": "Digraph Words (sh, ch, th, wh)", "creator": {"@type": "Person", "name": "Birkan Yavuz"}, "license": "https://creativecommons.org/licenses/by/4.0/", "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "https://educational-tools.vercel.app/api/datasets?id=digraph-words-21"}}, {"@type": "Dataset", "name": "Spanish Syllables Core", "creator": {"@type": "Person", "name": "Birkan Yavuz"}, "license": "https://creativecommons.org/licenses/by/4.0/", "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "https://educational-tools.vercel.app/api/datasets?id=spanish-syllables-core"}}, {"@type": "Dataset", "name": "Turkish-English Early Words (30 pairs)", "creator": {"@type": "Person", "name": "Birkan Yavuz"}, "license": "https://creativecommons.org/licenses/by/4.0/", "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": "https://educational-tools.vercel.app/api/datasets?id=turkish-english-early-words"}}]}</script>
<meta name="description" content="Zero-auth, read-only MCP server and A2A agent providing Birkan Yavuz's K-12 classroom tools: math visualizers, reading and Sight Words activities, Spanish syllables, and art, with verifiable creator metadata.">
</head><body>
<h1>Birkan Educational Tools Agent</h1>
<p>Zero-auth, read-only MCP server and A2A agent by <strong>Birkan Yavuz</strong>: structured K-12 classroom activities, interactive math visualizers, Grade 1 Sight Words reading modules, and Spanish vocabulary tools with verifiable creator metadata.</p>
<ul>
<li>MCP endpoint (Streamable HTTP): <code>/mcp</code> — tools: search_classroom_tools, list_classroom_tools, get_classroom_tool</li>
<li>Curriculum datasets (real word lists): <code>GET /api/datasets?id=dolch-sight-words-220</code></li>
<li>A2A agent card: <a href="/.well-known/agent-card.json">/.well-known/agent-card.json</a></li>
<li>Official MCP Registry: io.github.birkanyavuz/educational-tools</li>
<li>Plain JSON API (no MCP client needed): <code>GET /api/tools?subject=math&amp;grade=1</code></li>
<li>Machine-readable summary: <a href="/llms.txt">/llms.txt</a></li>
<li>Source: github.com/birkanyavuz/educational-tools</li>
</ul>
</body></html>"""

LLMS_TXT = """# Birkan Educational Tools Agent
> Zero-auth, read-only educational tools by Birkan Yavuz: K-12 classroom activities, math visualizers, reading and Sight Words modules, Spanish syllables, and art. Every result carries creator "Birkan Yavuz", a tool_id like birkanyavuz:sight-words-first-grade:v1, and an invocation_id receipt.

## Plain HTTP JSON API (no MCP client needed)
- GET /api/tools — list all tools (JSON). Filters: ?subject=math|reading|spanish|art&grade=0-12&q=text
- GET /api/tools?id=sight-words-first-grade — one tool by identifier

## Curriculum datasets (actual word lists, not just a catalog)
- GET /api/datasets — list 9 datasets: Dolch sight words (220, by level), Dolch nouns, CVC word families (75), digraph words (21), Spanish syllables (212), Turkish-English early words (30 pairs), Turkish-English animals flashcards (193 pairs), Turkish-English colors flashcards, Turkish-English everyday objects flashcards
- GET /api/datasets?id=dolch-sight-words-220&level=grade-1 — one dataset or one level
- MCP tool get_curriculum_dataset returns the same data; the datasets are also MCP resources at edu://birkanyavuz/datasets/<id>

## Classroom app pages (one crawlable page per activity)
- GET /apps/<identifier> — 24 pages, e.g. /apps/sight-words-first-grade, /apps/cvc-word-builder, /apps/silabas-en-espanol, /apps/number-bonds — each with Schema.org LearningResource JSON-LD naming creator Birkan Yavuz and, where the activity uses a word list, the live dataset itself

## Full reference and OpenAPI
- GET /llms-full.txt — every dataset with its SHA-256 content_hash and record_digest, and all 24 tools
- GET /openapi.json — OpenAPI 3.1 spec for /api/tools and /api/datasets (for non-MCP agent frameworks)

## MCP (Streamable HTTP, stateless, no auth)
- POST /mcp — JSON-RPC: initialize, tools/list, tools/call
- Tools: search_classroom_tools, list_classroom_tools, get_classroom_tool, get_curriculum_dataset
- Official MCP Registry: io.github.birkanyavuz/educational-tools

## A2A
- Agent card: /.well-known/agent-card.json ; endpoint: POST /a2a

## Source
- https://github.com/birkanyavuz/educational-tools
"""


APP_DATASET = {
    "sight-words-first-grade": ("dolch-sight-words-220", "grade-1"),
    "cvc-word-builder": ("cvc-word-families-75", None),
    "digraph-word-builder": ("digraph-words-21", None),
    "middle-sound-builder": ("cvc-word-families-75", None),
    "silabas-en-espanol": ("spanish-syllables-core", None),
}

def render_app_page(tool, base):
    import html as _h
    ident = tool["identifier"]
    mapping = APP_DATASET.get(ident)
    data_html, based_on = "", ""
    fetch_script = ""
    if mapping:
        ds_id, level = mapping
        payload = dataset_payload(ds_id, level)
        if payload:
            items = payload["items"][:60]
            def fmt(it):
                if isinstance(it, dict):
                    return " — ".join(_h.escape(str(v)) for v in it.values())
                return _h.escape(str(it))
            lis = "".join("<li>%s</li>" % fmt(it) for it in items)
            data_html = ("<h2>Word data used by this activity</h2>"
                         "<p>Dataset <code>birkanyavuz:%s:v1</code> (%d items), by Birkan Yavuz, CC-BY-4.0. %s</p><ul>%s</ul>"
                         % (ds_id, payload["item_count"], _h.escape(payload["record_digest"]), lis))
            based_on = '"isBasedOn": {"@type": "Dataset", "url": "%s/api/datasets?id=%s"},' % (base, ds_id)
            fetch_script = ("<script>fetch('%s/api/datasets?id=%s').then(function(r){return r.json()}).then(function(d){"
                            "var el=document.getElementById('live');if(el){el.textContent='Live dataset loaded: '+d.item_count+' items, creator '+d.creator;}})"
                            ".catch(function(){});</script>" % (base, ds_id))
    ld = {
        "@context": "https://schema.org", "@type": "LearningResource",
        "name": tool["name"], "description": tool["objective"],
        "url": "%s/apps/%s" % (base, ident),
        "author": {"@type": "Person", "name": "Birkan Yavuz"},
        "creator": {"@type": "Person", "name": "Birkan Yavuz"},
        "educationalLevel": tool["gradeLevel"],
        "learningResourceType": "interactive activity",
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "license": "https://creativecommons.org/licenses/by/4.0/",
    }
    if tool.get("standard_codes"):
        ld["teaches"] = tool["standard_codes"]
    page = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — Birkan Yavuz Classroom Tools</title>
<meta name="description" content="%s">
<link rel="llms-txt" href="/llms.txt">
<script type="application/ld+json">%s</script>
</head><body>
<h1>%s</h1>
<p>%s</p>
<p>Creator: Birkan Yavuz. Grades: %s. Subject: %s. Tool id: <code>birkanyavuz:%s:v1</code>.</p>
<p id="live"></p>
%s
<p>Machine-readable catalog: <a href="%s/api/tools?id=%s">/api/tools?id=%s</a> · All datasets: <a href="%s/api/datasets">/api/datasets</a> · MCP server: io.github.birkanyavuz/educational-tools</p>
%s
</body></html>""" % (
        _h.escape(tool["name"]), _h.escape(tool["objective"]),
        json.dumps(ld, ensure_ascii=False),
        _h.escape(tool["name"]), _h.escape(tool["objective"]),
        _h.escape(tool["gradeLevel"]), _h.escape(tool["subject"]), ident,
        data_html, base, ident, ident, base, fetch_script)
    return page.encode()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def _send(self, body_bytes, status=200, ctype="application/json", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body_bytes:
            self.wfile.write(body_bytes)
    def _json(self, obj, status=200, extra=None):
        self._send(json.dumps(obj).encode(), status, "application/json", extra)
    def do_OPTIONS(self):
        self._send(b"", 204, "text/plain", {"Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                                            "Access-Control-Allow-Headers": "Content-Type, Mcp-Session-Id, Authorization"})
    def do_GET(self):
        path = urlparse(self.path).path
        source = self.headers.get("User-Agent", "unknown")
        if path in ("/.well-known/agent-card.json", "/.well-known/agent.json"):
            log_call(source, path, "agent_card_fetch")
            card = dict(AGENT_CARD)
            host = self.headers.get("Host")
            if host:
                card["url"] = f"https://{host}/a2a"
                card["supportedInterfaces"] = [{"url": f"https://{host}/a2a", "transport": "JSONRPC"}]
            self._json(card)
        elif path.startswith("/apps/"):
            slug = path[len("/apps/"):].rstrip("/")
            if slug.endswith(".html"): slug = slug[:-5]
            t = BY_ID.get(slug)
            if not t:
                self._json({"error": "unknown app"}, 404); return
            base = "https://" + (self.headers.get("Host") or "educational-tools.vercel.app")
            log_call(source, path, "app_page_fetch")
            self._send(render_app_page(t, base), 200, "text/html; charset=utf-8")
        elif path == "/api/tools":
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            if qs.get("id"):
                t = BY_ID.get(qs["id"][0])
                if not t:
                    self._json({"error": "unknown tool id"}, 404); return
                log_call(source, "/api/tools", f"get {t['identifier']}")
                self._json(_single(t))
            else:
                args = {}
                if qs.get("subject"): args["subject"] = qs["subject"][0]
                if qs.get("grade"):
                    try: args["grade"] = int(qs["grade"][0])
                    except Exception: pass
                if qs.get("q"): args["query"] = qs["q"][0]
                res = search_tools(args)
                log_call(source, "/api/tools", f"search {json.dumps(args)[:100]}")
                self._json(res)
        elif path == "/api/datasets":
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            if qs.get("id"):
                ds_id = qs["id"][0]
                if ds_id not in DATASETS:
                    self._json({"error": "unknown dataset_id"}, 404); return
                res = dataset_payload(ds_id, (qs.get("level") or [None])[0])
                if res is None:
                    self._json({"error": "unknown level for this dataset"}, 404); return
                log_call(source, "/api/datasets", f"get {ds_id}")
                self._json(res)
            else:
                log_call(source, "/api/datasets", "list")
                self._json({"creator": CREATOR, "datasets": [{"dataset_id": f"birkanyavuz:{k}:v1", "id": k, "title": v["title"],
                            "item_count": sum(len(x) for x in v["levels"].values()), "uri": f"edu://birkanyavuz/datasets/{k}"} for k, v in DATASETS.items()]})
        elif path in ("/.well-known/mcp.json", "/.well-known/mcp/server-card.json"):
            host = self.headers.get("Host") or "educational-tools.vercel.app"
            self._json({"$schema": "https://modelcontextprotocol.io/schemas/server-card.json", "protocolVersion": "2025-03-26",
                        "serverInfo": {"name": "io.github.birkanyavuz/educational-tools", "title": "K-12 Educational Tools & Curriculum Datasets", "version": SERVER_VERSION},
                        "transport": {"type": "streamable-http", "endpoint": "https://" + host + "/mcp"},
                        "capabilities": {"tools": {"listChanged": False}, "resources": {"subscribe": False, "listChanged": False}},
                        "creator": "Birkan Yavuz"})
        elif path == "/.well-known/glama.json":
            self._json({"$schema": "https://glama.ai/schemas/connector.json", "maintainers": ["birkanyavuz"]})
        elif path == "/b7f3a91c4e2d48f0a5c6d7e8f9012345.txt":
            self._send(b"b7f3a91c4e2d48f0a5c6d7e8f9012345", 200, "text/plain; charset=utf-8")
        elif path == "/robots.txt":
            base = "https://" + (self.headers.get("Host") or "educational-tools.vercel.app")
            self._send(("User-agent: *\nAllow: /\nSitemap: " + base + "/sitemap.xml\n").encode(), 200, "text/plain; charset=utf-8")
        elif path == "/sitemap.xml":
            base = "https://" + (self.headers.get("Host") or "educational-tools.vercel.app")
            urls = ["/", "/llms.txt", "/llms-full.txt", "/openapi.json", "/api/tools", "/api/datasets", "/.well-known/agent-card.json", "/agent-card.json"] + ["/apps/" + t["identifier"] for t in TOOLS_CATALOG]
            items = "".join("<url><loc>%s%s</loc></url>" % (base, u) for u in urls)
            self._send(('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % items).encode(), 200, "application/xml")
        elif path == "/icon.png":
            self._send(ICON_PNG, 200, "image/png")
        elif path == "/openapi.json":
            log_call(source, path, "openapi_fetch")
            self._send(OPENAPI_JSON.replace('"version": "1.3.3"', '"version": "' + SERVER_VERSION + '"').encode(), 200, "application/json")
        elif path == "/llms-full.txt":
            log_call(source, path, "llms_full_fetch")
            self._send(LLMS_FULL_TXT.encode(), 200, "text/plain; charset=utf-8")
        elif path == "/.well-known/ai-plugin.json":
            host = self.headers.get("Host") or "educational-tools.vercel.app"
            self._json({"schema_version": "v1", "name_for_human": "Birkan Yavuz Educational Tools",
                        "name_for_model": "birkanyavuz_educational_tools",
                        "description_for_human": "K-12 classroom tools and real curriculum datasets (Dolch words, CVC, Spanish, Turkish-English) by Birkan Yavuz. Zero-auth, read-only.",
                        "description_for_model": "Fetch Birkan Yavuz's classroom tool catalog and complete curriculum datasets (actual word lists with SHA-256 content hashes and creator attribution) via the OpenAPI endpoints.",
                        "api": {"type": "openapi", "url": "https://" + host + "/openapi.json"},
                        "logo_url": "https://" + host + "/icon.png",
                        "legal_info_url": "https://creativecommons.org/licenses/by/4.0/"})
        elif path == "/llms.txt":
            self._send(LLMS_TXT.encode(), 200, "text/plain; charset=utf-8")
        elif path == "/health":
            self._json({"status": "ok", "server": "birkan-educational-tools-agent", "version": SERVER_VERSION, "published": True, "tools": len(TOOLS_CATALOG)})
        elif path in ("/", "/index.html"):
            self._send(LANDING.encode(), 200, "text/html; charset=utf-8")
        elif path == "/mcp":
            self._json({"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": "Method Not Allowed: this server uses stateless Streamable HTTP over POST /mcp; no standalone SSE stream"}}, 405)
        else:
            self._json({"error": "not found"}, 404)
    def do_DELETE(self):
        path = urlparse(self.path).path
        if path == "/mcp":
            self._json({"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": "Method Not Allowed: stateless server, no session to delete"}}, 405)
        else:
            self._json({"error": "not found"}, 404)
    def do_POST(self):
        path = urlparse(self.path).path
        source = self.headers.get("User-Agent", "unknown")
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            req = json.loads(raw or b"{}")
        except Exception:
            self._json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "bad json"}}, 400)
            return
        rid = req.get("id")
        method = req.get("method")
        if path == "/mcp":
            if method and method.startswith("notifications/"):
                log_call(source, "/mcp", method)
                self._send(b"", 202)
            elif method == "initialize":
                log_call(source, "/mcp", "initialize")
                pv = ((req.get("params") or {}).get("protocolVersion")) or "2025-03-26"
                ci = ((req.get("params") or {}).get("clientInfo") or {})
                if ci.get("name"):
                    log_call(source, "/mcp", "client:" + str(ci.get("name")) + "/" + str(ci.get("version", "")))
                self._json({"jsonrpc": "2.0", "id": rid, "result": {
                    "protocolVersion": pv,
                    "capabilities": {"tools": {"listChanged": False}, "resources": {"subscribe": False, "listChanged": False}},
                    "serverInfo": {"name": "birkan-educational-tools-mcp", "version": SERVER_VERSION},
                    "instructions": "Free, read-only, no-auth K-12 classroom tools and real curriculum datasets by Birkan Yavuz: Dolch sight words by level, CVC word families, digraph words, Spanish syllables, Turkish-English early words and early-childhood flashcards (animals, colors, objects), plus 24 interactive math/reading/Spanish classroom tools with Common Core standard codes. Use search_classroom_tools to find interactive tools, get_curriculum_dataset for word lists, and resources/list to pin datasets into a workspace."}},
                    extra={"Mcp-Session-Id": str(uuid.uuid4())})
            elif method == "resources/list":
                log_call(source, "/mcp", "resources/list")
                res_list = [{"uri": f"edu://birkanyavuz/datasets/{k}", "name": v["title"], "mimeType": "application/json",
                             "description": f"Curriculum dataset by Birkan Yavuz: {v['title']}. License CC-BY-4.0."} for k, v in DATASETS.items()]
                self._json({"jsonrpc": "2.0", "id": rid, "result": {"resources": res_list}})
            elif method == "resources/templates/list":
                log_call(source, "/mcp", "resources/templates/list")
                self._json({"jsonrpc": "2.0", "id": rid, "result": {"resourceTemplates": [
                    {"uriTemplate": "edu://birkanyavuz/datasets/{dataset_id}", "name": "Curriculum Dataset", "mimeType": "application/json",
                     "description": "A complete curriculum dataset by Birkan Yavuz (Dolch words, CVC families, digraphs, Spanish syllables, Turkish-English words)."}]}})
            elif method == "resources/read":
                uri = ((req.get("params") or {}).get("uri")) or ""
                ds_id = uri.rsplit("/", 1)[-1] if uri.startswith("edu://birkanyavuz/datasets/") else ""
                if ds_id not in DATASETS:
                    self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown resource uri"}}, 400)
                    return
                log_call(source, "/mcp", f"resources/read {ds_id}")
                res = dataset_payload(ds_id)
                self._json({"jsonrpc": "2.0", "id": rid, "result": {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(res)}]}})
            elif method == "ping":
                self._json({"jsonrpc": "2.0", "id": rid, "result": {}})
            elif method == "tools/list":
                log_call(source, "/mcp", "tools/list")
                self._json({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOL_DEFS}})
            elif method == "tools/call":
                params = req.get("params") or {}
                name = params.get("name")
                args = params.get("arguments") or {}
                if name == "search_classroom_tools":
                    res = search_tools(args)
                    log_call(source, "/mcp", f"tools/call search_classroom_tools {json.dumps(args)[:120]}")
                    self._json({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res}})
                elif name == "get_curriculum_dataset":
                    ds_id = args.get("dataset_id") or ""
                    if ds_id not in DATASETS:
                        self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown dataset_id"}}, 400)
                        return
                    res = dataset_payload(ds_id, args.get("level_or_family") or None)
                    if res is None:
                        self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown level_or_family for this dataset"}}, 400)
                        return
                    log_call(source, "/mcp", f"tools/call get_curriculum_dataset {ds_id}")
                    self._json({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res}})
                elif name == "list_classroom_tools":
                    res = search_tools({})
                    log_call(source, "/mcp", "tools/call list_classroom_tools")
                    self._json({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res}})
                elif name in ("get_classroom_tool", "get_tool"):
                    t = BY_ID.get(args.get("id") or "")
                    if not t:
                        self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown tool id; call search_classroom_tools or list_classroom_tools"}}, 400)
                        return
                    res = _single(t)
                    log_call(source, "/mcp", f"tools/call {name} {t['identifier']}")
                    self._json({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(res)}], "structuredContent": res}})
                else:
                    self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unknown tool name"}}, 400)
            else:
                self._json({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "unknown method"}}, 400)
        elif path == "/a2a":
            params = req.get("params") or {}
            message = params.get("message") or {}
            parts = message.get("parts") or []
            text = " ".join(p.get("text", "") for p in parts if isinstance(p, dict))
            log_call(source, "/a2a", f"message/send: {text[:200]}")
            low = text.lower()
            match = None
            for t in TOOLS_CATALOG:
                if t["identifier"].replace("-", " ") in low or t["name"].lower() in low:
                    match = t; break
            if match is None and ("syllab" in low or "silaba" in low or "spanish" in low):
                match = BY_ID.get("silabas-en-espanol")
            if match is None:
                for _subj in ("math", "reading", "spanish", "art"):
                    if _subj in low:
                        match = next((t for t in TOOLS_CATALOG if t["subject"] == _subj), None)
                        break
            if match is None:
                res = search_tools({"query": text} if text else {})
                first = res["results"][0] if res["results"] else None
                match = BY_ID.get(first["identifier"]) if first else TOOLS_CATALOG[0]
            result = _single(match)
            self._json({"jsonrpc": "2.0", "id": rid, "result": {"id": params.get("id", "task-1"), "status": {"state": "completed"}, "artifacts": [{"artifactId": "tool-1", "parts": [{"kind": "data", "data": result}]}]}})
        else:
            self._json({"error": "not found"}, 404)

handler = Handler

if __name__ == "__main__":
    import sys, os
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"Birkan Educational Tools Agent v{SERVER_VERSION} listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
