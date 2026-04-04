"""
MediaFlow — Background download worker.
Runs the download + post-processing in a QThread.
"""

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.downloader import Downloader
from services.format_service import FormatItem

log = logging.getLogger("mediaflow")


class DownloadWorker(QThread):
    """Runs Downloader in a background thread with progress signals."""

    # progress(percent, downloaded, total, speed, eta)
    progress = Signal(float, int, int, float, float)
    status = Signal(str)
    finished = Signal(str)           # final file path
    error = Signal(str)              # error message

    def __init__(
        self,
        url: str,
        mode: str,                    # "video" | "audio"
        *,
        video_format: FormatItem | None = None,
        audio_source_format: FormatItem | None = None,
        audio_output_format: str = "mp3",
        audio_bitrate: str = "192",
        output_dir: str = "",
        raw_formats: list[dict] | None = None,
        ffmpeg_path: str | None = None,
        embed_metadata: bool = True,
        download_thumbnail: bool = False,
        download_subtitles: bool = False,
        overwrite: bool = False,
    ) -> None:
        super().__init__()
        self._url = url
        self._mode = mode
        self._video_format = video_format
        self._audio_source = audio_source_format
        self._audio_fmt = audio_output_format
        self._audio_br = audio_bitrate
        self._output_dir = output_dir
        self._raw_formats = raw_formats or []
        self._ffmpeg = ffmpeg_path
        self._embed_meta = embed_metadata
        self._dl_thumb = download_thumbnail
        self._dl_subs = download_subtitles
        self._overwrite = overwrite
        self._downloader: Downloader | None = None

    def cancel(self) -> None:
        if self._downloader:
            self._downloader.cancel()

    def run(self) -> None:
        try:
            self._downloader = Downloader(
                ffmpeg_path=self._ffmpeg,
                embed_metadata=self._embed_meta,
                download_thumbnail=self._dl_thumb,
                download_subtitles=self._dl_subs,
                overwrite=self._overwrite,
            )

            if self._mode == "video":
                if not self._video_format:
                    self.error.emit("Aucun format vidéo sélectionné.")
                    return
                result = self._downloader.download_video(
                    url=self._url,
                    format_item=self._video_format,
                    output_dir=self._output_dir,
                    raw_formats=self._raw_formats,
                    on_progress=self._on_progress,
                    on_status=self._on_status,
                )
            else:
                result = self._downloader.download_audio(
                    url=self._url,
                    audio_format=self._audio_fmt,
                    audio_bitrate=self._audio_br,
                    source_format=self._audio_source,
                    output_dir=self._output_dir,
                    on_progress=self._on_progress,
                    on_status=self._on_status,
                )

            self.finished.emit(str(result))

        except Exception as exc:
            msg = str(exc)
            if "annulé" in msg.lower() or "cancel" in msg.lower():
                self.status.emit("Téléchargement annulé.")
                self.error.emit("Téléchargement annulé par l'utilisateur.")
            else:
                log.exception("Erreur pendant le téléchargement")
                self.error.emit(msg)

    def _on_progress(
        self, pct: float, downloaded: int,
        total: int | None, speed: float | None, eta: float | None,
    ) -> None:
        self.progress.emit(
            pct,
            downloaded,
            total or 0,
            speed or 0,
            eta or 0,
        )

    def _on_status(self, text: str) -> None:
        self.status.emit(text)
