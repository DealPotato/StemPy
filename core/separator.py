import os
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from core.backup import create_backup, delete_backup
from core.logger import logger
from core.scanner import SongItem


@dataclass
class StemModelConfig:
    stem: str
    model_family: str  # demucs_direct | demucs | mdx | roformer | vr_arch
    model_name: str
    enabled: bool = True
    model_dir: str = ""


@dataclass
class SeparationPreset:
    name: str
    stems: list[StemModelConfig]
    device: str = "auto"  # auto | cuda | cpu
    output_format: str = "same_as_input"
    create_backup: bool = True
    continue_on_error: bool = True
    delete_backup_after_success: bool = False
    use_autocast: bool = True


@dataclass
class SeparationResult:
    song: SongItem
    success: bool
    message: str
    output_files: list[Path] = field(default_factory=list)


def create_builtin_preset(name: str) -> SeparationPreset:
    preset_name = name.lower()

    if preset_name == "fast":
        return SeparationPreset(
            name="Fast",
            stems=[
                StemModelConfig("guitar", "demucs_direct", "htdemucs"),
                StemModelConfig("rhythm", "demucs_direct", "htdemucs"),
                StemModelConfig("drums", "demucs_direct", "htdemucs"),
                StemModelConfig("vocals", "demucs_direct", "htdemucs"),
                StemModelConfig("other", "demucs_direct", "htdemucs"),
            ],
        )

    if preset_name == "quality":
        return SeparationPreset(
            name="Quality",
            stems=[StemModelConfig("all", "roformer", "BS-Roformer-SW.ckpt")],
        )

    return SeparationPreset(
        name="Balanced",
        stems=[
            StemModelConfig("guitar", "demucs_direct", "htdemucs_6s"),
            StemModelConfig("rhythm", "demucs_direct", "htdemucs_6s"),
            StemModelConfig("drums", "demucs_direct", "htdemucs_6s"),
            StemModelConfig("vocals", "demucs_direct", "htdemucs_6s"),
            StemModelConfig("other", "demucs_direct", "htdemucs_6s"),
        ],
    )


class Separator:
    def __init__(self):
        self.cancel_requested = False
        self.active_process = None
        self.job_temp_root: Path | None = None

    def _run_command_streaming(self, command: list[str], environment=None) -> int:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=creation_flags,
            env=environment,
        )
        self.active_process = process

        try:
            if process.stdout is None:
                raise RuntimeError("Could not read process output")

            for raw_line in process.stdout:
                if self.cancel_requested:
                    process.terminate()
                    raise RuntimeError("Cancelled")

                line = raw_line.strip()
                if line:
                    logger.info(line)

            return process.wait()
        finally:
            self.active_process = None

    def process_song(self, song: SongItem, preset: SeparationPreset) -> SeparationResult:
        logger.info(f"START {song.artist} - {song.title}")
        self.job_temp_root = Path("data/temp/jobs") / uuid.uuid4().hex
        self.job_temp_root.mkdir(parents=True, exist_ok=True)

        try:
            self.cancel_requested = False

            if preset.create_backup:
                self._create_backup(song)

            grouped_models = self._resolve_models(preset)
            temp_outputs = self._run_backends(song, preset, grouped_models)
            encoded_outputs = self._encode_outputs(song, preset, temp_outputs)
            final_outputs = self._replace_outputs(song, preset, encoded_outputs)

            self._cleanup(song, preset)

            if preset.delete_backup_after_success:
                delete_backup(song.folder)

            logger.success(f"DONE {song.artist} - {song.title}")

            return SeparationResult(
                song=song,
                success=True,
                message="Separation completed",
                output_files=final_outputs,
            )

        except Exception as ex:
            self._cleanup(song, preset)
            logger.error(f"FAILED {song.artist} - {song.title} | {ex}")

            return SeparationResult(
                song=song,
                success=False,
                message=str(ex),
            )
        finally:
            self.job_temp_root = None

    def process_batch(
        self,
        songs: list[SongItem],
        preset: SeparationPreset,
        progress_callback=None,
    ) -> list[SeparationResult]:
        results: list[SeparationResult] = []

        for index, song in enumerate(songs, start=1):
            if self.cancel_requested:
                logger.warning("Batch cancelled")
                break

            if progress_callback is not None:
                progress_callback(index, len(songs), song)
            logger.info(f"Processing {index}/{len(songs)}")
            result = self.process_song(song, preset)
            results.append(result)

            if not result.success and not preset.continue_on_error:
                logger.warning("Stopping batch because continue_on_error is disabled")
                break

        return results

    def _create_backup(self, song: SongItem) -> None:
        logger.info("Creating backup")
        create_backup(song.source_audio)

    def _resolve_models(self, preset: SeparationPreset) -> dict[str, list[StemModelConfig]]:
        grouped: dict[str, list[StemModelConfig]] = {}

        for stem_config in preset.stems:
            if not stem_config.enabled:
                continue

            backend = self._resolve_backend(stem_config.model_family)
            grouped.setdefault(backend, []).append(stem_config)

        logger.info(f"Resolved backends: {', '.join(grouped.keys())}")
        return grouped

    def _resolve_backend(self, model_family: str) -> str:
        if model_family == "demucs_direct":
            return "demucs_direct"

        if model_family in {"demucs", "mdx", "roformer", "vr_arch"}:
            return "audio_separator"

        raise ValueError(f"Unknown model family: {model_family}")

    def _run_backends(
        self,
        song: SongItem,
        preset: SeparationPreset,
        grouped_models: dict[str, list[StemModelConfig]],
    ) -> list[Path]:
        outputs: list[Path] = []

        for backend, stem_configs in grouped_models.items():
            if self.cancel_requested:
                raise RuntimeError("Cancelled")

            if backend == "demucs_direct":
                outputs.extend(self._run_demucs_direct(song, preset, stem_configs))
            elif backend == "audio_separator":
                outputs.extend(self._run_audio_separator(song, preset, stem_configs))
            else:
                raise ValueError(f"Unknown backend: {backend}")

        return outputs

    def _run_demucs_direct(
        self,
        song: SongItem,
        preset: SeparationPreset,
        stem_configs: list[StemModelConfig],
    ) -> list[Path]:
        logger.info("Running Demucs Direct backend")

        model_name = stem_configs[0].model_name
        device = self._resolve_device(preset.device)

        temp_output_root = self._get_job_temp_root() / "demucs"
        temp_output_root.mkdir(parents=True, exist_ok=True)

        command = [
            sys.executable,
            "-m",
            "demucs",
            "-n",
            model_name,
            "--device",
            device,
            "-o",
            str(temp_output_root),
            str(song.source_audio),
        ]

        logger.debug(" ".join(command))

        return_code = self._run_command_streaming(command)

        if return_code != 0:
            raise RuntimeError(f"Demucs failed with exit code {return_code}")

        song_output_folder = temp_output_root / model_name / song.source_audio.stem

        if not song_output_folder.exists():
            raise FileNotFoundError(f"Demucs output folder not found: {song_output_folder}")

        output_files = [
            file
            for file in song_output_folder.glob("*")
            if file.is_file()
        ]

        logger.success(f"Demucs created {len(output_files)} files")

        for file in output_files:
            logger.info(f"Output: {file}")

        return output_files

    def _run_audio_separator(
        self,
        song: SongItem,
        preset: SeparationPreset,
        stem_configs: list[StemModelConfig],
    ) -> list[Path]:
        logger.info("Running Audio Separator backend")

        outputs: list[Path] = []

        temp_output_root = self._get_job_temp_root() / "audio_separator"
        temp_output_root.mkdir(parents=True, exist_ok=True)

        audio_separator_exe = Path(sys.executable).parent / "audio-separator.exe"

        grouped_configs: dict[tuple[str, str, str], list[StemModelConfig]] = {}
        for stem_config in stem_configs:
            key = (
                stem_config.model_family,
                stem_config.model_name,
                stem_config.model_dir,
            )
            grouped_configs.setdefault(key, []).append(stem_config)

        for index, configs in enumerate(grouped_configs.values()):
            stem_config = configs[0]
            requested_stems = [config.stem for config in configs]
            logger.info(
                f"Audio Separator model: {stem_config.model_family} / "
                f"{stem_config.model_name} for {', '.join(requested_stems)}"
            )

            model_dir = self._resolve_model_dir(stem_config)
            run_output_root = temp_output_root / f"{index:02d}-model"
            run_output_root.mkdir(parents=True, exist_ok=True)
            run_all_stems = len(configs) > 1 or stem_config.stem == "all"

            command = [
                str(audio_separator_exe),
                str(song.source_audio),
                "--model_filename",
                stem_config.model_name,
                "--model_file_dir",
                str(model_dir.resolve()),
                "--output_dir",
                str(run_output_root.resolve()),
            ]

            if not run_all_stems:
                command.extend(["--single_stem", self._separator_stem_name(stem_config.stem)])
            if preset.use_autocast and preset.device != "cpu":
                command.append("--use_autocast")

            logger.debug(" ".join(command))

            environment = None
            if preset.device == "cpu":
                environment = os.environ.copy()
                environment["CUDA_VISIBLE_DEVICES"] = "-1"
            return_code = self._run_command_streaming(command, environment)

            if return_code != 0:
                raise RuntimeError(
                    f"Audio Separator failed with exit code {return_code}"
                )

            created = [
                file
                for file in run_output_root.rglob("*")
                if file.is_file()
                and file.suffix.casefold() in {".wav", ".mp3", ".flac", ".ogg"}
            ]
            if not created:
                raise RuntimeError(f"Model created no output: {stem_config.model_name}")

            if stem_config.stem == "all":
                outputs.extend(created)
                continue

            for config in configs:
                selected = self._select_requested_output(created, config.stem)
                normalized = temp_output_root / f"{config.stem}{selected.suffix.casefold()}"
                shutil.copy2(selected, normalized)
                outputs.append(normalized)

        logger.success(f"Audio Separator created {len(outputs)} files")

        for file in outputs:
            logger.info(f"Output: {file}")

        return outputs

    def _encode_outputs(
        self,
        song: SongItem,
        preset: SeparationPreset,
        temp_outputs: list[Path],
    ) -> list[Path]:
        logger.info("Encoding outputs")

        stem_map = self._map_clone_hero_stems(temp_outputs)
        if not stem_map:
            raise RuntimeError("No recognized stems were created")

        extension = self._resolve_output_extension(song, preset)
        encoded_root = self._get_job_temp_root() / "encoded"
        encoded_root.mkdir(parents=True, exist_ok=True)
        encoded_outputs: list[Path] = []

        for clone_hero_name, source in stem_map.items():
            output = encoded_root / f"{clone_hero_name}{extension}"
            logger.info(f"Encoding {source.name} -> {output.name}")

            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(source),
                "-map",
                "0:a:0",
                "-threads",
                "0",
                *self._ffmpeg_codec_args(extension),
                str(output),
            ]

            return_code = self._run_command_streaming(command)
            if return_code != 0:
                raise RuntimeError(
                    f"FFmpeg failed while encoding {clone_hero_name} "
                    f"with exit code {return_code}"
                )
            if not output.exists() or output.stat().st_size == 0:
                raise RuntimeError(f"Encoded output is missing or empty: {output}")

            encoded_outputs.append(output)

        logger.success(f"Encoded {len(encoded_outputs)} Clone Hero files")
        return encoded_outputs

    def _replace_outputs(
        self,
        song: SongItem,
        preset: SeparationPreset,
        encoded_outputs: list[Path],
    ) -> list[Path]:
        logger.info("Replacing Clone Hero files")

        if not encoded_outputs:
            raise RuntimeError("No encoded files are available to install")

        transaction_id = uuid.uuid4().hex
        transaction_root = song.folder / f".stempy-staging-{transaction_id}"
        new_root = transaction_root / "new"
        rollback_root = transaction_root / "rollback"
        new_root.mkdir(parents=True)
        rollback_root.mkdir()

        destinations = {
            encoded.name: song.folder / encoded.name for encoded in encoded_outputs
        }
        affected_paths = set(destinations.values())
        affected_paths.add(song.source_audio)
        installed: list[Path] = []
        rollback_files: dict[Path, Path] = {}

        try:
            staged_files: dict[Path, Path] = {}
            for encoded in encoded_outputs:
                staged = new_root / encoded.name
                shutil.copy2(encoded, staged)
                if staged.stat().st_size != encoded.stat().st_size:
                    raise RuntimeError(f"Could not stage complete output: {encoded.name}")
                staged_files[destinations[encoded.name]] = staged

            for existing in affected_paths:
                if not existing.exists():
                    continue
                rollback = rollback_root / existing.name
                os.replace(existing, rollback)
                rollback_files[existing] = rollback

            for destination, staged in staged_files.items():
                os.replace(staged, destination)
                installed.append(destination)
                logger.success(f"Installed: {destination}")

            return installed
        except Exception:
            for destination in installed:
                destination.unlink(missing_ok=True)
            for original, rollback in rollback_files.items():
                if rollback.exists():
                    os.replace(rollback, original)
            raise
        finally:
            shutil.rmtree(transaction_root, ignore_errors=True)

    def _cleanup(self, song: SongItem, preset: SeparationPreset) -> None:
        if self.job_temp_root is None or not self.job_temp_root.exists():
            return

        logger.info("Cleaning temporary files")
        shutil.rmtree(self.job_temp_root, ignore_errors=True)

    def _get_job_temp_root(self) -> Path:
        if self.job_temp_root is None:
            raise RuntimeError("Processing workspace is not initialized")
        return self.job_temp_root

    @staticmethod
    def _separator_stem_name(stem: str) -> str:
        names = {
            "rhythm": "Bass",
            "keys": "Piano",
            "song": "Other",
        }
        return names.get(stem, stem.title())

    def _resolve_model_dir(self, config: StemModelConfig) -> Path:
        if config.model_dir:
            path = Path(config.model_dir)
            if path.exists():
                return path

        family_root = Path("models") / config.model_family
        for candidate in family_root.rglob(config.model_name):
            if candidate.is_file():
                return candidate.parent

        builtin = family_root / "builtin"
        downloaded = family_root / "downloaded"
        if builtin.exists():
            return builtin
        return downloaded

    def _select_requested_output(self, outputs: list[Path], target: str) -> Path:
        expected = self._separator_stem_name(target).casefold()
        aliases = {expected}
        if target == "song":
            aliases.add("instrumental")

        for output in outputs:
            detected = self._detect_stem_name(output)
            if detected in aliases:
                return output
            if any(f"({alias})" in output.stem.casefold() for alias in aliases):
                return output
        return outputs[0]

    def _map_clone_hero_stems(self, outputs: list[Path]) -> dict[str, Path]:
        detected: dict[str, Path] = {}

        for output in outputs:
            stem = self._detect_stem_name(output)
            if stem is None:
                logger.warning(f"Ignoring unrecognized output: {output.name}")
                continue
            detected[stem] = output

        has_separate_guitar = "guitar" in detected
        mapped: dict[str, Path] = {}

        for stem, output in detected.items():
            if stem in {"bass", "rhythm"}:
                target = "rhythm"
            elif stem in {"piano", "keys"}:
                target = "keys"
            elif stem == "other":
                target = "song" if has_separate_guitar else "guitar"
            elif stem in {"guitar", "drums", "vocals", "song"}:
                target = stem
            else:
                continue

            mapped[target] = output
            logger.info(f"Stem mapping: {output.name} -> {target}")

        return mapped

    @staticmethod
    def _detect_stem_name(path: Path) -> str | None:
        known_stems = {
            "bass",
            "drums",
            "guitar",
            "keys",
            "other",
            "piano",
            "rhythm",
            "song",
            "vocals",
        }
        name = path.stem.lower()

        parenthesized = re.findall(r"\(([^)]+)\)", name)
        for candidate in reversed(parenthesized):
            if candidate in known_stems:
                return candidate

        if name in known_stems:
            return name

        tokens = [token for token in re.split(r"[^a-z]+", name) if token]
        for candidate in reversed(tokens):
            if candidate in known_stems:
                return candidate

        return None

    @staticmethod
    def _resolve_output_extension(song: SongItem, preset: SeparationPreset) -> str:
        if preset.output_format == "same_as_input":
            extension = song.source_audio.suffix.lower()
        else:
            extension = "." + preset.output_format.lower().lstrip(".")

        supported = {".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}
        return extension if extension in supported else ".ogg"

    @staticmethod
    def _ffmpeg_codec_args(extension: str) -> list[str]:
        codecs = {
            ".flac": ["-c:a", "flac"],
            ".m4a": ["-c:a", "aac", "-b:a", "256k"],
            ".mp3": ["-c:a", "libmp3lame", "-q:a", "2"],
            ".ogg": ["-c:a", "libvorbis", "-q:a", "6"],
            ".opus": ["-c:a", "libopus", "-b:a", "192k"],
            ".wav": ["-c:a", "pcm_s16le"],
        }
        return codecs[extension]

    def _resolve_device(self, device: str) -> str:
        if device == "cuda":
            return "cuda"

        if device == "cpu":
            return "cpu"

        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def cancel(self):
        self.cancel_requested = True
        if self.active_process is not None and self.active_process.poll() is None:
            self.active_process.terminate()
