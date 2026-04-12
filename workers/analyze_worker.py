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
            msg = str(exc)
            if "Failed to extract any player response" in msg:
                self.error.emit(
                    "Échec YouTube : yt-dlp ne parvient pas à extraire la réponse du player.\n"
                    "Solutions : 1) Mettez à jour yt-dlp (pip install -U yt-dlp)\n"
                    "2) Exportez vos cookies YouTube et placez-les dans cookies.txt\n"
                    "3) Réessayez dans quelques minutes."
                )
            else:
                self.error.emit(msg)
        except Exception as exc:
            log.exception("Erreur inattendue pendant l'analyse")
            self.error.emit(f"Erreur inattendue : {exc}")
