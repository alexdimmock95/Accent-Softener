import librosa
import numpy as np
import matplotlib.pyplot as plt
import pyworld as pw

class FormantShifter:
    """
    Plausible formant shifter using spectral envelope warping.
    """
    
    def __init__(
        self,
        sr,
        n_fft=1024,
        hop_length=256,
        win_length=1024,
        max_freq=4000,
        multiplier=1.0
    ):
        self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.win_length = win_length
        self.max_freq = max_freq

        # alpha > 1 shifts formant upwards, <1 shifts downwards
        self.vowel_shifts = {
            'i': 1.10,
            'ɪ': 1.05,
            'e': 1.08,
            'ɛ': 1.00,
            'æ': 0.95,
            'ɑ': 0.90,
            'ɒ': 0.92,
            'ɔ': 0.95,
            'o': 1.00,
            'ʊ': 0.97,
            'u': 0.93,
            'ʌ': 1.05,
            'ə': 1.00,
            'ɚ': 1.00,
            'ɝ': 1.00,
        }

        # Scale all vowels by multiplier
        self.vowel_shifts = {k: v * multiplier for k, v in self.vowel_shifts.items()}
    
    def stft(self, audio):
        """
        Convert time-domain audio into a complex spectrogram.

        Output shape:
        (frequency_bins, time_frames)
        """
        return librosa.stft(
            audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length
        )
    
    def warp_magnitude(self, mag, alpha):
        """
        Warp the magnitude spectrum along the frequency axis.
        """
        n_bins, n_frames = mag.shape
        freqs = np.linspace(0, self.sr / 2, n_bins)

        warped_mag = np.zeros_like(mag)

        for i, f in enumerate(freqs):
            if f > self.max_freq:
                warped_mag[i, :] = mag[i, :]
                continue

            src_f = f / alpha
            if src_f < 0 or src_f > self.max_freq:
                continue

            # map frequency → fractional bin index
            src_idx = src_f / (self.sr / 2) * (n_bins - 1)

            low = int(np.floor(src_idx))
            high = min(low + 1, n_bins - 1)
            weight = src_idx - low

            warped_mag[i, :] = (
                (1 - weight) * mag[low, :] +
                weight * mag[high, :]
            )

        return warped_mag

    def istft(self, mag, phase):
        """
        Reconstruct time-domain audio from magnitude + phase.
        """
        S_new = mag * np.exp(1j * phase)

        return librosa.istft(
            S_new,
            hop_length=self.hop_length,
            win_length=self.win_length
        )
    
    def shift_formants_vowel(self, audio, phoneme):
        """
        Apply formant shift to a single vowel phoneme using internal vowel_shifts dict.
        """
        # Pick alpha for this vowel, default 1.0
        alpha = self.vowel_shifts.get(phoneme['phoneme'], 1.0)

        start_s = int(phoneme['start'] * self.sr)
        end_s = int(phoneme['end'] * self.sr)

        segment = audio[start_s:end_s]

        S = self.stft(segment)
        mag, phase = np.abs(S), np.angle(S)
        mag_warped = self.warp_magnitude(mag, alpha)
        shifted_segment = self.istft(mag_warped, phase)

        return shifted_segment
        
    def crossfade(self, original, shifted, fade_len):
        """
        Smoothly blend shifted vowel into original signal.
        """
        fade_len = min(fade_len, len(original) // 2)
        window = np.hanning(fade_len * 2)

        fade_in = window[:fade_len]
        fade_out = window[fade_len:]

        out = original.copy()

        out[:fade_len] = (
            original[:fade_len] * fade_out +
            shifted[:fade_len] * fade_in
        )

        out[fade_len:-fade_len] = shifted[fade_len:-fade_len]

        out[-fade_len:] = (
            shifted[-fade_len:] * fade_out +
            original[-fade_len:] * fade_in
        )

        return out
    
    def plot_spectrogram(self, audio, title="Audio"):
        """
        Display a single audio spectrogram in an interactive window.
        """
        S = self.stft(audio)
        S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)

        plt.figure(figsize=(10, 4))
        librosa.display.specshow(S_db, sr=self.sr, x_axis='time', y_axis='hz')
        plt.colorbar(format="%+2.0f dB")
        plt.title(title)
        plt.tight_layout()
        plt.show()  # <-- pops up a native interactive window

class VoiceTransformer:
    """
    WORLD-based voice transformation for gender/age modification.
    Separate from the STFT-based FormantShifter.
    """
    
    def __init__(self):
        pass
    
    def transform_voice(self, audio, sr, 
                       gender_shift=0,      # semitones
                       age_shift=1.0,       # time-stretch ratio
                       formant_shift=1.0):  # spectral envelope ratio
        """
        Apply voice transformation using WORLD vocoder.
        """

        # Convert to float64 (WORLD requirement)
        audio = audio.astype(np.float64)

        # Extract WORLD features
        f0, sp, ap = pw.wav2world(audio, sr)
        
        # Modify pitch (for gender)
        if gender_shift != 0:
            f0_modified = self._shift_pitch(f0, gender_shift)
        else:
            f0_modified = f0
        
        # Modify formants (spectral envelope)
        if formant_shift != 1.0:
            sp_modified = self._shift_formants(sp, formant_shift)
        else:
            sp_modified = sp
        
        # Resynthesize
        audio_modified = pw.synthesize(f0_modified, sp_modified, ap, sr)
        
        # Time-stretch (for age)
        if age_shift != 1.0:
            audio_modified = librosa.effects.time_stretch(
                audio_modified, 
                rate=age_shift
            )
        
        return audio_modified
    
    def _shift_pitch(self, f0, semitones):
        """Shift pitch by semitones"""
        ratio = 2 ** (semitones / 12)
        return f0 * ratio
    
    def _shift_formants(self, sp, ratio):
        """
        Shift formants by warping spectral envelope.
        sp: spectral envelope from WORLD (n_frames, n_bins)
        ratio: > 1.0 raises formants, < 1.0 lowers them
        """
        n_frames, n_bins = sp.shape
        sp_shifted = np.zeros_like(sp)
        
        for i in range(n_frames):
            old_bins = np.arange(n_bins)
            new_bins = old_bins * ratio
            
            # Clip to valid range
            new_bins_clipped = np.clip(new_bins, 0, n_bins - 1)
            
            # Interpolate
            sp_shifted[i] = np.interp(old_bins, new_bins_clipped, sp[i])
        
        return sp_shifted
    
    # Presets
    def preset_male_to_female(self, audio, sr):
        return self.transform_voice(
            audio, sr,
            gender_shift=8,
            formant_shift=1.15
        )
    
    def preset_female_to_male(self, audio, sr):
        return self.transform_voice(
            audio, sr,
            gender_shift=-8,
            formant_shift=0.88
        )
    
    def preset_older(self, audio, sr):
        return self.transform_voice(
            audio, sr,
            gender_shift=-2,
            age_shift=0.85
        )
    
    def preset_younger(self, audio, sr):
        return self.transform_voice(
            audio, sr,
            gender_shift=3,
            age_shift=1.15
        )