"""
generate_cefr_wordlist.py

Generates cefr_data/en.txt from two high-quality, human-annotated sources:

  Source 1 — CEFR-J Vocabulary Profile (A1–B2 words)
    URL: https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/cefrj-vocabulary-profile-1.5.csv
    License: Free for research and commercial use (cite CEFR-J project)
    Quality: Human-annotated by Tokyo University of Foreign Studies

  Source 2 — Octanove Vocabulary Profile (C1–C2 words)
    URL: https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/octanove-vocabulary-profile-c1c2-1.0.csv
    License: CC BY-SA 4.0
    Quality: Human-annotated by Octanove Labs

These are the same sources used by serious CEFR research projects.
Total expected output: ~8,000-10,000 real vocabulary words.

Usage (run from src/dictionary/):
    python generate_cefr_wordlist.py
"""

import os
import urllib.request
import csv
import io
from collections import Counter

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "cefr_data", "en.txt")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

VALID_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def is_valid_word(word: str) -> bool:
    """
    Filter out non-vocabulary entries — abbreviations, digits, single chars.
    cefrpy had these problems because it computed levels algorithmically.
    These human-annotated sources are much cleaner, but we filter anyway.
    """
    if len(word) < 2:
        return False
    if word.isdigit():
        return False
    if not any(c.isalpha() for c in word):
        return False
    return True


def normalise_level(raw: str) -> str:
    """
    Normalise level strings to standard CEFR format.
    CEFR-J uses sub-levels like 'A1.1', 'A1.2', 'B1.1' — round to main level.
    Also handles 'A2+' style entries.
    """
    raw = raw.strip().upper()

    # A1.1 → A1, B1.2 → B1
    if "." in raw:
        raw = raw.split(".")[0]

    # A2+ → A2
    raw = raw.replace("+", "")

    return raw if raw in VALID_LEVELS else None


# ── Sources ───────────────────────────────────────────────────────────────────

SOURCES = [
    {
        "name": "CEFR-J Vocabulary Profile (A1-B2)",
        "url": "https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/cefrj-vocabulary-profile-1.5.csv",
        "word_col": "headword",
        "level_col": "CEFR",
    },
    {
        "name": "Octanove Vocabulary Profile (C1-C2)",
        "url": "https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/octanove-vocabulary-profile-c1c2-1.0.csv",
        "word_col": "headword",
        "level_col": "CEFR",
    },
]


def fetch_csv(url: str) -> str:
    """Download a CSV and return its content as a string."""
    print(f"  Downloading: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────

lexicon = {}  # word → level (deduped — first source wins if word appears twice)
skipped = 0

for source in SOURCES:
    print(f"\nProcessing: {source['name']}")

    try:
        content = fetch_csv(source["url"])
    except Exception as e:
        print(f"  Failed to download: {e}")
        print(f"  Skipping this source.")
        continue

    reader = csv.DictReader(io.StringIO(content))
    source_count = 0

    for row in reader:
        word = row.get(source["word_col"], "").lower().strip()
        raw_level = row.get(source["level_col"], "").strip()

        if not word or not raw_level:
            skipped += 1
            continue

        if not is_valid_word(word):
            skipped += 1
            continue

        level = normalise_level(raw_level)
        if level is None:
            skipped += 1
            continue

        # Don't overwrite a word already added from an earlier source
        if word not in lexicon:
            lexicon[word] = level
            source_count += 1

    print(f"  Added {source_count} words from this source")


# ── Write output ──────────────────────────────────────────────────────────────

print(f"\nWriting {len(lexicon)} words to {OUTPUT_PATH}...")

# Sort by level then alphabetically so the file is readable by humans
level_order = {level: i for i, level in enumerate(VALID_LEVELS)}
sorted_words = sorted(lexicon.items(), key=lambda x: (level_order[x[1]], x[0]))

level_counts = Counter(level for _, level in sorted_words)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("# English CEFR word list\n")
    f.write("# Sources: CEFR-J Vocabulary Profile + Octanove Vocabulary Profile\n")
    f.write("# Format: word TAB level\n\n")

    current_level = None
    for word, level in sorted_words:
        # Add a section comment when the level changes
        if level != current_level:
            f.write(f"\n# {level}\n")
            current_level = level
        f.write(f"{word}\t{level}\n")

print("\nDone!")
print("\nLevel breakdown:")
for level in VALID_LEVELS:
    count = level_counts.get(level, 0)
    bar = "█" * (count // 30)
    print(f"  {level}: {count:>5} words  {bar}")

if skipped > 0:
    print(f"\n(Skipped {skipped} malformed or invalid entries)")

print(f"\nFile written to: {OUTPUT_PATH}")