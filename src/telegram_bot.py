from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load .env file
load_dotenv(Path(__file__).parent.parent / '.env')

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TOKEN is None:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

from src.telegram_bot.config import LANGUAGES
from src.telegram_bot.keyboards import (
       post_translate_keyboard,
       dictionary_result_keyboard,
       speed_keyboard,
       home_keyboard,
       build_language_keyboard
   )
from src.telegram_bot.utils import change_speed
from src.telegram_bot.handlers import start, set_language, handle_voice, handle_message
from src.telegram_bot.callbacks import handle_buttons

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("translate", set_language))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()


### TODO: Add in the voice distortion, male female options in forst set of buttons, "voice effects"
###### TODO: Add in capability to press "pronunciation" or "syntax" for IPA, tongue position/shape info and word type, grammar info, respectively. ALSO ETYMOLOGY
            ##### Pronunciation: ability to press either link text/button to hear pronunciation of IPA item
### TODO/ language aware wiktionary - if detected language is french, wiktionary french version
### TODO: What other models other than xtts can I use? Ones that are ideally faster, more languages
### TODO: what are the other functionalities of google translate that i can use

## python -m src.telegram_bot ##