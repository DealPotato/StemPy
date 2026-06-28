# Contributing

Bug reports, focused fixes, documentation improvements, and tested feature
proposals are welcome.

## Before Opening An Issue

- Use the newest release.
- Reproduce the problem with one song where possible.
- Keep the `StemPy Backup` folder until the problem is understood.
- Remove personal paths or unrelated song information from logs.

## Development

Use Python 3.12 and a local virtual environment.

```powershell
py -3.12 setup_runtime.py
.venv\Scripts\python.exe main.py
```

Keep changes scoped and test both EZ and Advanced workflows when modifying the
scanner, presets, model routing, encoding, or file replacement behavior.

## Pull Requests

- Explain the user-facing behavior being changed.
- Include reproduction and verification steps.
- Do not commit `.venv`, models, logs, settings, backups, or generated stems.
- Do not bundle copyrighted song audio or AI models.

By contributing, you agree that your contribution may be distributed under the
project's MIT License.
