"""
download_cefrlex_data.py

Downloads CEFR-graded vocabulary from the CEFRLex project for multiple languages.

CEFRLex is a family of lexical resources developed by research teams in Belgium,
Sweden, and Spain. Each resource provides word frequencies across CEFR levels
based on actual language learning materials (textbooks, readers).

Available languages:
  - French (FLELex) - 17,800+ entries
  - Dutch (NT2Lex) - 17,700+ entries  
  - Swedish (SVALex) - 15,000+ entries
  - Spanish (ELELex) - estimated 13,000+ entries
  - German - via Profile Deutsch (separate source, see comments)

All data is freely available for research and educational use.

Usage (run from src/dictionary/):
    python download_cefrlex_data.py
"""

import os
import urllib.request
import csv
import io
from collections import Counter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "cefr_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

VALID_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


# ─────────────────────────────────────────────────────────────────────────────
# DATA SOURCES
# ─────────────────────────────────────────────────────────────────────────────

CEFRLEX_SOURCES = {
    "fr": {
        "name": "French (FLELex)",
        "url": "https://cental.uclouvain.be/cefrlex/flelex/download/FLELex-CRF.csv",
        "description": "French as a Foreign Language - 17,800+ entries from textbooks",
        "columns": {
            "word": "Lemma",
            "pos": "POS",
            "A1": "A1",
            "A2": "A2",
            "B1": "B1",
            "B2": "B2",
            "C1": "C1",
            "C2": "C2",
        },
    },
    "nl": {
        "name": "Dutch (NT2Lex)",
        "url": "https://cental.uclouvain.be/cefrlex/nt2lex/download/NT2Lex.csv",
        "description": "Dutch as a Foreign Language (NT2) - 17,700+ entries",
        "columns": {
            "word": "Lemma",
            "pos": "POS",
            "A1": "A1",
            "A2": "A2",
            "B1": "B1",
            "B2": "B2",
            "C1": "C1",
            "C2": "C2",
        },
    },
    "sv": {
        "name": "Swedish (SVALex)",
        "url": "https://spraakbanken.gu.se/sites/spraakbanken.gu.se/files/SVALex_freq.csv",
        "description": "Swedish as a Second Language - 15,000+ entries",
        "columns": {
            "word": "lemma",
            "pos": "pos",
            "A1": "A1.per.mill",
            "A2": "A2.per.mill",
            "B1": "B1.per.mill",
            "B2": "B2.per.mill",
            "C1": "C1.per.mill",
            # Note: SVALex doesn't have C2
        },
    },
    "es": {
        "name": "Spanish (ELELex)",
        "url": "https://cental.uclouvain.be/cefrlex/elelex/download/ELELex.csv",
        "description": "Spanish as a Foreign Language - 13,000+ entries",
        "columns": {
            "word": "Lemma",
            "pos": "POS",
            "A1": "A1",
            "A2": "A2",
            "B1": "B1",
            "B2": "B2",
            "C1": "C1",
            "C2": "C2",
        },
    },
}

# NOTE: German (Profile Deutsch) exists but is not in CEFRLex.
# It's published by Langenscheidt and available at:
# https://www.goethe.de/en/spr/ueb/prf.html
# You'd need to extract from the PDF or purchase the digital version.


def download_csv(url: str) -> str:
    """Download a CSV file and return its content as a string."""
    print(f"  Downloading: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            # Check if it's actually a CSV
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                raise Exception("Got HTML instead of CSV - URL may have changed")
            
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise Exception(f"File not found (404). The CEFRLex download URL may have changed.")
        else:
            raise Exception(f"HTTP {e.code}: {e.reason}")


def infer_cefr_level(row_data: dict, columns: dict) -> str:
    """
    Infer the primary CEFR level for a word based on frequency distribution.
    
    CEFRLex provides frequency per level (how often the word appears in 
    materials for that level). We assign the word to the level where it
    appears most frequently.
    """
    level_freqs = {}
    
    for level in VALID_LEVELS:
        col_name = columns.get(level)
        if col_name is None:
            continue
        
        freq_str = row_data.get(col_name, "0").strip()
        
        # Handle empty or non-numeric values
        try:
            freq = float(freq_str) if freq_str else 0.0
        except ValueError:
            freq = 0.0
        
        if freq > 0:
            level_freqs[level] = freq
    
    if not level_freqs:
        return None  # No frequency data for any level
    
    # Assign to the level with highest frequency
    primary_level = max(level_freqs, key=level_freqs.get)
    return primary_level


def process_cefrlex_file(lang_code: str, source: dict) -> dict:
    """
    Download and process a CEFRLex CSV file.
    
    Returns:
        dict mapping word -> CEFR level
    """
    print(f"\n{'='*70}")
    print(f"Processing: {source['name']}")
    print(f"Description: {source['description']}")
    print(f"{'='*70}")
    
    try:
        content = download_csv(source["url"])
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        print(f"  Skipping {lang_code}")
        return {}
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(content))
    columns = source["columns"]
    
    lexicon = {}
    skipped = 0
    
    for row in reader:
        word = row.get(columns["word"], "").lower().strip()
        
        if not word or len(word) < 2:
            skipped += 1
            continue
        
        # Infer primary CEFR level from frequency distribution
        level = infer_cefr_level(row, columns)
        
        if level is None or level not in VALID_LEVELS:
            skipped += 1
            continue
        
        # Keep first occurrence if word appears multiple times with different POS
        if word not in lexicon:
            lexicon[word] = level
    
    print(f"  ✅ Extracted {len(lexicon)} words")
    if skipped > 0:
        print(f"  ⚠️  Skipped {skipped} entries (no valid data)")
    
    return lexicon


def write_lexicon_file(lang_code: str, lexicon: dict):
    """Write lexicon to a tab-separated file."""
    if not lexicon:
        print(f"  No data to write for {lang_code}")
        return
    
    output_path = os.path.join(OUTPUT_DIR, f"{lang_code}.txt")
    
    # Sort by level then alphabetically
    level_order = {level: i for i, level in enumerate(VALID_LEVELS)}
    sorted_words = sorted(lexicon.items(), key=lambda x: (level_order[x[1]], x[0]))
    
    level_counts = Counter(level for _, level in sorted_words)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {CEFRLEX_SOURCES[lang_code]['name']}\n")
        f.write(f"# Source: CEFRLex project\n")
        f.write(f"# {CEFRLEX_SOURCES[lang_code]['description']}\n")
        f.write(f"# Format: word TAB level\n\n")
        
        current_level = None
        for word, level in sorted_words:
            if level != current_level:
                f.write(f"\n# {level}\n")
                current_level = level
            f.write(f"{word}\t{level}\n")
    
    print(f"\n  📁 Written to: {output_path}")
    print(f"  📊 Level breakdown:")
    for level in VALID_LEVELS:
        count = level_counts.get(level, 0)
        bar = "█" * (count // 50)
        print(f"      {level}: {count:>5} words  {bar}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("Downloading CEFRLex data for multiple languages")
    print("=" * 70)
    print()
    print("This will create/update:")
    for lang_code, source in CEFRLEX_SOURCES.items():
        print(f"  • {OUTPUT_DIR}/{lang_code}.txt")
    print()
    
    for lang_code, source in CEFRLEX_SOURCES.items():
        lexicon = process_cefrlex_file(lang_code, source)
        write_lexicon_file(lang_code, lexicon)
        print()
    
    print("=" * 70)
    print("✅ Done! All available CEFRLex resources downloaded.")
    print()
    print("Note: German is not available via CEFRLex.")
    print("For German, see Profile Deutsch at: https://www.goethe.de/")
    print()
    print("For Italian, Portuguese, Russian, Arabic, Chinese:")
    print("These languages aren't in CEFRLex yet. Use the KELLY lists or")
    print("continue with embedding-based inference for now.")


if __name__ == "__main__":
    main()