"""
transformer_embeddings.py

Alternative embedding backend using sentence-transformers instead of GloVe.

Benefits:
  - One model for all languages
  - Better semantic similarity
  - Cross-lingual capability

Trade-offs:
  - Slower (~100ms vs <1ms per lookup)
  - Larger memory footprint (2-4GB vs 200MB)
  - Requires: pip install sentence-transformers

Usage:
  Replace the _load_embeddings() method in SmartDifficultyClassifier
  with TransformerEmbeddings.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple


class TransformerEmbeddings:
    """
    Wrapper for sentence-transformers that mimics the gensim API
    so it can drop into the existing classifier code.
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Args:
            model_name: sentence-transformers model name
              - "paraphrase-multilingual-MiniLM-L12-v2" (118MB, 50+ languages, fast)
              - "sentence-transformers/LaBSE" (470MB, 100+ languages, slower but better)
        """
        print(f"Loading transformer model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Transformer model ready!")

        # Cache embeddings for known words to avoid recomputing
        # Format: {"word": numpy_array}
        self._cache = {}

    def _get_embedding(self, word: str) -> np.ndarray:
        """Get or compute embedding for a word."""
        if word not in self._cache:
            self._cache[word] = self.model.encode(word, convert_to_numpy=True)
        return self._cache[word]

    def __contains__(self, word: str) -> bool:
        """Check if word can be embedded (always True for transformers)."""
        return True  # Transformers can embed any text

    def most_similar(self, word: str, topn: int = 10) -> List[Tuple[str, float]]:
        """
        Find most similar words from a vocabulary.

        For this to work, you need to pre-compute embeddings for your
        entire CEFR lexicon. This happens once at initialization.

        Returns:
            List of (word, similarity_score) tuples
        """
        if not hasattr(self, '_lexicon_embeddings'):
            raise RuntimeError(
                "Lexicon not indexed. Call .index_lexicon(words) first."
            )

        query_emb = self._get_embedding(word)

        # Compute cosine similarity with all lexicon words
        similarities = {}
        for lex_word, lex_emb in self._lexicon_embeddings.items():
            if lex_word == word:
                continue  # Skip the word itself

            # Cosine similarity = dot product of normalized vectors
            similarity = np.dot(query_emb, lex_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(lex_emb)
            )
            similarities[lex_word] = float(similarity)

        # Sort by similarity and return top N
        sorted_words = sorted(
            similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_words[:topn]

    def index_lexicon(self, words: List[str], batch_size: int = 32):
        """
        Pre-compute embeddings for all words in the CEFR lexicon.

        This runs once when the classifier loads — takes ~10 seconds
        for 8000 words, but then lookups are fast.

        Args:
            words: List of all words in your CEFR lexicon
            batch_size: How many words to embed at once (larger = faster)
        """
        print(f"Indexing {len(words)} words for similarity search...")

        # Batch encode for speed
        embeddings = self.model.encode(
            words,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Store as dict: word -> embedding
        self._lexicon_embeddings = {
            word: emb for word, emb in zip(words, embeddings)
        }

        print(f"✓ Indexed {len(words)} words")


# ─────────────────────────────────────────────────────────────────────────────
# HOW TO INTEGRATE INTO SmartDifficultyClassifier
# ─────────────────────────────────────────────────────────────────────────────

"""
In smart_difficulty_classifier.py, replace the _load_embeddings() method:

def _load_embeddings(self):
    '''Load transformer embeddings instead of GloVe.'''
    if DISABLE_EMBEDDINGS:
        return None

    try:
        from src.dictionary.transformer_embeddings import TransformerEmbeddings

        # Load the multilingual model (works for all languages!)
        embeddings = TransformerEmbeddings(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )

        # CRITICAL: Index the lexicon so similarity search works
        embeddings.index_lexicon(list(self.lexicon.keys()))

        return embeddings

    except ImportError:
        print("Warning: sentence-transformers not installed.")
        print("Run:  pip install sentence-transformers")
        return None
    except Exception as e:
        print(f"Warning: Could not load transformer embeddings: {e}")
        return None
"""


# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test the transformer embeddings wrapper
    embeddings = TransformerEmbeddings()

    # Pretend lexicon with a few words
    fake_lexicon = ["happy", "sad", "beautiful", "ugly", "run", "walk"]
    embeddings.index_lexicon(fake_lexicon)

    # Find similar words
    print("\nSimilar to 'joyful':")
    for word, score in embeddings.most_similar("joyful", topn=3):
        print(f"  {word}: {score:.3f}")

    print("\nSimilar to 'sprint':")
    for word, score in embeddings.most_similar("sprint", topn=3):
        print(f"  {word}: {score:.3f}")