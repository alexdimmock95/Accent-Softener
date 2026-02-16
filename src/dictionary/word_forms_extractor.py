# src/dictionary/word_forms_extractor.py
"""
Extract word inflections and conjugations using external libraries.
This module handles:
- Verb conjugations (using mlconjug3 for multiple languages)
- Noun plurals (using inflect for English)
- Adjective comparative/superlative forms (using inflect for English)
"""

from typing import Dict, List, Optional
import inflect

# We'll use lazy loading for mlconjug3 since it's heavy
_conjugators = {}  # Cache conjugators by language


def _get_conjugator(language_code: str):
    """
    Get or create a conjugator for the given language.
    Uses lazy loading to avoid importing heavy libraries at startup.
    
    Args:
        language_code: Two-letter language code (e.g., 'en', 'es', 'fr')
    
    Returns:
        Conjugator instance or None if language not supported
    """
    if language_code in _conjugators:
        return _conjugators[language_code]
    
    try:
        import mlconjug3
        
        # mlconjug3 supports: en, es, fr, it, pt, ro
        supported_languages = ['en', 'es', 'fr', 'it', 'pt', 'ro']
        
        if language_code not in supported_languages:
            print(f"DEBUG: Language '{language_code}' not supported by mlconjug3")
            return None
        
        print(f"DEBUG: Loading conjugator for language '{language_code}'...")
        conjugator = mlconjug3.Conjugator(language=language_code)
        _conjugators[language_code] = conjugator
        print(f"DEBUG: Conjugator loaded successfully")
        return conjugator
        
    except ImportError:
        print("DEBUG: mlconjug3 not installed. Install with: pip install mlconjug3")
        return None
    except Exception as e:
        print(f"DEBUG: Error loading conjugator: {e}")
        return None


def get_verb_conjugations(verb: str, language_code: str = 'en') -> Optional[Dict[str, str]]:
    """
    Get verb conjugations using mlconjug3.
    
    Args:
        verb: The verb to conjugate (infinitive form)
        language_code: Two-letter language code (e.g., 'en', 'es', 'fr')
    
    Returns:
        Dict with key conjugation forms, or None if not found
        Example for English: {
            'infinitive': 'go',
            'present_3sg': 'goes',
            'present_participle': 'going',
            'past': 'went',
            'past_participle': 'gone'
        }
    """
    conjugator = _get_conjugator(language_code)
    if not conjugator:
        return None
    
    try:
        # Conjugate the verb (may return Verb, list of Verb, or None)
        raw = conjugator.conjugate(verb)
        if raw is None:
            print(f"DEBUG: conjugate('{verb}') returned None")
            return None
        conjugation = raw[0] if isinstance(raw, (list, tuple)) else raw
        if not hasattr(conjugation, 'iterate') and not hasattr(conjugation, 'conjug_info'):
            print(f"DEBUG: conjugate returned object without iterate/conjug_info: {type(conjugation)}")
            return None

        # Extract the most useful forms depending on language
        if language_code == 'en':
            return _extract_english_verb_forms(conjugation, verb)
        elif language_code == 'es':
            return _extract_spanish_verb_forms(conjugation, verb)
        elif language_code == 'fr':
            return _extract_french_verb_forms(conjugation, verb)
        else:
            return _extract_generic_verb_forms(conjugation, verb)
    except Exception as e:
        print(f"DEBUG: Error conjugating '{verb}': {e}")
        import traceback
        traceback.print_exc()
        return None

def _extract_english_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Extract ALL English verb forms - complete conjugation table."""
    forms = {'infinitive': verb}

    try:
        for item in conjugation.iterate():
            # Handle variable-length tuples (infinitive has 3, others have 4)
            if len(item) == 4:
                mood, tense, person, conj_form = item
            elif len(item) == 3:
                # Skip infinitive row (already have it)
                continue
            else:
                continue
            
            m, t = (mood or '').lower(), (tense or '').lower()
            
            # Present tense
            if 'indicative' in m and 'present' in t:
                if person == 'I':
                    forms['present_I'] = conj_form
                elif person == 'you':
                    forms['present_you'] = conj_form
                elif person == 'he/she/it':
                    forms['present_he/she/it'] = conj_form
                elif person == 'we':
                    forms['present_we'] = conj_form
                elif person == 'they':
                    forms['present_they'] = conj_form
            
            # Past tense
            elif 'indicative' in m and 'past tense' in t:
                if person == 'I':
                    forms['past_I'] = conj_form
                elif person == 'you':
                    forms['past_you'] = conj_form
                elif person == 'he/she/it':
                    forms['past_he/she/it'] = conj_form
                elif person == 'we':
                    forms['past_we'] = conj_form
                elif person == 'they':
                    forms['past_they'] = conj_form
            
            # Future
            elif 'indicative' in m and 'future' in t:
                if person == 'I':
                    forms['future_I'] = conj_form
                elif person == 'he/she/it':
                    forms['future_he/she/it'] = conj_form
                elif person == 'we':
                    forms['future_we'] = conj_form
            
            # Participles
            elif 'present participle' in t:
                forms['present_participle'] = conj_form
            elif 'past participle' in t:
                forms['past_participle'] = conj_form
                
    except Exception as e:
        print(f"DEBUG: Error extracting English forms: {e}")
    
    return forms if len(forms) > 1 else None


def _extract_spanish_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Extract ALL Spanish verb forms."""
    forms = {'infinitive': verb}

    try:
        for item in conjugation.iterate():
            if len(item) == 4:
                mood, tense, person, conj_form = item
            elif len(item) == 3:
                continue  # Skip infinitive
            else:
                continue
            
            if not conj_form:  # Skip None values
                continue
                
            m, t = (mood or '').lower(), (tense or '').lower()
            
            # Present
            if 'indicativo' in m and 'presente' in t:
                if person == 'yo':
                    forms['present_yo'] = conj_form
                elif person == 'tú':
                    forms['present_tú'] = conj_form
                elif 'él' in person or 'ella' in person:
                    forms['present_él/ella'] = conj_form
                elif person == 'nosotros':
                    forms['present_nosotros'] = conj_form
                elif person == 'vosotros':
                    forms['present_vosotros'] = conj_form
                elif person == 'ellos' or person == 'ellas':
                    forms['present_ellos/ellas'] = conj_form
            
            # Preterite
            elif 'indicativo' in m and 'pretérito' in t and 'imperfecto' not in t:
                if person == 'yo':
                    forms['preterite_yo'] = conj_form
                elif person == 'tú':
                    forms['preterite_tú'] = conj_form
                elif 'él' in person:
                    forms['preterite_él/ella'] = conj_form
            
            # Imperfect
            elif 'indicativo' in m and 'imperfecto' in t:
                if person == 'yo':
                    forms['imperfect_yo'] = conj_form
                elif 'él' in person:
                    forms['imperfect_él/ella'] = conj_form
            
            # Future
            elif 'indicativo' in m and 'futuro' in t:
                if person == 'yo':
                    forms['future_yo'] = conj_form
                elif 'él' in person:
                    forms['future_él/ella'] = conj_form
            
            # Participles
            elif 'gerundio' in t.lower():
                forms['gerund'] = conj_form
            elif 'participio' in t.lower():
                forms['past_participle'] = conj_form
                
    except Exception as e:
        print(f"DEBUG: Error extracting Spanish forms: {e}")
    
    return forms if len(forms) > 1 else None

def _extract_french_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Extract ALL French verb forms with correct person matching."""
    forms = {'infinitive': verb}

    try:
        for item in conjugation.iterate():
            if len(item) == 4:
                mood, tense, person, conj_form = item
            elif len(item) == 3:
                continue  # Skip infinitive row
            else:
                continue
            
            m = (mood or '').lower()
            t = (tense or '').lower()
            p = (person or '').lower()  # Keep lowercase
            
            # Present
            if 'indicatif' in m and 'présent' in t:
                if p == 'je':
                    forms['present_je'] = conj_form
                elif p == 'tu':
                    forms['present_tu'] = conj_form
                elif 'il (' in p or p == 'il':  # Matches "il (elle, on)" but NOT "ils"
                    forms['present_il/elle'] = conj_form
                elif p == 'nous':
                    forms['present_nous'] = conj_form
                elif p == 'vous':
                    forms['present_vous'] = conj_form
                elif 'ils (' in p or p == 'ils':  # Matches "ils (elles)"
                    forms['present_ils/elles'] = conj_form
            
            # Imperfect
            elif 'indicatif' in m and 'imparfait' in t:
                if p == 'je':
                    forms['imperfect_je'] = conj_form
                elif p == 'tu':
                    forms['imperfect_tu'] = conj_form
                elif 'il (' in p or p == 'il':
                    forms['imperfect_il/elle'] = conj_form
                elif p == 'nous':
                    forms['imperfect_nous'] = conj_form
                elif p == 'vous':
                    forms['imperfect_vous'] = conj_form
                elif 'ils (' in p or p == 'ils':
                    forms['imperfect_ils/elles'] = conj_form
            
            # Future
            elif 'indicatif' in m and 'futur' in t:
                if p == 'je':
                    forms['future_je'] = conj_form
                elif p == 'tu':
                    forms['future_tu'] = conj_form
                elif 'il (' in p or p == 'il':
                    forms['future_il/elle'] = conj_form
                elif p == 'nous':
                    forms['future_nous'] = conj_form
                elif p == 'vous':
                    forms['future_vous'] = conj_form
                elif 'ils (' in p or p == 'ils':
                    forms['future_ils/elles'] = conj_form
            
            # Passé simple
            elif 'indicatif' in m and 'passé simple' in t:
                if p == 'je':
                    forms['passe_simple_je'] = conj_form
                elif 'il (' in p or p == 'il':
                    forms['passe_simple_il/elle'] = conj_form
                elif 'ils (' in p or p == 'ils':
                    forms['passe_simple_ils/elles'] = conj_form
            
            # Conditional
            elif 'conditionnel' in m:
                if p == 'je':
                    forms['conditional_je'] = conj_form
                elif 'il (' in p or p == 'il':
                    forms['conditional_il/elle'] = conj_form
            
            # Subjunctive
            elif 'subjonctif' in m and 'présent' in t:
                if p == 'je':
                    forms['subjunctive_je'] = conj_form
                elif 'il (' in p or p == 'il':
                    forms['subjunctive_il/elle'] = conj_form
            
            # Participles
            elif 'participe' in t:
                if 'passé' in t:
                    forms['past_participle'] = conj_form
                elif 'présent' in t:
                    forms['present_participle'] = conj_form
                    
    except Exception as e:
        print(f"DEBUG: Error extracting French forms: {e}")
        import traceback
        traceback.print_exc()
    
    return forms if len(forms) > 1 else None

def _extract_italian_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Extract ALL Italian verb forms."""
    forms = {'infinitive': verb}

    try:
        for item in conjugation.iterate():
            if len(item) == 4:
                mood, tense, person, conj_form = item
            elif len(item) == 3:
                continue
            else:
                continue
            
            m, t = (mood or '').lower(), (tense or '').lower()
            
            # Present
            if 'indicativo' in m and 'presente' in t:
                if person == 'io':
                    forms['present_io'] = conj_form
                elif person == 'tu':
                    forms['present_tu'] = conj_form
                elif 'egli' in person or 'ella' in person:
                    forms['present_lui/lei'] = conj_form
                elif person == 'noi':
                    forms['present_noi'] = conj_form
                elif person == 'voi':
                    forms['present_voi'] = conj_form
                elif 'essi' in person or 'esse' in person:
                    forms['present_loro'] = conj_form
            
            # Imperfect
            elif 'indicativo' in m and 'imperfetto' in t:
                if person == 'io':
                    forms['imperfect_io'] = conj_form
                elif 'egli' in person:
                    forms['imperfect_lui/lei'] = conj_form
            
            # Future
            elif 'indicativo' in m and 'futuro' in t:
                if person == 'io':
                    forms['future_io'] = conj_form
                elif 'egli' in person:
                    forms['future_lui/lei'] = conj_form
            
            # Participles
            elif 'participio' in t or 'gerundio' in t:
                if 'passato' in t:
                    forms['past_participle'] = conj_form
                elif 'gerundio' in t:
                    forms['gerund'] = conj_form
                    
    except Exception as e:
        print(f"DEBUG: Error extracting Italian forms: {e}")
    
    return forms if len(forms) > 1 else None


def _extract_portuguese_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Extract ALL Portuguese verb forms."""
    forms = {'infinitive': verb}

    try:
        for item in conjugation.iterate():
            if len(item) == 4:
                mood, tense, person, conj_form = item
            elif len(item) == 3:
                continue
            else:
                continue
            
            m, t = (mood or '').lower(), (tense or '').lower()
            
            # Present
            if 'indicativo' in m and 'presente' in t:
                if person == 'eu':
                    forms['present_eu'] = conj_form
                elif person == 'tu':
                    forms['present_tu'] = conj_form
                elif 'ele' in person or 'ela' in person or 'você' in person:
                    forms['present_ele/ela'] = conj_form
                elif person == 'nós':
                    forms['present_nós'] = conj_form
                elif 'eles' in person or 'elas' in person or 'vocês' in person:
                    forms['present_eles/elas'] = conj_form
            
            # Imperfect
            elif 'indicativo' in m and 'imperfeito' in t:
                if person == 'eu':
                    forms['imperfect_eu'] = conj_form
                elif 'ele' in person:
                    forms['imperfect_ele/ela'] = conj_form
            
            # Preterite
            elif 'indicativo' in m and 'pretérito' in t:
                if person == 'eu':
                    forms['preterite_eu'] = conj_form
                elif 'ele' in person:
                    forms['preterite_ele/ela'] = conj_form
            
            # Future
            elif 'indicativo' in m and 'futuro' in t:
                if person == 'eu':
                    forms['future_eu'] = conj_form
                elif 'ele' in person:
                    forms['future_ele/ela'] = conj_form
            
            # Participles
            elif 'particípio' in t or 'gerúndio' in t:
                if 'particípio' in t:
                    forms['past_participle'] = conj_form
                elif 'gerúndio' in t:
                    forms['gerund'] = conj_form
                    
    except Exception as e:
        print(f"DEBUG: Error extracting Portuguese forms: {e}")
    
    return forms if len(forms) > 1 else None


def _extract_romanian_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Extract ALL Romanian verb forms."""
    forms = {'infinitive': verb}

    try:
        for item in conjugation.iterate():
            if len(item) == 4:
                mood, tense, person, conj_form = item
            elif len(item) == 3:
                continue
            else:
                continue
            
            m, t = (mood or '').lower(), (tense or '').lower()
            
            # Present
            if 'indicativ' in m and 'prezent' in t:
                if person == 'eu':
                    forms['present_eu'] = conj_form
                elif person == 'tu':
                    forms['present_tu'] = conj_form
                elif 'el' in person or 'ea' in person:
                    forms['present_el/ea'] = conj_form
                elif person == 'noi':
                    forms['present_noi'] = conj_form
                elif 'ei' in person or 'ele' in person:
                    forms['present_ei/ele'] = conj_form
            
            # Imperfect
            elif 'indicativ' in m and 'imperfect' in t:
                if person == 'eu':
                    forms['imperfect_eu'] = conj_form
                elif 'el' in person:
                    forms['imperfect_el/ea'] = conj_form
            
            # Future
            elif 'indicativ' in m and 'viitor' in t:
                if person == 'eu':
                    forms['future_eu'] = conj_form
                elif 'el' in person:
                    forms['future_el/ea'] = conj_form
            
            # Participles
            elif 'participiu' in t or 'gerunziu' in t:
                if 'participiu' in t:
                    forms['past_participle'] = conj_form
                elif 'gerunziu' in t:
                    forms['gerund'] = conj_form
                    
    except Exception as e:
        print(f"DEBUG: Error extracting Romanian forms: {e}")
    
    return forms if len(forms) > 1 else None


def _extract_from_conjug_info(conjug_info: dict, forms: Dict[str, str], lang: str) -> None:
    """Fallback: extract forms from conjug_info dict (mood -> tense -> person -> value)."""
    if not conjug_info:
        return
    try:
        def first_value(d: dict):
            if not d or not isinstance(d, dict):
                return None
            for v in d.values():
                if isinstance(v, str):
                    return v
                if isinstance(v, dict):
                    return first_value(v)
            return None

        ind_key = 'Indicative' if lang == 'en' else 'Indicatif' if lang == 'fr' else 'Indicativo'
        ind = None
        for k, v in conjug_info.items():
            if k and v and isinstance(v, dict) and (k.lower() == 'indicative' or k.lower() == 'indicatif' or k.lower() == 'indicativo'):
                ind = v
                break
        if not ind:
            return
        for tense_name, form_key in [
            ('present', 'present_3sg'), ('Present', 'present_3sg'), ('Présent', 'present_1sg'),
            ('present participle', 'present_participle'), ('Present participle', 'present_participle'),
            ('past', 'past'), ('Past', 'past'),
            ('past participle', 'past_participle'), ('Past participle', 'past_participle'),
            ('Participe passé', 'past_participle'), ('Participio', 'past_participle'),
        ]:
            for tkey, tval in ind.items():
                if tkey and (tkey.lower() == tense_name.lower() or tense_name.lower() in (tkey or '').lower()):
                    if isinstance(tval, dict):
                        if '3s' in tval and form_key == 'present_3sg':
                            forms['present_3sg'] = tval['3s']
                        elif '1s' in tval and lang == 'fr' and 'present' in (tkey or '').lower():
                            forms['present_1sg'] = tval['1s']
                        elif form_key not in forms:
                            s = next((x for x in (tval.values() if isinstance(tval, dict) else []) if isinstance(x, str)), None)
                            if s:
                                forms[form_key] = s
                    break
    except Exception:
        pass


def _extract_generic_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Generic extraction for languages we don't have specific handling for."""
    forms = {'infinitive': verb}

    try:
        for mood, tense, person, conj_form in conjugation.iterate():
            key = f"{(tense or '')}_{person}".replace(' ', '_').lower()
            if key and key != 'infinitive':
                forms[key] = conj_form
            if len(forms) >= 10:
                break
    except Exception:
        pass
    return forms if len(forms) > 1 else None


def get_noun_forms(noun: str, language_code: str = 'en') -> Optional[Dict[str, str]]:
    """
    Get noun inflections (primarily plural for English).
    
    Args:
        noun: The noun to inflect
        language_code: Two-letter language code (currently only 'en' supported)
    
    Returns:
        Dict with forms like {'plural': 'dogs'}, or None if not found
    """
    if language_code != 'en':
        # For non-English, we could add other libraries later
        return None
    
    try:
        p = inflect.engine()
        plural = p.plural(noun)
        
        if plural and plural != noun:
            return {'plural': plural}
        else:
            return None
            
    except Exception as e:
        print(f"DEBUG: Error getting plural for '{noun}': {e}")
        return None


def get_adjective_forms(adjective: str, language_code: str = 'en') -> Optional[Dict[str, str]]:
    """
    Get adjective forms (comparative and superlative for English).
    
    Args:
        adjective: The adjective to inflect
        language_code: Two-letter language code (currently only 'en' supported)
    
    Returns:
        Dict with forms like {'comparative': 'bigger', 'superlative': 'biggest'}
    """
    if language_code != 'en':
        return None
    
    try:
        p = inflect.engine()
        
        forms = {}
        
        # inflect library has comparative/superlative methods
        comparative = p.compare(adjective, 'er')
        superlative = p.compare(adjective, 'est')
        
        # If the library returns results, use them
        # Otherwise, apply basic rules
        if comparative:
            forms['comparative'] = comparative
        else:
            forms['comparative'] = _make_comparative(adjective)
        
        if superlative:
            forms['superlative'] = superlative
        else:
            forms['superlative'] = _make_superlative(adjective)
        
        return forms if forms else None
        
    except Exception as e:
        print(f"DEBUG: Error getting adjective forms for '{adjective}': {e}")
        return None


def _make_comparative(adjective: str) -> str:
    """
    Simple rule-based comparative formation.
    This is a backup in case inflect doesn't work.
    """
    # Long adjectives (3+ syllables) use 'more'
    if len(adjective) > 6:  # Rough heuristic for syllables
        return f'more {adjective}'
    
    # Ending in -y: happy -> happier
    if adjective.endswith('y') and len(adjective) > 1 and adjective[-2] not in 'aeiou':
        return adjective[:-1] + 'ier'
    
    # Ending in -e: large -> larger
    if adjective.endswith('e'):
        return adjective + 'r'
    
    # Short words with CVC pattern: big -> bigger
    if (len(adjective) <= 4 and 
        len(adjective) >= 3 and
        adjective[-1] not in 'aeiou' and 
        adjective[-2] in 'aeiou' and 
        adjective[-3] not in 'aeiou'):
        return adjective + adjective[-1] + 'er'
    
    # Default: add -er
    return adjective + 'er'


def _make_superlative(adjective: str) -> str:
    """Simple rule-based superlative formation."""
    # Long adjectives use 'most'
    if len(adjective) > 6:
        return f'most {adjective}'
    
    if adjective.endswith('y') and len(adjective) > 1 and adjective[-2] not in 'aeiou':
        return adjective[:-1] + 'iest'
    
    if adjective.endswith('e'):
        return adjective + 'st'
    
    if (len(adjective) <= 4 and 
        len(adjective) >= 3 and
        adjective[-1] not in 'aeiou' and 
        adjective[-2] in 'aeiou' and 
        adjective[-3] not in 'aeiou'):
        return adjective + adjective[-1] + 'est'
    
    return adjective + 'est'


def get_word_forms(word: str, pos: str, language_code: str = 'en') -> Optional[Dict[str, str]]:
    """
    Get word forms based on part of speech.
    This is the main entry point that delegates to the appropriate function.
    
    Args:
        word: The word to get forms for
        pos: Part of speech (e.g., "Verb", "Noun", "Adjective")
        language_code: Two-letter language code
    
    Returns:
        Dict of word forms or None
    """
    pos_lower = pos.lower()
    
    if 'verb' in pos_lower:
        return get_verb_conjugations(word, language_code)
    elif 'noun' in pos_lower or 'proper noun' in pos_lower:
        return get_noun_forms(word, language_code)
    elif 'adjective' in pos_lower:
        return get_adjective_forms(word, language_code)
    
    return None

def _escape_telegram_markdown(text: str) -> str:
    """Escape special Telegram markdown characters."""
    return (
        text.replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("`", "\\`")
    )


def format_word_forms_for_telegram(forms: Dict[str, str], pos: str) -> str:
    """
    Format word forms for display in Telegram - grouped by tense with proper headers.
    
    Args:
        forms: Dictionary of word forms
        pos: Part of speech
    
    Returns:
        Formatted string for Telegram with proper markdown escaping
    """
    if not forms:
        return "No forms available."
    
    lines = [f"📝 *{pos} Forms*\n"]
    
    # Show infinitive first
    if 'infinitive' in forms:
        lines.append(f"*Infinitive:* {_escape_telegram_markdown(forms['infinitive'])}\n")
    
    # Group present tense forms
    present_forms = [(k, v) for k, v in forms.items() if k.startswith('present_')]
    if present_forms:
        lines.append("*Present Tense:*")
        for key, value in sorted(present_forms):
            person = key.replace('present_', '').replace('_', ' ').title()
            lines.append(f"  • {person}: {_escape_telegram_markdown(value)}")
        lines.append("")
    
    # Group past/preterite forms
    past_forms = [(k, v) for k, v in forms.items() if k.startswith('past_') and k != 'past_participle']
    preterite_forms = [(k, v) for k, v in forms.items() if k.startswith('preterite_')]
    if past_forms or preterite_forms:
        lines.append("*Past Tense:*")
        for key, value in sorted(past_forms + preterite_forms):
            person = key.replace('past_', '').replace('preterite_', '').replace('_', ' ').title()
            lines.append(f"  • {person}: {_escape_telegram_markdown(value)}")
        lines.append("")
    
    # Group imperfect forms
    imperfect_forms = [(k, v) for k, v in forms.items() if k.startswith('imperfect_')]
    if imperfect_forms:
        lines.append("*Imperfect:*")
        for key, value in sorted(imperfect_forms):
            person = key.replace('imperfect_', '').replace('_', ' ').title()
            lines.append(f"  • {person}: {_escape_telegram_markdown(value)}")
        lines.append("")
    
    # Group future forms
    future_forms = [(k, v) for k, v in forms.items() if k.startswith('future_')]
    if future_forms:
        lines.append("*Future:*")
        for key, value in sorted(future_forms):
            person = key.replace('future_', '').replace('_', ' ').title()
            lines.append(f"  • {person}: {_escape_telegram_markdown(value)}")
        lines.append("")
    
    # Passé simple
    passe_simple_forms = [(k, v) for k, v in forms.items() if k.startswith('passe_simple_')]
    if passe_simple_forms:
        lines.append("*Passé Simple:*")
        for key, value in passe_simple_forms:
            person = key.replace('passe_simple_', '').replace('_', ' ').title()
            lines.append(f"  • {person}: {_escape_telegram_markdown(value)}")
        lines.append("")
    
    # Conditional
    conditional_forms = [(k, v) for k, v in forms.items() if k.startswith('conditional_')]
    if conditional_forms:
        lines.append("*Conditional:*")
        for key, value in conditional_forms:
            person = key.replace('conditional_', '').replace('_', ' ').title()
            lines.append(f"  • {person}: {_escape_telegram_markdown(value)}")
        lines.append("")
    
    # Subjunctive
    subjunctive_forms = [(k, v) for k, v in forms.items() if k.startswith('subjunctive_')]
    if subjunctive_forms:
        lines.append("*Subjunctive:*")
        for key, value in subjunctive_forms:
            person = key.replace('subjunctive_', '').replace('_', ' ').title()
            lines.append(f"  • {person}: {_escape_telegram_markdown(value)}")
        lines.append("")
    
    # Participles and gerunds
    special_forms = []
    if 'present_participle' in forms:
        special_forms.append(f"*Present Participle:* {_escape_telegram_markdown(forms['present_participle'])}")
    if 'past_participle' in forms:
        special_forms.append(f"*Past Participle:* {_escape_telegram_markdown(forms['past_participle'])}")
    if 'gerund' in forms:
        special_forms.append(f"*Gerund:* {_escape_telegram_markdown(forms['gerund'])}")
    
    if special_forms:
        lines.append('\n'.join(special_forms))
    
    # Noun plurals
    if 'plural' in forms:
        lines.append(f"\n*Plural:* {_escape_telegram_markdown(forms['plural'])}")
    
    # Adjective forms
    if 'comparative' in forms:
        lines.append(f"\n*Comparative:* {_escape_telegram_markdown(forms['comparative'])}")
    if 'superlative' in forms:
        lines.append(f"*Superlative:* {_escape_telegram_markdown(forms['superlative'])}")
    
    return '\n'.join(lines)


def _escape_telegram_markdown(text: str) -> str:
    """Escape special Telegram markdown characters."""
    return (
        text.replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("`", "\\`")
    )