# hermes

A Telegram bot for multilingual voice and text translation, in-chat dictionary lookups, and learning tools (pronunciation practice, word statistics).

## Project Overview

The bot is the main interface. It provides:

- **Translation** — Voice note or text → WhisperX transcription → Google Translate → XTTS v2 voice-cloned audio. Language picker, “Reply in X” for conversational flow, speed presets (0.5x / 1x / 2x).
- **Dictionary** — Wiktionary lookups with definitions, etymology, examples, and **word-form buttons** (conjugations for verbs, plural for nouns, comparative/superlative for adjectives). Pronunciation audio, etymology, practice pronunciation, and Smart Synonyms (CEFR) where supported.
- **Learning** — Event storage, word stats, pronunciation scoring (Wav2Vec2 + DTW), and `/stats` for progress.

Under the hood it uses: **speech_to_speech** (WhisperX, Google Translate, XTTS), **voice_transformer** (speed/age/gender presets), **wiktionary_client** (mwparserfromhell, Telegram-safe formatting), **learning** (SQLite, aggregations), **ml/pronunciation_score**.

## Project Structure

### Root

- **[README.md](README.md)** — This file
- **[requirements.txt](requirements.txt)** — Python dependencies

### Source (`src/`)

- **[telegram_bot.py](src/telegram_bot.py)** — Bot entry point and routing
- **[speech_to_speech.py](src/speech_to_speech.py)** — Voice/text translation (WhisperX, Translate, XTTS)
- **[voice_transformer.py](src/voice_transformer.py)** — Speed/age/gender voice effects
- **[latiniser.py](src/latiniser.py)** — Latin script conversion for non-Latin languages

#### Telegram Bot (`src/telegram_bot/`)

- **[handlers.py](src/telegram_bot/handlers.py)** — Commands and message handlers (translate, dictionary)
- **[callbacks.py](src/telegram_bot/callbacks.py)** — Button callbacks (language, word forms, pronunciation, etc.)
- **[keyboards.py](src/telegram_bot/keyboards.py)** — Inline keyboard layouts
- **[config.py](src/telegram_bot/config.py)** — Languages and bot config

#### Dictionary (`src/dictionary/`)

- **[wiktionary_client.py](src/dictionary/wiktionary_client.py)** — Definitions, etymology, examples, word-forms keyboard
- **[corpus_examples.py](src/dictionary/corpus_examples.py)** — Sentence examples
- **[cefr.py](src/dictionary/cefr.py)** — CEFR difficulty / Smart Synonyms
- **[word_forms_extractor.py](src/dictionary/word_forms_extractor.py)** — Conjugations and word forms

#### Learning (`src/learning/`)

- **[storage.py](src/learning/storage.py)** — SQLite for learning events
- **[events.py](src/learning/events.py)** — Event models
- **[aggregations.py](src/learning/aggregations.py)** — Stats and trends

#### ML (`src/ml/`)

- **[pronunciation_score.py](src/ml/pronunciation_score.py)** — Wav2Vec2-based pronunciation scoring

### Tests (`tests/`)

pytest suite for ASR, denoiser, formant shifting, phonemize, streamer, voice_transformer, speech_to_speech.

### Demo

- **Pipeline demo** — Optional: `python legacy/demo/demo.py` (file or mic → processing → playback), if that script is present.

## Running the Bot

1. Add `TELEGRAM_BOT_TOKEN=...` to a `.env` file at the project root (or set the env var).
2. Start the bot:
   ```bash
   python src/telegram_bot.py
   ```
   or
   ```bash
   python -m src.telegram_bot
   ```

Notes: WhisperX and XTTS are lazy-loaded (first use may be slower). You need network access for Wiktionary and translation APIs.

## Getting Started (development)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests**
   ```bash
   pytest tests/
   ```

3. **Run the demo** (optional, if present)
   ```bash
   python legacy/demo/demo.py
   ```

## Dependencies

Key packages: **python-telegram-bot**, **python-dotenv**, **whisperx**, **TTS** (XTTS), **deep_translator**, **mwparserfromhell**, **gtts**, **soundfile**, **librosa**, **torch**, **onnxruntime** (pronunciation scorer). See [requirements.txt](requirements.txt).

## Learning Analytics

- Events stored in `data/learning_events.db`.
- Aggregations: words learned/reviewed, pronunciation scores, streaks, trends.
- `/stats`: dashboard, difficult words, weekly/monthly progress.

## ML Pronunciation Scorer

- **Wav2Vec2** for phoneme recognition, **DTW** for alignment, **MFCC** features.
- Used by the “Practice Pronunciation” flow in the bot.
- Example:
  ```python
  from src.ml.pronunciation_score import score_user_pronunciation
  result = score_user_pronunciation(user_audio_bytes, "hello")
  print(result['overall_score'], result['feedback'])
  ```
