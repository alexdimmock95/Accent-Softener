# Changelog

All notable changes to the Accent Softener project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- README.md with comprehensive project documentation
- Complete file structure documentation and module descriptions
- Paused progress on formant shifter module; formant shifting alone does not modify vowel pronunciation and is a more rigorous body of work I will return to after fleshing out the remaining modules.

---

## [0.2.0] — 2025-12-24

### Added
- **FormantShifter class** — DSP module for formant shifting and accent softening
- **Formant shifting integration** into demo pipeline
- Unit tests for formant shifting functionality
- Updated demo to showcase full accent softening pipeline

### Changed
- Enhanced demo.py to demonstrate end-to-end formant modification
- Improved test coverage for DSP transformations

---

## [0.1.2] — 2025-12-24

### Added
- **ASR phoneme timestamp extraction** — Implemented phoneme-level timing from Whisper
- ASR wrapper class for audio transcription with alignment data
- Unit tests for ASR module with phoneme verification
- phoneme_output.json output format for ASR results

### Changed
- Updated demo to include ASR phoneme extraction
- Enhanced ASRWrapper with detailed timing information

---

## [0.1.1] — 2025-12-14

### Added
- **ASRWrapper class** — Wrapper around Whisper for audio transcription
- Unit tests for ASR wrapper functionality
- Initial implementation of phoneme extraction from ASR output

---

## [0.1.0] — 2025-12-12

### Added
- **Denoiser module** — Audio denoising functionality with noise suppression
- **Overlap-add reconstruction** — Seamless audio stitching with overlap handling
- Unit tests for denoising and overlap-add modules
- Enhanced demo script with denoising pipeline
- Audio quality metrics tracking

### Changed
- Improved input streaming for better chunk handling
- Enhanced demo with full denoising + reconstruction workflow

### Features
- SNR (Signal-to-Noise Ratio) metrics calculation
- Crossfade blending for chunk reconstruction
- Minimal latency overlap-add implementation

---

## [0.0.1] — 2025-12-06

### Added
- **Initial commit** — Project scaffolding and core setup
- **FileStreamer class** — Audio file input handling with chunking
- **Basic demo script** — End-to-end pipeline demonstration
- Project structure with src/, tests/, and demo/ directories
- requirements.txt with core dependencies
- Initial test suite framework

### Features
- Audio file reading and chunking
- Basic pipeline architecture
- Test infrastructure with pytest

---

## Project Milestones

- **Week 0** — Setup & smoke test (Initial commit, FileStreamer, demo) [COMPLETE]
- **Week 1** — Input streamer (FileStreamer with chunking and buffering) [COMPLETE]
- **Week 2** — Denoiser integration (Denoiser module, SNR tests) [COMPLETE]
- **Week 3** — ASR alignment (ASRWrapper with phoneme timestamps) [COMPLETE]
- **Week 4** — Accent softening (FormantShifter DSP module) [COMPLETE]
- **Week 5** — Recombiner + metrics (Enhanced overlap-add, latency tracking) [IN PROGRESS]
- **Week 6** — Tests + CI + documentation (Full test suite, README, CI setup) [IN PROGRESS]

---

## Version History Summary

| Version | Date | Focus | Status |
|---------|------|-------|--------|
| 0.2.0 | Dec 24, 2025 | Formant Shifting & Accent Softening DSP | Complete |
| 0.1.2 | Dec 24, 2025 | ASR Phoneme Extraction & Timing | Complete |
| 0.1.1 | Dec 14, 2025 | ASR Wrapper Implementation | Complete |
| 0.1.0 | Dec 12, 2025 | Denoising & Overlap-Add Reconstruction | Complete |
| 0.0.1 | Dec 6, 2025 | Initial Project Setup & FileStreamer | Complete |

---

## Development Timeline

**Dec 6** — Project initialization with FileStreamer and basic demo  
**Dec 12** — Denoiser and overlap-add reconstruction added  
**Dec 14** — ASR wrapper implementation for transcription  
**Dec 24** — ASR phoneme timing extraction and FormantShifter DSP module  
**Jan 26, 2026** — README and project documentation completed

---

## Next Steps

- [ ] Enhanced metrics tracking and latency profiling
- [ ] Real-time microphone input streaming
- [ ] Advanced pitch smoothing algorithms
- [ ] Energy normalization and loudness matching
- [ ] CI/CD pipeline setup (GitHub Actions)
- [ ] Performance optimization for laptop execution
- [ ] Extended test coverage for edge cases
- [ ] Audio quality benchmarks and comparisons
