"""
Main demo/workflow file - orchestrates the complete accent softening pipeline.

Architecture:
1. Load audio
2. Denoise (full file)
3. ASR with phoneme detection
4. Filter vowels for formant shifting
5. Save output

No chunking during DSP - all processing happens on the full file.
"""


import sys
import numpy as np
import soundfile as sf
from pathlib import Path


# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
from src.denoiser import Denoiser
from src.asr import PhonemeAligner
from src.formant_shifter import FormantShifter
# from src.pitch_shifter import PitchShifter  # Add when ready
# from src.formant_shifter import FormantShifter  # Add when ready


def main():
    print("Accent Softener")
    print("=" * 50)
    
    # Define input and output paths
    input_file = Path("audio_files/input/vowels.wav")
    output_folder = Path("audio_files/output")
    output_folder.mkdir(parents=True, exist_ok=True)
    output_file = output_folder / f"{input_file.stem}_processed.wav"

    # Define temp path
    temp_folder = Path("audio_files/temp")
    temp_folder.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        print(f"ERROR: File not found: {input_file}")
        return
    
    # ============================================================
    # STEP 1: LOAD AUDIO
    # ============================================================
    print("\n" + "="*50)
    print("STEP 1: Load Audio")
    print("="*50)
    
    audio, sr = sf.read(input_file)
    print(f"  File: {input_file.name}")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Original shape: {audio.shape}")
    
    # Ensure mono
    if audio.ndim > 1:
        print("  Converting stereo to mono...")
        audio = np.mean(audio, axis=1)
    
    audio = audio.flatten().astype(np.float32)
    print(f"  Duration: {len(audio)/sr:.2f} seconds")
    print(f"  ✓ Audio loaded")
    
    # ============================================================
    # STEP 2: DENOISE
    # ============================================================
    print("\n" + "="*50)
    print("STEP 2: Denoise Audio")
    print("="*50)
    
    denoiser = Denoiser(model_name="DeepFilterNet3", post_filter=True)
    audio = denoiser.process_frame(audio)
    print("  ✓ Denoising complete")

    # ============================================================
    # STEP 3: ASR TRANSCRIPTION & PHONEME ALIGNMENT
    # ============================================================
    print("\n" + "="*50)
    print("STEP 3: ASR Transcription & Phoneme Alignment")
    print("="*50)

    # --- 3.1 Save denoised audio to temp file ---
    temp_asr_file = temp_folder / f"{input_file.stem}_tempasr{input_file.suffix}"
    sf.write(temp_asr_file, audio, sr)

    # --- 3.2 Initialise phoneme aligner ---
    aligner = PhonemeAligner(
        device="cpu",
        model_size="base",
        compute_type="int8",
        batch_size=16
    )

    aligner.load_models()

    # --- 3.3 Run ASR + alignment ---

    result, vowel_phonemes = aligner.process(str(temp_asr_file))

    ###########################################################################################################################################################################################################
    ################ TODO: print location of result################################################################################################################################################################################################

    print("✓ ASR + phoneme alignment complete")

    # ============================================================
    # STEP 4: FORMANT SHIFTING 
    # ============================================================
    print("\n" + "="*50)
    print("STEP 4: Formant Shifting")
    print("="*50)

    # --- Instantiate the formant shifter ---
    shifter = FormantShifter(
        sr=sr,
        n_fft=1024,
        hop_length=256,
        win_length=1024,
        max_freq=4000
    )

    # --- Apply formant shift to all detected vowel phonemes ---
    for vowel_phoneme in vowel_phonemes:
        shifted_segment = shifter.shift_formants_vowel(audio, vowel_phoneme)

        start_s = int(vowel_phoneme['start'] * sr)
        end_s = start_s + len(shifted_segment)

        audio[start_s:end_s] = shifter.crossfade(
            original=audio[start_s:end_s],
            shifted=shifted_segment,
            fade_len=int(0.02 * sr)  # 20 ms crossfade
        )

    print("  ✓ Formant shifting complete")

    # ============================================================
    # FINAL STEP: SAVE OUTPUT
    # ============================================================
    print("\n" + "="*50)
    print("FINAL STEP: Save Output")
    print("="*50)
    
    sf.write(str(output_file), audio, samplerate=sr, format='WAV')
    
    print(f"\n  Output info:")
    print(f"    Shape: {audio.shape}")
    print(f"    Dtype: {audio.dtype}")
    print(f"    Sample rate: {sr}")
    print(f"    Path: {output_file}")
    
    # Statistics
    original_audio, _ = sf.read(input_file)
    if original_audio.ndim > 1:
        original_audio = np.mean(original_audio, axis=1)
    
    original_rms = np.sqrt(np.mean(original_audio**2))
    processed_rms = np.sqrt(np.mean(audio**2))
    
    print(f"\n  Statistics:")
    print(f"    Original RMS: {original_rms:.4f}")
    print(f"    Processed RMS: {processed_rms:.4f}")
    print(f"    RMS change: {((processed_rms/original_rms - 1)*100):+.1f}%")
    
    print(f"\n✓ Processing complete! Output saved to:")
    print(f"  {output_file.absolute()}")
    
    # ============================================================
    # OPTIONAL: Chunking for streaming
    # ============================================================
    # If you need to stream the output later, you can chunk it here
    # But DSP processing should already be done at this point

if __name__ == "__main__":
    main()



'''    # ============================================================
    # STEP 3: PITCH SHIFT (placeholder)
    # ============================================================
    print("\n" + "="*50)
    print("STEP 3: Pitch Shift")
    print("="*50)
    
    # TODO: Add pitch shifting
    # pitch_shifter = PitchShifter(semitones=-2)
    # audio = pitch_shifter.process(audio, sr)
    print("  [Not implemented yet - skipping]")
    
    # ============================================================
    # STEP 4: FORMANT SHIFT (placeholder)
    # ============================================================
    print("\n" + "="*50)
    print("STEP 4: Formant Shift")
    print("="*50)
    
    # TODO: Add formant shifting
    # formant_shifter = FormantShifter(shift_factor=0.9)
    # audio = formant_shifter.process(audio, sr)
    print("  [Not implemented yet - skipping]")
'''