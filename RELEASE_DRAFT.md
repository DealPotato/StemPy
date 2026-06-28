# StemPy v1.0.0

StemPy's first full release turns single-track Clone Hero songs into local
multitrack charts using Demucs, RoFormer, MDX, and other Audio Separator models.

## Highlights

- **Easy first launch:** `Launch StemPy.bat` creates a private `.venv`, installs
  the CPU or NVIDIA GPU runtime, and installs FFmpeg when needed.
- **EZ UI:** scan a Clone Hero library, select songs, and use Fast, Balanced, or
  Quality presets.
- **Advanced UI:** assign a different installed model to guitar, rhythm, drums,
  vocals, keys, and backing audio.
- **Model browser:** search, filter, and download models from the Audio Separator
  catalog.
- **Safer replacement:** source backups, per-song staging, and automatic rollback
  if installation fails.
- **Faster batches:** real-time logs, optimized scanning, CUDA autocast, and one
  inference pass when several stems share the same multi-stem model.
- **Persistent setup:** StemPy remembers folders, UI mode, options, model choices,
  and custom presets.

## Installation

1. Download `StemPy-v1.0.0-windows-x64.zip` below.
2. Extract the complete ZIP to a writable folder.
3. Double-click `Launch StemPy.bat`.
4. Approve the one-time runtime installation.

The first setup can download several GB. An NVIDIA GPU is recommended; CPU mode
is supported but considerably slower.

## Important Notes

- Process one or two test songs first.
- Verify the generated stems in Clone Hero before deleting `StemPy Backup`.
- Do not interrupt the first runtime installation or a model download.
- Models are downloaded separately and may have their own license terms.
- Windows 10 and Windows 11 x64 are the supported release platforms.

## Reporting Problems

Use the bug report template and include the StemPy version, Windows version,
GPU, selected preset/model, reproduction steps, and relevant final log lines.
Do not upload copyrighted audio or unredacted private filesystem paths.

## License And Credits

StemPy source code is MIT licensed. Third-party runtimes and AI models retain
their own licenses. See `THIRD_PARTY_NOTICES.md` in the repository.
