"""
MediaFlow — URL input bar widget.
Large URL field with Paste / Analyze buttons.
"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QApplication,
)


class UrlBar(QWidget):
    """URL entry bar with Paste and Analyze buttons."""

    analyze_requested = Signal(str)   # emitted with the URL string

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        from ui.widgets.animated_button import AnimatedButton

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Rechercher ou coller le lien YouTube ici")
        self.url_input.setMinimumHeight(48)
        self.url_input.setClearButtonEnabled(True)
        self.url_input.returnPressed.connect(self._on_analyze)
        layout.addWidget(self.url_input, stretch=1)

        self.paste_btn = AnimatedButton("📋  Coller")
        self.paste_btn.setColors("#f1f3f5", "#e2e6ea", "#212529")
        self.paste_btn.setMinimumHeight(48)
        self.paste_btn.setMinimumWidth(100)
        self.paste_btn.clicked.connect(self._on_paste)
        self.paste_btn.setToolTip("Coller le contenu du presse-papiers")
        layout.addWidget(self.paste_btn)

        self.analyze_btn = AnimatedButton("Convertir")
        self.analyze_btn.setColors("#e53935", "#c62828", "#ffffff")
        self.analyze_btn.setMinimumHeight(48)
        self.analyze_btn.setMinimumWidth(140)
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.analyze_btn.setToolTip("Analyser le lien pour récupérer les formats disponibles")
        layout.addWidget(self.analyze_btn)

    def _on_paste(self) -> None:
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self.url_input.setText(text)

    def _on_analyze(self) -> None:
        url = self.url_input.text().strip()
        self.analyze_requested.emit(url)

    def get_url(self) -> str:
        return self.url_input.text().strip()

    def set_enabled(self, enabled: bool) -> None:
        self.url_input.setEnabled(enabled)
        self.paste_btn.setEnabled(enabled)
        self.analyze_btn.setEnabled(enabled)

    def set_analyzing(self, analyzing: bool) -> None:
        """Visual feedback while analysis is running."""
        if analyzing:
            self.analyze_btn.setText("⏳  Analyse…")
            self.analyze_btn.setEnabled(False)
            self.url_input.setEnabled(False)
            self.paste_btn.setEnabled(False)
        else:
            self.analyze_btn.setText("🔍  Analyser")
            self.analyze_btn.setEnabled(True)
            self.url_input.setEnabled(True)
            self.paste_btn.setEnabled(True)
