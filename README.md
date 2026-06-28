# StemPy

Local AI stem separation and Clone Hero multitrack automation for Windows.

StemPy scans a Clone Hero song library, finds songs that still use a single
audio track, separates that track with Demucs or Audio Separator models, and
installs the results using Clone Hero-compatible filenames. Processing happens
locally on your computer.

> **Important:** Start with a small test selection and verify the generated
> stems in Clone Hero before deleting backups.

## Features

- EZ UI with Fast, Balanced, and Quality presets.
- Advanced UI with a different model selectable for each output stem.
- Searchable Audio Separator model catalog with in-app downloads.
- NVIDIA CUDA acceleration when supported, with CPU fallback.
- Automatic Python 3.12, `.venv`, dependency, and FFmpeg setup on Windows.
- Recursive Clone Hero library scanning with processed-song detection.
- Real-time model and encoding logs.
- Per-song source backups before replacement.
- Transactional file installation with rollback on failure.
- Persistent folders, UI mode, model selections, options, and custom presets.
- Batch processing with continue-on-error support.

## Requirements

- Windows 10 or Windows 11, 64-bit.
- An internet connection for first-time setup and model downloads.
- Several GB of free disk space for the runtime and AI models.
- An NVIDIA GPU is recommended. CPU processing is supported but much slower.

## Quick Start

1. Download the release ZIP and extract it to a normal writable folder.
2. Double-click `Launch StemPy.bat`.
3. Approve the one-time runtime installation.
4. Select the root of your Clone Hero Songs folder.
5. Scan, select a small test group, choose a preset, and start processing.
6. Test the generated stems in Clone Hero before deleting backups.

The launcher installs Python 3.12 and FFmpeg when required, creates a private
`.venv` inside the StemPy folder, detects NVIDIA hardware, installs the matching
dependencies, and opens StemPy. Later launches reuse that environment.

If a component becomes missing or damaged, use **Install / Repair Runtime** in
the Runtime Check panel.

## EZ And Advanced UI

| Mode | Intended use |
| --- | --- |
| EZ UI | Pick songs and use a tested Fast, Balanced, or Quality preset. |
| Advanced UI | Enable individual stems and choose an installed model for each one. |

In Advanced UI, open **Browse & Download Models** to search the Audio Separator
catalog, filter by output stem, and install a model. When several selected stems
use the same multi-stem model, StemPy runs that model once per song and reuses
its outputs.

Custom Advanced presets can be saved, imported, and exported as JSON files.

## Clone Hero Output Mapping

| Separated source | Clone Hero filename |
| --- | --- |
| Guitar | `guitar.<format>` |
| Bass | `rhythm.<format>` |
| Drums | `drums.<format>` |
| Vocals | `vocals.<format>` |
| Piano / Keys | `keys.<format>` |
| Other / Backing | `song.<format>` |

The original source track is copied to a `StemPy Backup` folder before StemPy
replaces song audio. Installation is staged inside the song folder and rolled
back if a file operation fails.

## Project Data

- `.venv/`: private Python runtime; safe to recreate.
- `models/`: built-in and downloaded AI models.
- `data/settings.json`: local UI settings.
- `data/presets/`: custom Advanced presets.
- `data/logs/`: local diagnostic logs, which may contain filesystem paths.
- `data/temp/`: temporary processing files.

The runtime, models, logs, settings, and temporary files are excluded from Git.

## Development

Python 3.12 is the supported development version.

```powershell
py -3.12 setup_runtime.py
.venv\Scripts\python.exe main.py
```

The public release path is `Launch StemPy.bat`, which uses `setup_runtime.py`
to create and repair the isolated runtime. `requirements.txt` is provided as a
reference; on NVIDIA systems, use the runtime setup so PyTorch is installed
from the CUDA 12.4 package index before Demucs.

## Troubleshooting

- **CUDA is not detected:** update the NVIDIA driver, then use Runtime Repair.
- **A model does not appear:** refresh the model catalog and confirm that the
  model supports the stem selected in Advanced UI.
- **Processing fails:** keep the backup, open `data/logs`, and include the final
  relevant lines when reporting the issue.
- **The application closes unexpectedly:** attach the newest
  `data/logs/crash_*.log` file to a bug report.

## Privacy And Network Access

StemPy has no telemetry and does not upload song audio. Network access is used
only for runtime installation, package downloads, the model catalog, and model
downloads. See [PRIVACY.md](PRIVACY.md) for details.

## Legal Notice

Only process audio you are legally permitted to modify. Downloaded AI models
may have licenses or usage conditions separate from StemPy. No AI models or
third-party runtime packages are included in this source repository.

StemPy is an independent community project and is not affiliated with or
endorsed by Clone Hero, Ultimate Vocal Remover, or their developers.

## Credits

StemPy builds on the work of Audio Separator, Ultimate Vocal Remover, Demucs,
PyTorch, ONNX Runtime, FFmpeg, and Qt for Python. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

StemPy source code is released under the [MIT License](LICENSE). Third-party
software and downloaded models remain subject to their own licenses.
