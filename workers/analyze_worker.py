"""
MediaFlow — Background analysis worker.
Runs URL analysis in a QThread to avoid UI freezes.
"""

import logging
from PySide6.QtCore import QThread, Signal

from core.analyzer import Analyzer, MediaInfo

log = logging.getLogger("mediaflow")


class AnalyzeWorker(QThread):
    """Runs Analyzer.analyze() in a background thread."""

    finished = Signal(object)     # MediaInfo
    error = Signal(str)           # error message

    def __init__(self, url: str, ffmpeg_path: str | None = None) -> None:
        super().__init__()
        self._url = url
        self._ffmpeg = ffmpeg_path

    def run(self) -> None:
        try:
            analyzer = Analyzer(ffmpeg_path=self._ffmpeg)
            info = analyzer.analyze(self._url)
            self.finished.emit(info)
        except (ValueError, RuntimeError) as exc:
            self.error.emit(str(exc))
        except Exception as exc:
            log.exception("Erreur inattendue pendant l'analyse")
            self.error.emit(f"Erreur inattendue : {exc}")
