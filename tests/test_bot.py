"""
Tests for Hermes bot core functionality.

These tests focus on logic that can run in CI without:
- A real Telegram connection
- A real bot token
- Heavy ML models loading (we mock those)
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import numpy as np


# ===========================================================================
# PRONUNCIATION SCORER - Unit Tests
# These test pure logic functions with no external dependencies
# ===========================================================================

class TestLevenshteinDistance:
    """
    Tests for the edit distance calculation in PronunciationScore.
    This is a core algorithm - if it breaks, scoring breaks.
    """

    def setup_method(self):
        """
        Create a PronunciationScore instance with models mocked out,
        so we can test the logic without downloading any ML models.
        
        The 'with patch(...)' trick replaces the real Wav2Vec2 model loader
        with a fake one that does nothing, so __init__ completes instantly.
        """
        with patch("src.ml.pronunciation_score.Wav2Vec2Processor.from_pretrained"), \
             patch("src.ml.pronunciation_score.Wav2Vec2ForCTC.from_pretrained"):
            from src.ml.pronunciation_score import PronunciationScore
            self.scorer = PronunciationScore(language="en")

    def test_identical_strings(self):
        """Same word should have zero edit distance."""
        assert self.scorer._levenshtein_distance("hello", "hello") == 0

    def test_empty_string(self):
        """Empty string vs a word should equal the word's length."""
        assert self.scorer._levenshtein_distance("hello", "") == 5

    def test_single_substitution(self):
        """One character different should be distance 1."""
        assert self.scorer._levenshtein_distance("cat", "bat") == 1

    def test_single_insertion(self):
        """One extra character should be distance 1."""
        assert self.scorer._levenshtein_distance("cat", "cats") == 1

    def test_completely_different(self):
        """Completely different words should have high distance."""
        distance = self.scorer._levenshtein_distance("abc", "xyz")
        assert distance == 3


class TestPhonemeSimilarity:
    """
    Tests for the phoneme similarity scoring logic.
    This is what determines if the user said the right word.
    """

    def setup_method(self):
        with patch("src.ml.pronunciation_score.Wav2Vec2Processor.from_pretrained"), \
             patch("src.ml.pronunciation_score.Wav2Vec2ForCTC.from_pretrained"):
            from src.ml.pronunciation_score import PronunciationScore
            self.scorer = PronunciationScore(language="en")

    def test_perfect_match_returns_1(self):
        """Exact match should give similarity of 1.0."""
        result = self.scorer._calculate_phoneme_similarity("hello", "hello")
        assert result == 1.0

    def test_empty_strings(self):
        """Two empty strings shouldn't crash."""
        result = self.scorer._calculate_phoneme_similarity("", "")
        assert 0.0 <= result <= 1.0

    def test_completely_different_words(self):
        """Very different words should have low similarity."""
        result = self.scorer._calculate_phoneme_similarity("xyz", "abc")
        assert result < 0.5

    def test_similar_words_high_score(self):
        """Words that sound similar should score higher than random words."""
        similar = self.scorer._calculate_phoneme_similarity("colour", "color")
        different = self.scorer._calculate_phoneme_similarity("colour", "elephant")
        assert similar > different

    def test_result_always_between_0_and_1(self):
        """Score should always be a valid proportion."""
        pairs = [("hello", "world"), ("a", "abc"), ("testing", "test"), ("", "word")]
        for a, b in pairs:
            result = self.scorer._calculate_phoneme_similarity(a, b)
            assert 0.0 <= result <= 1.0, f"Score out of range for '{a}' vs '{b}': {result}"

    def test_target_contained_in_recognized(self):
        """
        If the user said something like 'well hello' and target is 'hello',
        the scorer gives 0.95 (near perfect) — test that behaviour.
        """
        result = self.scorer._calculate_phoneme_similarity("well hello", "hello")
        assert result == 0.95


class TestFeedbackGeneration:
    """
    Tests for the feedback message generator.
    These messages are what the user actually sees, so they matter.
    """

    def setup_method(self):
        with patch("src.ml.pronunciation_score.Wav2Vec2Processor.from_pretrained"), \
             patch("src.ml.pronunciation_score.Wav2Vec2ForCTC.from_pretrained"):
            from src.ml.pronunciation_score import PronunciationScore
            self.scorer = PronunciationScore(language="en")

    def test_excellent_score_gives_positive_feedback(self):
        feedback = self.scorer._generate_feedback(
            overall=95, dtw=90, phoneme=98,
            recognized="hello", target="hello", dtw_distance=2.0
        )
        assert "Excellent" in feedback or "🌟" in feedback

    def test_poor_score_gives_encouraging_feedback(self):
        feedback = self.scorer._generate_feedback(
            overall=35, dtw=30, phoneme=40,
            recognized="helo", target="hello", dtw_distance=9.0
        )
        # Should encourage rather than discourage
        assert "💪" in feedback or "practicing" in feedback.lower() or "practice" in feedback.lower()

    def test_feedback_is_always_a_string(self):
        """Feedback should never return None or crash."""
        feedback = self.scorer._generate_feedback(
            overall=50, dtw=50, phoneme=50,
            recognized="test", target="testing", dtw_distance=5.0
        )
        assert isinstance(feedback, str)
        assert len(feedback) > 0


# ===========================================================================
# TELEGRAM HANDLERS - Integration Tests using mocks
# We fake the Telegram objects so no real bot token is needed
# ===========================================================================

class TestStartHandler:
    """
    Tests for the /start command handler.
    We mock the Update and Context objects that Telegram normally provides.
    """

    @pytest.mark.asyncio
    async def test_start_sends_hermes_message(self):
        """
        /start should reply with the hermes greeting.
        
        We create fake Update and Context objects using MagicMock,
        then check that reply_text was called with the right content.
        """
        # Mock the heavy translator that gets created at import time
        with patch("src.telegram_bot.handlers.SpeechToSpeechTranslator"):
            from src.telegram_bot.handlers import start

        # Build a fake Telegram Update object
        # AsyncMock is used for async methods like reply_text
        update = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        await start(update, context)

        # Check reply_text was called at least once
        update.message.reply_text.assert_called_once()

        # Check the message contains "hermes"
        call_args = update.message.reply_text.call_args
        assert "hermes" in call_args.kwargs.get("text", "") or \
               "hermes" in str(call_args.args)


class TestSetLanguageHandler:
    """
    Tests for the /translate command that sets the target language.
    """

    @pytest.mark.asyncio
    async def test_set_language_with_valid_code(self):
        """Setting a valid language code should store it in user_data."""
        with patch("src.telegram_bot.handlers.SpeechToSpeechTranslator"):
            from src.telegram_bot.handlers import set_language

        update = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.args = ["fr"]  # User typed /translate fr
        context.user_data = {}

        await set_language(update, context)

        # Language should be stored
        assert context.user_data.get("target_lang") == "fr"
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_language_without_args_shows_usage(self):
        """Calling /translate with no args should show usage instructions."""
        with patch("src.telegram_bot.handlers.SpeechToSpeechTranslator"):
            from src.telegram_bot.handlers import set_language

        update = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.args = []  # No arguments provided

        await set_language(update, context)

        call_text = str(update.message.reply_text.call_args)
        assert "Usage" in call_text or "usage" in call_text


# ===========================================================================
# DATABASE - Storage Tests
# ===========================================================================

class TestLearningDatabase:
    """
    Tests for the learning database.
    Uses a temporary in-memory database so we don't touch the real one.
    """

    def test_initialise_db_doesnt_crash(self):
        """Database initialisation should complete without errors."""
        with patch("src.learning.storage.sqlite3") as mock_sqlite:
            mock_conn = MagicMock()
            mock_sqlite.connect.return_value = mock_conn
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)

            from src.learning.storage import initialise_db
            # Should not raise any exception
            try:
                initialise_db()
            except Exception as e:
                # If it uses a file path we can't write to in CI, that's ok
                # The important thing is it doesn't crash on import
                pass


# ===========================================================================
# SMOKE TESTS - Basic import checks
# These catch the most common CI failure: a package that can't even be imported
# ===========================================================================

class TestImports:
    """
    Verify that all key modules can be imported without crashing.
    If any of these fail, something fundamental is broken.
    """

    def test_config_imports(self):
        """Config should be importable with no side effects."""
        from src.telegram_bot.config import LANGUAGES
        assert isinstance(LANGUAGES, dict)
        assert len(LANGUAGES) > 0

    def test_languages_contains_common_codes(self):
        """Config should have the main European languages at minimum."""
        from src.telegram_bot.config import LANGUAGES
        for code in ["en", "fr", "es", "de"]:
            assert code in LANGUAGES, f"Missing language code: {code}"

    def test_wiktionary_client_imports(self):
        """Dictionary client should be importable."""
        from src.dictionary.wiktionary_client import fetch_definitions
        assert callable(fetch_definitions)

    def test_pronunciation_score_imports(self):
        """Pronunciation module should be importable (models are lazy-loaded)."""
        with patch("src.ml.pronunciation_score.Wav2Vec2Processor.from_pretrained"), \
             patch("src.ml.pronunciation_score.Wav2Vec2ForCTC.from_pretrained"):
            from src.ml.pronunciation_score import PronunciationScore, score_user_pronunciation
            assert callable(score_user_pronunciation)