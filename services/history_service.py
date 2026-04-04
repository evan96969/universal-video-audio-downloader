"""
MediaFlow — Download history service.
Stores recent downloads in a JSON file.
"""

import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict, field
from pathlib import Path

log = logging.getLogger("mediaflow")

MAX_HISTORY = 100


@dataclass
class HistoryEntry:
    title: str
    url: str
    filepath: str
    date: str
    status: str              # "success" | "error"
    platform: str = ""
    mode: str = ""           # "video" | "audio"


class HistoryService:
    """Manages a JSON-backed list of recent downloads."""

    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / "history.json"
        self._entries: list[HistoryEntry] = []
        self._load()

    def add(
        self,
        title: str,
        url: str,
        filepath: str,
        status: str,
        platform: str = "",
        mode: str = "",
    ) -> None:
        entry = HistoryEntry(
            title=title,
            url=url,
            filepath=filepath,
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            status=status,
            platform=platform,
            mode=mode,
        )
        self._entries.insert(0, entry)
        if len(self._entries) > MAX_HISTORY:
            self._entries = self._entries[:MAX_HISTORY]
        self._save()
        log.debug("Historique mis à jour : %s", title)

    def get_all(self) -> list[HistoryEntry]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._save()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self._entries = [HistoryEntry(**e) for e in data]
        except Exception:
            self._entries = []

    def _save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump([asdict(e) for e in self._entries], fh,
                          indent=2, ensure_ascii=False)
        except OSError:
            pass
