"""
MediaFlow — Download history panel.
Shows recent downloads in a table-like list.
"""

import os
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QMessageBox,
)

from services.history_service import HistoryService, HistoryEntry


class HistoryPanel(QWidget):
    """Displays the recent download history."""

    def __init__(self, history: HistoryService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._history = history
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # Header
        header = QHBoxLayout()
        title = QLabel("📜  Historique récent")
        title.setStyleSheet("font-size: 13px; font-weight: 600; color: #8b8b9e;")
        header.addWidget(title)
        header.addStretch()

        clear_btn = QPushButton("Effacer")
        clear_btn.setFixedHeight(28)
        clear_btn.setStyleSheet("font-size: 11px;")
        clear_btn.clicked.connect(self._clear)
        header.addWidget(clear_btn)
        root.addLayout(header)

        # Scroll area for entries
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._container = QWidget()
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll)

    def refresh(self) -> None:
        """Reload history entries from service."""
        # Clear current items
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self._history.get_all()
        if not entries:
            empty = QLabel("Aucun téléchargement récent")
            empty.setStyleSheet("color: #5c5c72; font-size: 12px; padding: 12px;")
            empty.setAlignment(Qt.AlignCenter)
            self._list_layout.insertWidget(0, empty)
            return

        for entry in entries:
            card = self._make_entry_card(entry)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)

    def _make_entry_card(self, entry: HistoryEntry) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: #1c1c26; border: 1px solid #2a2a38; "
            "border-radius: 6px; padding: 8px 12px; }"
        )
        layout = QHBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # Status icon
        icon = "✅" if entry.status == "success" else "❌"
        icon_label = QLabel(icon)
        icon_label.setFixedWidth(20)
        layout.addWidget(icon_label)

        # Info column
        info = QVBoxLayout()
        info.setSpacing(2)

        title = QLabel(entry.title)
        title.setStyleSheet("font-size: 12px; font-weight: 600; color: #e8e8ed;")
        title.setWordWrap(True)
        info.addWidget(title)

        detail_parts = []
        if entry.platform:
            detail_parts.append(entry.platform)
        if entry.mode:
            detail_parts.append(entry.mode)
        detail_parts.append(entry.date)
        detail = QLabel(" • ".join(detail_parts))
        detail.setStyleSheet("font-size: 11px; color: #5c5c72;")
        info.addWidget(detail)

        layout.addLayout(info, stretch=1)

        # Open folder button
        if entry.status == "success" and entry.filepath:
            open_btn = QPushButton("📂")
            open_btn.setFixedSize(28, 28)
            open_btn.setToolTip("Ouvrir le dossier")
            filepath = entry.filepath
            open_btn.clicked.connect(lambda checked, fp=filepath: self._open_folder(fp))
            layout.addWidget(open_btn)

        return card

    def _open_folder(self, filepath: str) -> None:
        folder = os.path.dirname(filepath)
        if os.path.isdir(folder):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(filepath)])
        else:
            QMessageBox.warning(self, "Dossier introuvable",
                                f"Le dossier n'existe plus :\n{folder}")

    def _clear(self) -> None:
        self._history.clear()
        self.refresh()
