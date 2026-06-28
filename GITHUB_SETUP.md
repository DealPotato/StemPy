# GitHub Release Setup

## Repository Metadata

**Name:** `StemPy`

**Description:**

> Local AI stem separation and Clone Hero multitrack automation for Windows.

**Suggested topics:**

`clone-hero`, `audio-separation`, `stem-separation`, `demucs`, `roformer`,
`ultimate-vocal-remover`, `python`, `pyside6`, `cuda`, `music-tools`, `windows`

**Website:** leave empty until project documentation or a release page exists.

## Recommended First Release

- Tag: `v1.0.0`
- Title: `StemPy v1.0.0`
- Set as the latest release.
- Copy the contents of `RELEASE_DRAFT.md` into the release description.
- Upload `StemPy-v1.0.0-windows-x64.zip` as the release asset.
- Do not upload `.venv`, models, logs, settings, backups, or temporary files.

## Repository Settings

- Keep the repository public if the project is intended to be open source.
- Enable Issues and Discussions.
- Add the MIT license through the existing `LICENSE` file.
- Use squash merging for small focused pull requests.
- Protect the default branch after the first stable release.

## Release Checklist

- [ ] Test first launch on a Windows machine without an existing `.venv`.
- [ ] Test runtime repair.
- [ ] Test one EZ UI song with Quality.
- [ ] Test one Advanced UI custom preset.
- [ ] Test model catalog refresh and one model download.
- [ ] Confirm backup deletion requires confirmation.
- [ ] Confirm generated stems load in Clone Hero.
- [ ] Review the ZIP and ensure no personal logs or paths are included.
