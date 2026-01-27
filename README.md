# Accent Softener

A near-real-time audio pipeline for accent softening that combines noise suppression, ASR alignment, and linguistically-informed DSP processing to subtly modify speech characteristics.

## Project Overview

This project builds a modular, laptop-friendly audio processing pipeline that:
- Accepts microphone or file input
- Performs lightweight noise suppression
- Uses ASR for phoneme alignment
- Applies DSP-based accent softening (formant nudges, pitch smoothing, energy normalization)
- Stitches output with minimal drift
- Includes comprehensive testing and metrics tracking

## Project Structure

### Root Level Files

- **[README.md](README.md)** — This file; project documentation
- **[requirements.txt](requirements.txt)** — Python dependencies (numpy, scipy, soundfile, torch, whisper, librosa, pytest, etc.)

### Source Code (`src/`)

Core modules implementing the audio processing pipeline:

- **[asr.py](src/asr.py)** — Automatic Speech Recognition integration using Whisper for phoneme/word alignment and transcription
- **[denoiser.py](src/denoiser.py)** — Audio denoising module (RNNoise or torchaudio-based noise suppression)
- **[formant_shifter.py](src/formant_shifter.py)** — DSP module for formant shifting and spectral modification (accent softening)
- **[input_streamer.py](src/input_streamer.py)** — Real-time audio input handling with chunking, buffering, and overlap management
- **[overlap_add.py](src/overlap_add.py)** — Overlap-add reconstruction for seamless audio stitching with crossfade handling
- **[__pycache__/](__pycache__)** — Python bytecode cache (auto-generated)

### Tests (`tests/`)

Comprehensive test suite with pytest:

- **[test_asr.py](tests/test_asr.py)** — Unit tests for ASR module (phoneme extraction, timing accuracy)
- **[test_denoiser.py](tests/test_denoiser.py)** — Tests for denoising module (SNR metrics, audio quality)
- **[test_formant_shifting.py](tests/test_formant_shifting.py)** — Tests for formant modification DSP (frequency response, artifact detection)
- **[test_phonemise.py](tests/test_phonemise.py)** — Tests for phoneme-level processing and alignment
- **[test_streamer.py](tests/test_streamer.py)** — Tests for input streaming (jitter handling, buffering, chunking)
- **[test_voice_transformer.py](tests/test_voice_transformer.py)** - Tests for applying voice transformations based on F0 (fundamental frequency), SP (spectral envelope), and AP (aperiodicity)

### Demo (`demo/`)

- **[demo.py](demo.py)** — Demo script showcasing end-to-end pipeline usage (file or mic input, output playback)

### Audio Data (`audio_files/`)

Directory structure for managing audio input/output:

- **`input/`** — Input audio files for processing
  - **`temp_file_asr/`** — Temporary files for ASR processing
- **`output/`** — Final processed audio output
- **`spectrograms/`** — Spectrogram visualizations and analysis plots
- **`temp/`** — General temporary processing files

## Dependencies

Key Python packages (see [requirements.txt](requirements.txt)):

- **Audio I/O**: soundfile, sounddevice
- **DSP**: numpy, scipy, librosa, resampy, pyworld
- **ASR**: openai-whisper
- **ML Runtime**: onnxruntime
- **Testing**: pytest, psutil

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests:**
   ```bash
   pytest tests/
   ```

3. **Run the demo:**
   ```bash
   python demo/demo.py
   ```

## Architecture

The pipeline follows a modular, streaming-first design:

1. **Input Streaming** → Chunks and buffers audio from file or microphone
2. **Denoising** → Suppresses background noise while preserving speech
3. **ASR Alignment** → Extracts phoneme-level timing for precision modification
4. **Accent Softening** → Applies formant, pitch, and energy adjustments via DSP
5. **Overlap-Add Reconstruction** → Stitches chunks with minimal artifacts