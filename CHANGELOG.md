# Changelog

All notable changes to StemPy will be documented in this file.

## [0.1.0-beta.1] - 2026-06-28

### Added

- EZ UI with Fast, Balanced, and Quality separation presets.
- Advanced UI with per-stem model selection and custom presets.
- Searchable Audio Separator model catalog and model downloads.
- Automatic Windows runtime setup and in-app runtime repair.
- Clone Hero library scanning, song filtering, and batch selection.
- Real-time subprocess logs and crash diagnostics.
- Backup creation and bulk backup deletion.
- Clone Hero output encoding and stem filename mapping.
- Transactional installation with rollback after file-operation failures.
- Persistent application settings and remembered model selections.

### Optimized

- Single-pass folder scanning with one `song.ini` read per song.
- Shared inference when multiple stems use the same multi-stem model.
- CUDA autocast option and automatic CPU fallback.

### Known Limitations

- Windows is the supported release platform.
- Initial runtime setup and model downloads can require several GB.
- AI separation quality depends on the selected model and source material.
- This beta still needs testing across a wider range of Windows systems.
