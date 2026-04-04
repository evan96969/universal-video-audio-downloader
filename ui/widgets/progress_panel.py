"""
MediaFlow — Progress panel widget.
Shows download progress bar, speed, size, ETA.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame,
)

from utils.file_utils import format_filesize


class ProgressPanel(QWidget):
    """Download progress indicator with stats."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()
        self.hide()

    def _build(self) -> None:
        self.setProperty("class", "card")

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # Status text
        self._status_label = QLabel("En attente…")
        self._status_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(self._status_label)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 1000)
        self._bar.setValue(0)
        self._bar.setFixedHeight(10)
        root.addWidget(self._bar)

        # Stats row
        stats = QHBoxLayout()
        stats.setSpacing(24)

        self._pct_label = QLabel("0 %")
        self._pct_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #6c5ce7;")
        stats.addWidget(self._pct_label)

        self._size_label = QLabel("— / —")
        self._size_label.setStyleSheet("font-size: 12px; color: #8b8b9e;")
        stats.addWidget(self._size_label)

        self._speed_label = QLabel("")
        self._speed_label.setStyleSheet("font-size: 12px; color: #8b8b9e;")
        stats.addWidget(self._speed_label)

        self._eta_label = QLabel("")
        self._eta_label.setStyleSheet("font-size: 12px; color: #8b8b9e;")
        stats.addWidget(self._eta_label)

        stats.addStretch()
        root.addLayout(stats)

    # ── Public API ─────────────────────────────────────────────────

    def update_progress(
        self,
        percent: float,
        downloaded: int,
        total: int,
        speed: float,
        eta: float,
    ) -> None:
        self._bar.setValue(int(percent * 10))  # bar range is 0-1000
        self._pct_label.setText(f"{percent:.1f} %")

        if total > 0:
            self._size_label.setText(
                f"{format_filesize(downloaded)} / {format_filesize(total)}"
            )
        else:
            self._size_label.setText(format_filesize(downloaded))

        if speed and speed > 0:
            self._speed_label.setText(f"⬇  {format_filesize(speed)}/s")
        else:
            self._speed_label.setText("")

        if eta and eta > 0:
            m, s = divmod(int(eta), 60)
            self._eta_label.setText(f"⏱  {m}:{s:02d} restant")
        else:
            self._eta_label.setText("")

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def set_complete(self) -> None:
        self._bar.setValue(1000)
        self._pct_label.setText("100 %")
        self._status_label.setText("Téléchargement terminé ✓")
        self._speed_label.setText("")
        self._eta_label.setText("")
        self._pct_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #00cec9;")

    def set_error(self, msg: str) -> None:
        self._status_label.setText(f"❌  {msg}")
        self._speed_label.setText("")
        self._eta_label.setText("")
        self._pct_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #ff6b6b;")

    def reset(self) -> None:
        self._bar.setValue(0)
        self._pct_label.setText("0 %")
        self._pct_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #6c5ce7;")
        self._size_label.setText("— / —")
        self._speed_label.setText("")
        self._eta_label.setText("")
        self._status_label.setText("En attente…")
