"""Handler functions for the Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes
import tempfile
import soundfile as sf

from src.telegram_bot.config import LANGUAGES
from src.telegram_bot.keyboards import (
    post_translate_keyboard,
    dictionary_result_keyboard,
    home_keyboard
)
from src.telegram_bot.utils import change_speed
from src.speech_to_speech import SpeechToSpeechTranslator
from src.dictionary.wiktionary_client import format_for_telegram, format_etymology_for_telegram
from src.latiniser import latinise, NON_LATIN_LANGS


# Initialize translator
translator = SpeechToSpeechTranslator(device="cpu", model_size="base")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    await update.message.reply_text(
        text="What would you like to do?",
        reply_markup=home_keyboard()
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /translate command to set target language."""
    if context.args:
        lang = context.args[0]
        context.user_data['target_lang'] = lang
        await update.message.reply_text(f"✅ Target language set to: {lang}")
    else:
        await update.message.reply_text("Usage: /translate [language_code]")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice message translation."""
    # Snapshot target_lang NOW — we flip it after sending, but still need the old value for the button label
    target_lang = context.user_data.get('target_lang', 'fr')

    # Download voice message
    voice_file = await update.message.voice.get_file()

    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
        await voice_file.download_to_drive(tmp.name)
        context.user_data["last_audio"] = tmp.name

        # --- Transcribe ---
        transcribe_msg = await update.message.reply_text("⏳ Transcribing...")
        input_text = translator.transcribe(tmp.name)

        detected_lang_code = translator.get_source_language()
        detected_lang_name = LANGUAGES.get(detected_lang_code, detected_lang_code)

        await transcribe_msg.edit_text(f"⏳ Transcribing...\n{detected_lang_name}")
        await transcribe_msg.edit_text(f"*{detected_lang_name}* ➡️\n{input_text}", parse_mode="Markdown")

        # --- Translate ---
        translate_msg = await update.message.reply_text("⏳ Translating...")
        translated_text = translator.translate(input_text, target_language=target_lang)

        # Check if target language is non-Latin
        if target_lang in NON_LATIN_LANGS:
            latin = latinise(translated_text, target_lang)
            if latin:
                final_text = (
                    f"➡️ *{LANGUAGES[target_lang]}*\n"
                    f"{translated_text}\n\n"
                    f"_{latin}_\n\n"
                    f"⏳ Generating audio..."
                )
            else:
                final_text = (
                    f"➡️ *{LANGUAGES[target_lang]}*\n{translated_text}\n"
                    f"⏳ Generating audio...")
        else:
            final_text = (
                f"➡️ *{LANGUAGES[target_lang]}*\n"
                f"{translated_text}\n"
                f"⏳ Generating audio..."
                )

        await translate_msg.edit_text(final_text, parse_mode="Markdown")

        output_audio, sr = translator.translate_speech(
            audio_path=tmp.name,
            text=input_text,
            target_language=target_lang
        )

        output_path = "output.wav"
        sf.write(output_path, output_audio, sr)
        context.user_data["last_audio_translated"] = output_path

        # --- After audio is ready, remove "⏳ Generating audio..." but keep Latinisation
        # We can rebuild the message without the loading text
        if target_lang in NON_LATIN_LANGS and latin:
            clean_text = (
                f"➡️ *{LANGUAGES[target_lang]}*\n"
                f"{translated_text}\n\n"
                f"_{latin}_"
            )
        else:
            clean_text = f"➡️ *{LANGUAGES[target_lang]}*\n{translated_text}"

        await translate_msg.edit_text(clean_text, parse_mode="Markdown")

        # --- Store state for buttons / speed menu ---
        context.user_data["last_target_lang"] = target_lang          # e.g. "fr"
        context.user_data["last_detected_lang"] = detected_lang_code # e.g. "en"

        # --- Store last translation for possible later use ---
        context.user_data["last_translated_text"] = translated_text
        context.user_data["last_translated_lang"] = target_lang

        # --- Send audio + all buttons in one message ---
        # "Reply in X" label = target_lang (old target, e.g. French — what they'll speak next)
        # "Reply in X" callback = detected_lang_code (e.g. English — what to translate INTO)
        await update.message.reply_voice(
            voice=open(output_path, 'rb'),
            caption="What would you like to do next?",
            reply_markup=post_translate_keyboard(
                last_detected_lang=detected_lang_code
            )
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (primarily for dictionary lookups)."""
    
    if context.user_data.get("awaiting_dictionary_word"):
        word = update.message.text.strip().lower()
        context.user_data["awaiting_dictionary_word"] = False
        context.user_data["last_dictionary_word"] = word

        formatted_message = format_for_telegram(word, max_defs_per_pos=5)
        
        await update.message.reply_text(
            formatted_message, 
            parse_mode="Markdown",
            reply_markup=dictionary_result_keyboard(word)
        )