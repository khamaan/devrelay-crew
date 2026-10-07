"""Small, versioned reference shelf used by the research agent.

These are curated notes, not a live web search. Each card points to the
authoritative Python documentation so a human can verify it.
"""
from __future__ import annotations

import re

CARDS = [
    {"topic": "regular expressions", "keywords": "regex regular expression match search substitute slug text validation re",
     "note": "The re module provides compile, search, fullmatch, and sub for matching and replacing text. Prefer fullmatch when the entire input must conform to a pattern.",
     "url": "https://docs.python.org/3/library/re.html"},
    {"topic": "Unicode normalization", "keywords": "unicode normalize accents transliterate slug name text unicodedata",
     "note": "unicodedata.normalize transforms Unicode text into a chosen normalization form; NFKD can separate many accents before filtering, but behavior must be chosen deliberately for non-Latin text.",
     "url": "https://docs.python.org/3/library/unicodedata.html"},
    {"topic": "URL quoting", "keywords": "url uri quote percent encode safe slug urllib link",
     "note": "urllib.parse.quote percent-encodes text for a URL component. It does not normalize or transliterate text; define the desired slug behavior separately.",
     "url": "https://docs.python.org/3/library/urllib.parse.html"},
    {"topic": "JSON", "keywords": "json parse serialize decode encode data api response",
     "note": "json.loads parses JSON text; json.dumps serializes supported Python values. Validate types after parsing rather than assuming a JSON document has the expected shape.",
     "url": "https://docs.python.org/3/library/json.html"},
    {"topic": "CSV", "keywords": "csv rows columns spreadsheet import export reader writer",
     "note": "The csv module offers reader, writer, DictReader, and DictWriter. Open files with newline='' when using csv readers or writers.",
     "url": "https://docs.python.org/3/library/csv.html"},
    {"topic": "dates and times", "keywords": "datetime date time timezone parse format iso timestamp schedule",
     "note": "datetime provides date, time, datetime, and timezone-aware values. fromisoformat handles many ISO-style strings; clarify timezone assumptions before comparing or storing timestamps.",
     "url": "https://docs.python.org/3/library/datetime.html"},
    {"topic": "paths and files", "keywords": "path file directory filename extension pathlib filesystem",
     "note": "pathlib.Path represents filesystem paths and supports safe path composition, suffix inspection, and reading/writing text. Validate inputs before using them as paths.",
     "url": "https://docs.python.org/3/library/pathlib.html"},
    {"topic": "collections", "keywords": "counter count frequency group defaultdict queue collections",
     "note": "collections.Counter counts hashable items; defaultdict creates missing values through a factory. Both can simplify small aggregation utilities.",
     "url": "https://docs.python.org/3/library/collections.html"},
    {"topic": "unit testing", "keywords": "test tests unittest assertions fixtures edge cases",
     "note": "unittest.TestCase provides assertions and test discovery. Include normal, empty, invalid, and boundary inputs rather than only mirroring the implementation.",
     "url": "https://docs.python.org/3/library/unittest.html"},
]


def lookup_cards(query: str) -> list[dict[str, str]]:
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not words:
        return []
    scored = []
    for card in CARDS:
        tokens = set(re.findall(r"[a-z0-9]+", card["keywords"]))
        score = len(words & tokens)
        if score:
            scored.append((score, card))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["topic"]))
    return [{k: v for k, v in card.items() if k != "keywords"} for _, card in scored[:3]]
