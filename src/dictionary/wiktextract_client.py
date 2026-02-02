"""Enhanced dictionary client using wiktextract for more reliable parsing."""

from wiktextract import parse_wiktionary
import requests


def get_word_data(word: str, language: str = 'en') -> dict:
    """
    Get comprehensive word data using wiktextract.
    
    Args:
        word: The word to look up
        language: Language code (default 'en' for English)
    
    Returns:
        Dictionary containing word data including definitions, IPA, etymology
    """
    # Fetch the raw Wiktionary page
    url = f"https://{language}.wiktionary.org/wiki/{word}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return None
    
    # Parse the page content
    # wiktextract returns structured data
    word_data = parse_wiktionary(response.text, word, language)
    
    return word_data


def extract_ipa(word_data: dict) -> list:
    """Extract IPA pronunciations from wiktextract data."""
    if not word_data:
        return []
    
    ipa_list = []
    
    # wiktextract structures pronunciation data
    if 'sounds' in word_data:
        for sound in word_data['sounds']:
            if 'ipa' in sound:
                ipa_list.append(sound['ipa'])
    
    return ipa_list


def format_for_telegram_enhanced(word: str, max_defs_per_pos: int = 5) -> tuple:
    """
    Enhanced version that returns formatted text AND IPA data.
    
    Returns:
        tuple: (formatted_message: str, ipa_pronunciations: list, has_data: bool)
    """
    word_data = get_word_data(word)
    
    if not word_data:
        return (f"❌ Could not find definition for '{word}'", [], False)
    
    # Extract IPA
    ipa_list = extract_ipa(word_data)
    
    # Build formatted message
    message = f"📖 *{word.title()}*\n\n"
    
    # Add IPA if available
    if ipa_list:
        message += f"🔊 *Pronunciation:*\n"
        for ipa in ipa_list[:3]:  # Limit to 3 pronunciations
            message += f"`{ipa}`\n"
        message += "\n"
    
    # Add definitions (similar to your existing format)
    if 'senses' in word_data:
        for i, sense in enumerate(word_data['senses'][:max_defs_per_pos], 1):
            if 'glosses' in sense:
                gloss = sense['glosses'][0]
                message += f"{i}. {gloss}\n"
    
    return (message, ipa_list, True)