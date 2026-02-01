# src/dictionary/wiktionary_client.py
# Wiktionary client using raw wikitext + mwparserfromhell
# This avoids HTML scraping and is robust to Wiktionary templates/structure.

import requests
import mwparserfromhell
import re

WIKTIONARY_API = "https://en.wiktionary.org/w/api.php"

HEADERS = {
    "User-Agent": "DictionaryBot/1.0 (Educational Project; Contact: user@example.com)"
}


def fetch_wikitext(word: str) -> str | None:
    """
    Fetch raw Wiktionary wikitext for a given word using MediaWiki API.

    Returns:
        Raw wikitext string, or None if page does not exist.
    """
    params = {
        "action": "parse",
        "page": word,
        "prop": "wikitext",
        "format": "json",
    }

    resp = requests.get(WIKTIONARY_API, params=params, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        return None

    data = resp.json()

    ##########
    print("DEBUG: fetched JSON keys:", data.keys())  # <-- optional sanity check
    ##########

    if "error" in data:
        print(f"DEBUG: Wiktionary API returned error for '{word}':", data["error"])
        return None

    wikitext = data["parse"]["wikitext"]["*"]

    # <<< ADD THIS LINE
    print(f"DEBUG: raw wikitext for '{word}':\n", wikitext[:500], "\n---END---")  # print first 500 chars

    return wikitext 

def extract_definitions(
    wikitext: str,
    language: str = "English",
    max_defs_per_pos: int = 5,
):
    """
    Parse raw wikitext and extract definitions for a given language.

    Returns:
        List of dicts:
        [
            {"pos": "Noun", "definitions": ["def1", "def2"]},
            ...
        ]
    """
    code = mwparserfromhell.parse(wikitext)

    # --- Step 1: isolate language section ---
    lang_sections = code.get_sections(matches=language, include_lead=False)
    if not lang_sections:
        return []

    language_section = lang_sections[0]

    entries = []

    # Define allowed POS headings
    allowed_pos = {
        "Noun", "Verb", "Adjective", "Adverb", "Pronoun",
        "Preposition", "Conjunction", "Interjection",
        "Determiner", "Article", "Numeral", "Proper noun"
    }

    for heading in language_section.filter_headings():
        heading_text = heading.title.strip_code().strip()
        if heading_text not in allowed_pos:
            continue

        print("DEBUG: POS heading found:", repr(heading_text))

        # --- grab the section under this heading correctly ---
        pos_sections = language_section.get_sections(matches=heading_text, include_lead=False)
        if not pos_sections:
            continue
        pos_section = pos_sections[0]

        definitions = []
        
        for node in pos_section.nodes:
            text = str(node)  # treat any node as raw text
            for line in text.splitlines():
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    # Remove leading #, #:, #* etc.
                    clean = clean_definition(stripped.lstrip("#:* ").strip())
                    if clean:
                        definitions.append(clean)

        if definitions:
            entries.append({
                "pos": heading_text,
                "definitions": definitions,
            })

    return entries

def clean_definition(text: str) -> str:
    """
    Clean a single definition line while preserving meaning.
    """
    # Remove templates {{...}}
    text = re.sub(r"\{\{[^}]+\}\}", "", text)

    # Replace wiki links [[dog]] -> dog
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def fetch_definitions(word: str, max_defs_per_pos: int = 5) -> dict:
    """
    High-level dictionary lookup.
    """
    empty = {"word": word, "language": "English", "entries": []}

    wikitext = fetch_wikitext(word)
    if not wikitext:
        return empty

    entries = extract_definitions(
        wikitext,
        language="English",
        max_defs_per_pos=max_defs_per_pos,
    )

    return {
        "word": word,
        "language": "English",
        "entries": entries,
    }


def format_for_telegram(word: str, max_defs_per_pos: int = 5) -> str:
    """
    Format dictionary output for Telegram Markdown.
    """
    result = fetch_definitions(word, max_defs_per_pos)

    if not result["entries"]:
        return f"❌ No definition found for '*{word}*'."

    lines = [f"📖 *{word.upper()}*\n"]

    for entry in result["entries"]:
        lines.append(f"*{entry['pos']}*")

        for i, definition in enumerate(entry["definitions"], 1):
            safe = (
                definition.replace("*", "\\*")
                .replace("_", "\\_")
                .replace("[", "\\[")
                .replace("]", "\\]")
                .replace("`", "\\`")
            )
            lines.append(f"  {i}. {safe}")

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    for w in ["dog", "run", "set", "cat"]:
        print("=" * 40)
        print(format_for_telegram(w))