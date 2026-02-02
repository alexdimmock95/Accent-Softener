"""Utility functions for the Telegram bot."""

import librosa
import subprocess
import tempfile
from src.voice_transformer import VoiceTransformer

def generate_ipa_audio(ipa_text: str, language: str = 'en') -> str:
    """
    Generate audio from IPA pronunciation using espeak-ng.
    
    Args:
        ipa_text: IPA pronunciation string (e.g., "/dɒɡ/")
        language: Language code (e.g., 'en', 'fr', 'de')
    
    Returns:
        Path to generated audio file
    """
    # Clean IPA text (remove slashes if present)
    clean_ipa = ipa_text.strip('/')
    
    # Create temporary output file
    output_path = tempfile.mktemp(suffix='.wav')
    
    # Generate speech from IPA using espeak-ng
    # -v = voice/language
    # -w = write to file
    # --ipa = input is IPA notation
    subprocess.run([
        'espeak-ng',
        f'-v{language}',
        '-w', output_path,
        '--ipa',
        clean_ipa
    ], check=True)
    
    return output_path

def change_speed(audio_path: str, speed_factor: float, sr: int):
    """
    Change the speed of an audio file.
    
    Args:
        audio_path: Path to the audio file
        speed_factor: Speed multiplication factor (e.g., 0.5 for half speed, 2.0 for double speed)
        sr: Sample rate
        
    Returns:
        Modified audio array
    """
    audio, _ = librosa.load(audio_path, sr=sr)

    vt = VoiceTransformer()
    modified_audio = vt.transform_voice(
        audio, sr,
        age_shift=speed_factor
    )

    return modified_audio