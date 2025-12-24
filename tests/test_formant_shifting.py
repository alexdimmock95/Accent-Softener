import librosa
import numpy as np
import soundfile as sf
import sys
from pathlib import Path
# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.formant_shifter import FormantShifter

def main():
    # ---- Load test audio ----
    audio_path = "/Users/Alex/Documents/Coding/personal_project/accent_softener/audio_files/output/vowels_processed.wav"
    audio, sr = librosa.load(audio_path, sr=None)

    # ---- Instantiate shifter ----
    shifter = FormantShifter(
        sr=sr,
        n_fft=1024,
        hop_length=256,
        win_length=1024,
        max_freq=4000
    )

    # ---- Choose vowel segment (seconds) ----
    start_time = 0.5
    end_time = 7.5

    # ---- Formant shift factor ----
    alpha = 1.15

    # ---- Apply formant shift ----
    shifted_segment = shifter.shift_formants_vowel(
        audio,
        start=start_time,
        end=end_time,
        alpha=alpha
    )

    # ---- Reinsert into original audio ----
    start_s = int(start_time * sr)
    end_s = start_s + len(shifted_segment)

    output = audio.copy()
    output[start_s:end_s] = shifter.crossfade(
        original=audio[start_s:end_s],
        shifted=shifted_segment,
        fade_len=int(0.02 * sr)  # 20 ms crossfade
    )

    # ---- Save result ----
    sf.write("audio_files/output/test_formant_shift.wav", output, sr)

    # ---- Visual sanity check ----
    shifter.plot_spectrogram(audio, "Original")
    shifter.plot_spectrogram(output, "Formant Shifted")


if __name__ == "__main__":
    main()