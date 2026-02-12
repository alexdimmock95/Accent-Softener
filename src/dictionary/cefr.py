"""
smart_difficulty_classifier.py

Classifies word difficulty (A1-C2 CEFR levels) for multiple languages.
Uses lexicon lookup first, then falls back to word embeddings for unknown words.

Confidence scores are only shown when DEBUG=True — never shown to end users.
"""

import os

# ─────────────────────────────────────────────
# DEBUG FLAG — flip this to True when developing
# Never shown in the user-facing output
# ─────────────────────────────────────────────
DEBUG = os.getenv("BOT_DEBUG", "false").lower() == "true"

# ─────────────────────────────────────────────
# EMBEDDINGS CACHE FLAG — set to True to SKIP loading embeddings entirely
# Useful when you want to iterate quickly without waiting for downloads/loads
# Falls back to "UNKNOWN" for words not in the lexicon
# ─────────────────────────────────────────────
DISABLE_EMBEDDINGS = os.getenv("DISABLE_EMBEDDINGS", "false").lower() == "true"
if DISABLE_EMBEDDINGS:
    print("⚠️  EMBEDDINGS DISABLED (DISABLE_EMBEDDINGS=true)")
    print("    Only lexicon lookups will be used. Unknown words → 'UNKNOWN'")



# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE CONFIGURATION
#
# Each language entry explains:
#   - what CEFR data is freely available
#   - where to download it
#   - which gensim embedding model to use
#
# Coverage guide:
#   ✅ Good data available
#   ⚠️  Partial data available (community lists, may have gaps)
#   ❌  Very limited (you'll rely heavily on the embedding fallback)
# ─────────────────────────────────────────────────────────────────────────────

LANGUAGE_CONFIG = {
    "en": {
        "name": "English",
        "coverage": "✅",
        "lexicon_source": (
            "Cambridge English Profile: https://www.englishprofile.org/wordlists\n"
            "Also: https://github.com/oprogramador/cefr-levels (free, MIT licensed)"
        ),
        # gensim model name — downloads automatically on first use (~130MB)
        "embedding_model": "glove-wiki-gigaword-100",
    },
    "de": {
        "name": "German",
        "coverage": "✅",
        "lexicon_source": (
            "Goethe Institut word lists (A1–C2): https://www.goethe.de/en/spr/ueb/prf/prf/gb.html\n"
            "Frequency list with CEFR: https://github.com/Bartlomiej-Ciszewski/german-cefr-wordlist"
        ),
        "embedding_model": "word2vec-ruscorpora-300",  # fallback — better German models need manual download
    },
    "fr": {
        "name": "French",
        "coverage": "✅",
        "lexicon_source": (
            "DELF/DALF official vocabulary: https://www.ciep.fr/en/delf-dalf\n"
            "Wiktionary-based French CEFR list: https://github.com/s-m-e/french-cefr-wordlist"
        ),
        "embedding_model": "fasttext-wiki-news-subwords-300",  # covers French too
    },
    "es": {
        "name": "Spanish",
        "coverage": "✅",
        "lexicon_source": (
            "DELE exam vocabulary: https://www.cervantes.es/lengua_y_ensenanza/aprender_espanol/dele.htm\n"
            "Community CEFR list: https://github.com/matigumma/spanish-cefr"
        ),
        "embedding_model": "fasttext-wiki-news-subwords-300",
    },
    "it": {
        "name": "Italian",
        "coverage": "⚠️",
        "lexicon_source": (
            "CILS exam vocabulary (Perugia): https://www.cils.unistrasi.it\n"
            "No clean free download exists yet — manual work required"
        ),
        "embedding_model": "fasttext-wiki-news-subwords-300",
    },
    "pt": {
        "name": "Portuguese",
        "coverage": "⚠️",
        "lexicon_source": (
            "CAPLE/CELPE-Bras frequency lists\n"
            "Partial community list: https://github.com/fserb/pt-cefr"
        ),
        "embedding_model": "fasttext-wiki-news-subwords-300",
    },
    "nl": {
        "name": "Dutch",
        "coverage": "⚠️",
        "lexicon_source": (
            "NT2 (Dutch as second language) word lists from Inburgering:\n"
            "https://www.inburgeren.nl — no clean download, needs scraping"
        ),
        "embedding_model": "fasttext-wiki-news-subwords-300",
    },
    "ru": {
        "name": "Russian",
        "coverage": "⚠️",
        "lexicon_source": (
            "TORFL (ТРКИ) exam vocabulary by level:\n"
            "https://www.torfl.ru — word lists available per level PDF"
        ),
        "embedding_model": "word2vec-ruscorpora-300",
    },
    "zh": {
        "name": "Chinese (Mandarin)",
        "coverage": "⚠️",
        "lexicon_source": (
            "HSK word lists map roughly to CEFR:\n"
            "HSK1-2 ≈ A1-A2, HSK3-4 ≈ B1-B2, HSK5-6 ≈ C1-C2\n"
            "Free HSK lists: https://www.HSKacademy.com/word-list/"
        ),
        "embedding_model": "fasttext-wiki-news-subwords-300",
    },
    "ja": {
        "name": "Japanese",
        "coverage": "⚠️",
        "lexicon_source": (
            "JLPT levels map roughly to CEFR:\n"
            "N5 ≈ A1, N4 ≈ A2, N3 ≈ B1, N2 ≈ B2, N1 ≈ C1-C2\n"
            "Free JLPT lists: https://www.jlpt.jp/e/about/levelsummary.html"
        ),
        "embedding_model": "fasttext-wiki-news-subwords-300",
    },
    "ko": {
        "name": "Korean",
        "coverage": "❌",
        "lexicon_source": (
            "TOPIK levels loosely map to CEFR but no clean public CEFR list exists.\n"
            "TOPIK vocab: https://www.topik.go.kr"
        ),
        "embedding_model": "fasttext-wiki-news-subwords-300",
    },
    "ar": {
        "name": "Arabic",
        "coverage": "❌",
        "lexicon_source": (
            "No clean public CEFR Arabic list — very limited.\n"
            "Partial resource: ALECSO Arabic level descriptors"
        ),
        "embedding_model": "fasttext-wiki-news-subwords-300",
    },
}

# Order of CEFR levels — used for sorting and display
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


class SmartDifficultyClassifier:
    """
    Classifies word difficulty (A1–C2) for multiple languages.

    For each lookup:
      1. Check the CEFR lexicon (fast, accurate)
      2. If not found, use word embeddings to infer level from similar known words

    Confidence scores are only included in output when DEBUG mode is on.
    Users never see confidence — it's an internal quality signal.
    """

    def __init__(self, language: str = "en"):
        """
        Args:
            language: Two-letter language code, e.g. "en", "de", "fr"
        """
        if language not in LANGUAGE_CONFIG:
            supported = ", ".join(LANGUAGE_CONFIG.keys())
            raise ValueError(
                f"Language '{language}' not configured. "
                f"Supported languages: {supported}"
            )

        self.language = language
        self.config = LANGUAGE_CONFIG[language]
        self.lexicon = self._load_cefr_lexicon()
        self.embeddings = None  # Lazy-loaded on first use
        self._embeddings_load_attempted = False

        if DEBUG:
            print(f"[DEBUG] Loaded classifier for {self.config['name']}")
            print(f"[DEBUG] Lexicon size: {len(self.lexicon)} words")
            print(f"[DEBUG] Coverage rating: {self.config['coverage']}")
            print(f"[DEBUG] Embeddings will load on demand (lazy loading)")

    # ─────────────────────────────────────────────
    # LEXICON LOADING
    # ─────────────────────────────────────────────

    def _load_cefr_lexicon(self) -> dict:
        """
        Load CEFR word list for the current language.

        Looks for a file named:  cefr_data/{language_code}.txt
        Expected format (tab-separated):
            word    A1
            another_word    B2

        Falls back to a small built-in sample if the file isn't found.
        """
        lexicon = {}

        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, "cefr_data", f"{self.language}.txt")

        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as f:
                for line_number, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue  # skip blank lines and comments

                    parts = line.split("\t")
                    if len(parts) != 2:
                        if DEBUG:
                            print(f"[DEBUG] Skipping malformed line {line_number}: {line!r}")
                        continue

                    word, level = parts
                    level = level.upper().strip()

                    if level not in CEFR_LEVELS:
                        if DEBUG:
                            print(f"[DEBUG] Unknown CEFR level '{level}' at line {line_number}")
                        continue

                    lexicon[word.lower().strip()] = level

            if DEBUG:
                print(f"[DEBUG] Loaded {len(lexicon)} words from {filepath}")

        else:
            # No file found — load a tiny built-in sample to keep the bot runnable
            lexicon = self._get_sample_lexicon()
            if DEBUG:
                print(
                    f"[DEBUG] No lexicon file found at '{filepath}'. "
                    f"Using sample data ({len(lexicon)} words).\n"
                    f"[DEBUG] To get full data, see: {self.config['lexicon_source']}"
                )

        return lexicon

    def _get_sample_lexicon(self) -> dict:
        """
        Tiny built-in sample — just enough to test the system.
        Replace this with real CEFR data files for production use.
        """
        # These are English examples — for other languages you'd want
        # language-specific samples, but this at least keeps the bot running.
        return {
            "cat": "A1", "dog": "A1", "happy": "A1", "sad": "A1",
            "run": "A1", "walk": "A1", "big": "A1", "small": "A1",
            "beautiful": "A2", "dangerous": "A2", "explain": "A2",
            "remember": "A2", "opinion": "A2", "travel": "A2",
            "advantage": "B1", "conclusion": "B1", "recommend": "B1",
            "approximately": "B1", "characteristic": "B1",
            "adequate": "B2", "arbitrary": "B2", "compelling": "B2",
            "inherent": "B2", "notion": "B2", "ambiguous": "B2",
            "meticulous": "C1", "paradigm": "C1", "pragmatic": "C1",
            "ubiquitous": "C1", "intrinsic": "C1", "eloquent": "C1",
            "ephemeral": "C2", "perfunctory": "C2", "obstreperous": "C2",
            "verisimilitude": "C2", "recalcitrant": "C2",
        }

    # ─────────────────────────────────────────────
    # EMBEDDING LOADING
    # ─────────────────────────────────────────────

    def _ensure_embeddings_loaded(self):
        """
        Lazy-load embeddings on first use.
        Only loads if not already loaded and hasn't failed before.
        """
        if self.embeddings is not None or self._embeddings_load_attempted:
            return  # Already loaded or already tried to load
        
        self._embeddings_load_attempted = True
        self.embeddings = self._load_embeddings()

    def _load_embeddings(self):
        """
        Load pre-trained word embeddings via gensim.
        Downloads automatically on first use (one-time, ~100–300MB depending on model).

        Install gensim first:  pip install gensim
        
        Set DISABLE_EMBEDDINGS=true environment variable to skip loading for faster iteration.
        """
        # Quick exit if embeddings are disabled
        if DISABLE_EMBEDDINGS:
            print(f"⚠️  Embeddings disabled for {self.config['name']} — unknown words will be 'UNKNOWN'")
            return None
            
        try:
            import gensim.downloader as api
            model_name = self.config["embedding_model"]
            
            # Check if model is already cached locally
            info = api.info(model_name)
            if info and api.base_dir is not None:
                model_path = os.path.join(api.base_dir, model_name)
                if os.path.exists(model_path):
                    print(f"Loading cached embeddings for {self.config['name']}...")
                    embeddings = api.load(model_name, return_path=False)
                    print("Embeddings ready!")
                    return embeddings
            
            print(f"Loading embeddings for {self.config['name']}...")
            print("(This only downloads once, then it's cached locally)")
            embeddings = api.load(model_name)
            print("Embeddings ready!")
            return embeddings

        except ImportError:
            print("Warning: gensim not installed.")
            print("Run:  pip install gensim")
            print("Without this, unknown words will return 'UNKNOWN' level.")
            return None

        except Exception as e:
            if DEBUG:
                print(f"[DEBUG] Could not load embeddings: {e}")
            else:
                print("Warning: Could not load word embeddings. Unknown words won't be classified.")
            return None

    # ─────────────────────────────────────────────
    # DIFFICULTY INFERENCE (FALLBACK)
    # ─────────────────────────────────────────────

    def _infer_difficulty_from_embeddings(self, word: str):
        """
        When a word isn't in our lexicon, use embeddings to find similar
        words that ARE in the lexicon, then vote on the likely CEFR level.

        Returns:
            (inferred_level, confidence_score, top_similar_words)
            e.g. ("B2", 0.73, [("gorgeous", 0.91), ("stunning", 0.88)])

        Confidence is only exposed to the user interface when DEBUG is True.
        """
        # Lazy-load embeddings on first use
        self._ensure_embeddings_loaded()
        
        if self.embeddings is None or word not in self.embeddings:
            return "UNKNOWN", 0.0, []

        try:
            # Get the 15 most similar words from the embedding space
            similar_words = self.embeddings.most_similar(word, topn=15)
        except KeyError:
            return "UNKNOWN", 0.0, []

        # Only keep similar words whose CEFR level we actually know
        known_similar = [
            (similar_word, similarity)
            for similar_word, similarity in similar_words
            if similar_word in self.lexicon
        ]

        if not known_similar:
            if DEBUG:
                print(f"[DEBUG] '{word}': found similar words but none were in our lexicon")
            return "UNKNOWN", 0.0, []

        # Weighted vote: each known similar word votes for its level,
        # weighted by how similar it is (higher similarity = stronger vote)
        level_votes: dict = {}
        for similar_word, similarity in known_similar:
            level = self.lexicon[similar_word]
            level_votes[level] = level_votes.get(level, 0.0) + similarity

        # The level with the highest total weight wins
        inferred_level = max(level_votes, key=lambda lvl: level_votes[lvl])
        total_weight = sum(level_votes.values())
        confidence = level_votes[inferred_level] / total_weight

        if DEBUG:
            print(f"[DEBUG] '{word}' inference:")
            print(f"[DEBUG]   Similar known words: {known_similar[:5]}")
            print(f"[DEBUG]   Level votes: {level_votes}")
            print(f"[DEBUG]   Inferred: {inferred_level} (confidence: {confidence:.1%})")

        return inferred_level, round(confidence, 3), known_similar

    # ─────────────────────────────────────────────
    # SYNONYM FINDER
    # ─────────────────────────────────────────────

    def get_synonyms_by_level(self, word: str) -> dict:
        """
        Find words similar to the input, grouped by CEFR level.

        This gives the user a useful range:
          A1: easy alternatives
          C2: advanced alternatives

        Returns a dict like:
        {
            "A1": [{"word": "happy", "similarity": 0.91}],
            "B2": [{"word": "content", "similarity": 0.78}],
            ...
        }
        Empty lists mean no similar words were found at that level.
        """
        # Lazy-load embeddings on first use
        self._ensure_embeddings_loaded()
        
        if self.embeddings is None or word not in self.embeddings:
            return {level: [] for level in CEFR_LEVELS}

        try:
            # Cast a wide net — we'll filter down to ones with known CEFR levels
            similar_words = self.embeddings.most_similar(word, topn=60)
        except KeyError:
            return {level: [] for level in CEFR_LEVELS}

        synonyms_by_level: dict = {level: [] for level in CEFR_LEVELS}

        for similar_word, similarity in similar_words:
            # Only include words we know the level of
            if similar_word not in self.lexicon:
                continue

            # Only include reasonably close matches
            if similarity < 0.45:
                continue

            # Don't include the word itself
            if similar_word == word:
                continue

            level = self.lexicon[similar_word]
            synonyms_by_level[level].append({
                "word": similar_word,
                "similarity": round(similarity, 3),
            })

        # Sort each level by similarity (most similar first), cap at 5 per level
        for level in CEFR_LEVELS:
            synonyms_by_level[level] = sorted(
                synonyms_by_level[level],
                key=lambda x: x["similarity"],
                reverse=True
            )[:5]

        return synonyms_by_level

    # ─────────────────────────────────────────────
    # MAIN PUBLIC METHOD
    # ─────────────────────────────────────────────

    def classify_with_synonyms(self, word: str) -> dict:
        """
        Main entry point. Given a word, returns its difficulty level
        and a list of synonyms at each CEFR level.

        Example return value (user-facing, no confidence shown):
        {
            "word": "gorgeous",
            "language": "English",
            "difficulty": "B2",
            "method": "inferred",
            "synonyms": {
                "A1": [{"word": "nice", "similarity": 0.88}],
                "A2": [{"word": "pretty", "similarity": 0.91}],
                "B1": [{"word": "lovely", "similarity": 0.84}],
                "B2": [{"word": "stunning", "similarity": 0.79}],
                "C1": [{"word": "resplendent", "similarity": 0.61}],
                "C2": []
            }
        }

        When DEBUG=True, the result also includes:
            "confidence": 0.73,
            "inferred_from": [("beautiful", 0.93), ...]
        """
        word = word.lower().strip()

        result = {
            "word": word,
            "language": self.config["name"],
        }

        # ── Step 1: Try direct lexicon lookup ───────────────────────────────
        if word in self.lexicon:
            result["difficulty"] = self.lexicon[word]
            result["method"] = "lexicon"

            # Confidence is always 1.0 for lexicon hits (it's a known fact)
            # Only show it in debug mode
            if DEBUG:
                result["confidence"] = 1.0

        # ── Step 2: Fallback to embedding-based inference ───────────────────
        else:
            difficulty, confidence, similar_words = self._infer_difficulty_from_embeddings(word)
            result["difficulty"] = difficulty
            result["method"] = "inferred"

            # Confidence and inference details are debug-only
            if DEBUG:
                result["confidence"] = confidence
                result["inferred_from"] = similar_words[:5]

        # ── Step 3: Find synonyms at each CEFR level ────────────────────────
        result["synonyms"] = self.get_synonyms_by_level(word)

        return result


# ─────────────────────────────────────────────────────────────────────────────
# FORMATTED OUTPUT HELPER
# (call this when displaying results in your bot's UI)
# ─────────────────────────────────────────────────────────────────────────────

def format_result_for_user(result: dict) -> str:
    """
    Format the classifier output into a clean, readable message for users.
    Confidence is never shown here — it's debug-only internal data.
    """
    word = result["word"]
    difficulty = result["difficulty"]
    language = result["language"]
    synonyms = result["synonyms"]

    lines = []
    lines.append(f"📖 **{word}** ({language})")
    lines.append(f"🎯 Difficulty: **{difficulty}**")

    # If we inferred the level, let the user know it's an estimate
    if result["method"] == "inferred":
        lines.append("_(Level estimated — this word isn't in our word list yet)_")

    if difficulty == "UNKNOWN":
        lines.append("⚠️ We couldn't determine the difficulty level for this word.")
    else:
        # Show synonyms grouped by level
        lines.append("\n📚 **Similar words by level:**")
        for level in CEFR_LEVELS:
            words_at_level = synonyms.get(level, [])
            if words_at_level:
                word_list = ", ".join(w["word"] for w in words_at_level)
                lines.append(f"  {level}: {word_list}")
            else:
                lines.append(f"  {level}: —")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST
# Run this file directly to check everything is working:
#   python smart_difficulty_classifier.py
#   BOT_DEBUG=true python smart_difficulty_classifier.py
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Debug mode: {'ON' if DEBUG else 'OFF'}")
    print("(Set BOT_DEBUG=true in your terminal to enable debug output)\n")

    classifier = SmartDifficultyClassifier(language="en")

    test_words = [
        "beautiful",       # should be in lexicon → A2
        "gorgeous",        # probably NOT in lexicon → inferred from embeddings
        "ephemeral",       # should be in lexicon → C2
        "schadenfreude",   # definitely not in lexicon → inferred
    ]

    for test_word in test_words:
        print("─" * 50)
        result = classifier.classify_with_synonyms(test_word)
        print(format_result_for_user(result))

        # In debug mode, show the raw result dict too
        if DEBUG:
            print(f"\n[DEBUG] Raw result: {result}")
        print()