"""
MediaFlow — Persistent settings manager.
Stores user preferences as JSON in the local app data directory.
"""

import json
import os
from pathlib import Path
from typing import Any


_DEFAULTS: dict[str, Any] = {
    "output_dir": str(Path.home() / "Downloads"),
    "last_mode": "video",               # "video" | "audio"
    "preferred_video_ext": "mp4",
    "preferred_audio_format": "mp3",
    "preferred_audio_bitrate": "192",
    "open_folder_after": False,
    "download_thumbnail": False,
    "download_subtitles": False,
    "embed_metadata": True,
    "overwrite_existing": False,
    "ffmpeg_path": "",                   # empty = rely on PATH
    "window_width": 1060,
    "window_height": 780,
}


class Settings:
    """Thread-safe, JSON-backed settings store."""

    def __init__(self) -> None:
        self._dir = Path(os.getenv("APPDATA", Path.home())) / "UniversalDownloader"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "settings.json"
        self._data: dict[str, Any] = dict(_DEFAULTS)
        self._load()

    # -- public API ----------------------------------------------------------

    def get(self, key: str, fallback: Any = None) -> Any:
        return self._data.get(key, fallback if fallback is not None else _DEFAULTS.get(key))

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._save()

    def get_all(self) -> dict[str, Any]:
        return dict(self._data)

    def reset(self) -> None:
        self._data = dict(_DEFAULTS)
        self._save()

    @property
    def data_dir(self) -> Path:
        return self._dir

    # -- internals -----------------------------------------------------------

    def _load(self) -> None:
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                if isinstance(stored, dict):
                    self._data.update(stored)
            except (json.JSONDecodeError, OSError):
                pass  # fall back to defaults silently

    def _save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, ensure_ascii=False)
        except OSError:
            pass  # non-critical — settings will be lost on next launch
