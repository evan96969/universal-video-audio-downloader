"""
MediaFlow — Media info card widget.
Displays title, platform, duration, uploader and thumbnail.
"""

import logging
from io import BytesIO

import requests
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy,
)

from core.analyzer import MediaInfo

log = logging.getLogger("mediaflow")


class ThumbnailLoader(QThread):
    """Fetches a thumbnail image in the background."""
    loaded = Signal(QPixmap)

    def __init__(self, url: str) -> None:
        super().__init__()
        self._url = url

    def run(self) -> None:
        try:
            resp = requests.get(self._url, timeout=10)
            resp.raise_for_status()
            img = QImage()
            img.loadFromData(resp.content)
            if not img.isNull():
                pix = QPixmap.fromImage(img)
                self.loaded.emit(pix)
        except Exception:
            log.debug("Impossible de charger la miniature.")


class MediaCard(QWidget):
    """Card showing media metadata after successful analysis."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._loader: ThumbnailLoader | None = None
        self._build()
        self.hide()

    def _build(self) -> None:
        self.setProperty("class", "card")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)

        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(QSize(200, 112))
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet(
            "background-color: #22222e; border-radius: 8px;"
        )
        self.thumb_label.setText("🎬")
        self.thumb_label.setScaledContents(False)
        outer.addWidget(self.thumb_label)

        # Info column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        self.title_label = QLabel("—")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #e8e8ed;"
        )
        info_layout.addWidget(self.title_label)

        self.platform_label = QLabel("")
        self.platform_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #6c5ce7;"
        )
        info_layout.addWidget(self.platform_label)

        details_layout = QHBoxLayout()
        details_layout.setSpacing(16)

        self.uploader_label = QLabel("")
        self.uploader_label.setStyleSheet("font-size: 12px; color: #8b8b9e;")
        details_layout.addWidget(self.uploader_label)

        self.duration_label = QLabel("")
        self.duration_label.setStyleSheet("font-size: 12px; color: #8b8b9e;")
        details_layout.addWidget(self.duration_label)

        details_layout.addStretch()
        info_layout.addLayout(details_layout)

        self.formats_count_label = QLabel("")
        self.formats_count_label.setStyleSheet("font-size: 11px; color: #5c5c72;")
        info_layout.addWidget(self.formats_count_label)

        info_layout.addStretch()
        outer.addLayout(info_layout, stretch=1)

    def set_media(self, media: MediaInfo) -> None:
        """Populate the card with analysis results."""
        self.title_label.setText(media.title)
        self.platform_label.setText(f"📡  {media.platform}")

        if media.uploader:
            self.uploader_label.setText(f"👤  {media.uploader}")
            self.uploader_label.show()
        else:
            self.uploader_label.hide()

        if media.duration is not None:
            self.duration_label.setText(f"⏱  {media.duration_str}")
            self.duration_label.show()
        else:
            self.duration_label.hide()

        n = len(media.formats)
        self.formats_count_label.setText(f"{n} format(s) disponible(s)")

        # Load thumbnail
        self.thumb_label.setText("🎬")
        if media.thumbnail_url:
            self._loader = ThumbnailLoader(media.thumbnail_url)
            self._loader.loaded.connect(self._set_thumb)
            self._loader.start()

        self.show()

    def _set_thumb(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            self.thumb_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.thumb_label.setPixmap(scaled)

    def clear(self) -> None:
        """Reset the card to blank state."""
        self.title_label.setText("—")
        self.platform_label.setText("")
        self.uploader_label.setText("")
        self.duration_label.setText("")
        self.formats_count_label.setText("")
        self.thumb_label.setPixmap(QPixmap())
        self.thumb_label.setText("🎬")
        self.hide()
