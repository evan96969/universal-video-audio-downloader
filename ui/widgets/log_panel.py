"""
MediaFlow — Activity log panel.
Shows human-readable log entries in a scrollable text area.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLabel


class LogPanel(QWidget):
    """Scrollable log display connected to the app logger."""

    MAX_LINES = 2000

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()
        self._line_count = 0

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        header = QLabel("📋  Journal d'activité")
        header.setStyleSheet("font-size: 13px; font-weight: 600; color: #8b8b9e;")
        root.addWidget(header)

        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setMaximumBlockCount(self.MAX_LINES)
        self._text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._text.setMinimumHeight(120)
        root.addWidget(self._text)

    def append(self, message: str) -> None:
        """Add a log line and auto-scroll."""
        self._text.appendPlainText(message)
        # Auto-scroll to bottom
        sb = self._text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear(self) -> None:
        self._text.clear()
