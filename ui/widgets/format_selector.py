"""
MediaFlow — Format / quality selector widget.
Provides Video / Audio mode toggle and quality combo boxes.
"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QRadioButton, QButtonGroup, QGroupBox, QFrame, QSizePolicy,
)

from core.converter import AUDIO_FORMATS, AUDIO_BITRATES, LOSSLESS_FORMATS
from services.format_service import FormatItem


class FormatSelector(QWidget):
    """
    Mode toggle (Video / Audio) plus quality combo boxes.
    Emits mode_changed when user switches modes.
    """

    mode_changed = Signal(str)   # "video" | "audio"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._video_formats: list[FormatItem] = []
        self._audio_formats: list[FormatItem] = []
        self._build()
        self.hide()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # ── Mode toggle ────────────────────────────────────────────
        mode_frame = QFrame()
        mode_frame.setProperty("class", "card")
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(16, 12, 16, 12)
        mode_layout.setSpacing(20)

        mode_label = QLabel("Mode :")
        mode_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        mode_layout.addWidget(mode_label)

        self._mode_group = QButtonGroup(self)

        self._video_radio = QRadioButton("🎬  Vidéo")
        self._video_radio.setChecked(True)
        self._video_radio.setStyleSheet("font-size: 14px; font-weight: 600;")
        self._mode_group.addButton(self._video_radio, 0)
        mode_layout.addWidget(self._video_radio)

        self._audio_radio = QRadioButton("🎵  Audio uniquement")
        self._audio_radio.setStyleSheet("font-size: 14px; font-weight: 600;")
        self._mode_group.addButton(self._audio_radio, 1)
        mode_layout.addWidget(self._audio_radio)

        mode_layout.addStretch()
        root.addWidget(mode_frame)

        self._mode_group.idToggled.connect(self._on_mode_toggled)

        # ── Video quality section ──────────────────────────────────
        self._video_section = QGroupBox("Qualité Vidéo")
        vs_layout = QVBoxLayout(self._video_section)

        self._video_combo = QComboBox()
        self._video_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._video_combo.setMinimumHeight(38)
        vs_layout.addWidget(self._video_combo)

        self._video_info = QLabel("")
        self._video_info.setProperty("class", "muted")
        vs_layout.addWidget(self._video_info)

        root.addWidget(self._video_section)

        # ── Audio quality section ──────────────────────────────────
        self._audio_section = QGroupBox("Qualité Audio")
        as_layout = QVBoxLayout(self._audio_section)

        # Source stream
        src_label = QLabel("Flux source :")
        src_label.setStyleSheet("font-weight: 600; font-size: 12px; color: #8b8b9e;")
        as_layout.addWidget(src_label)

        self._audio_source_combo = QComboBox()
        self._audio_source_combo.setMinimumHeight(36)
        as_layout.addWidget(self._audio_source_combo)

        # Output format
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(12)

        fmt_col = QVBoxLayout()
        fmt_lbl = QLabel("Format de sortie :")
        fmt_lbl.setStyleSheet("font-weight: 600; font-size: 12px; color: #8b8b9e;")
        fmt_col.addWidget(fmt_lbl)
        self._audio_fmt_combo = QComboBox()
        self._audio_fmt_combo.setMinimumHeight(36)
        for af in AUDIO_FORMATS:
            self._audio_fmt_combo.addItem(f"{af['label']}  —  {af['description']}", af["id"])
        self._audio_fmt_combo.currentIndexChanged.connect(self._on_audio_fmt_changed)
        fmt_col.addWidget(self._audio_fmt_combo)
        fmt_row.addLayout(fmt_col, stretch=1)

        br_col = QVBoxLayout()
        br_lbl = QLabel("Qualité :")
        br_lbl.setStyleSheet("font-weight: 600; font-size: 12px; color: #8b8b9e;")
        br_col.addWidget(br_lbl)
        self._audio_br_combo = QComboBox()
        self._audio_br_combo.setMinimumHeight(36)
        for ab in AUDIO_BITRATES:
            self._audio_br_combo.addItem(ab["label"], ab["id"])
        # default to 192 kbps
        self._audio_br_combo.setCurrentIndex(2)
        br_col.addWidget(self._audio_br_combo)
        fmt_row.addLayout(br_col, stretch=1)

        as_layout.addLayout(fmt_row)

        self._audio_note = QLabel("")
        self._audio_note.setProperty("class", "muted")
        self._audio_note.setWordWrap(True)
        as_layout.addWidget(self._audio_note)

        root.addWidget(self._audio_section)
        self._audio_section.hide()

    # ── Public API ─────────────────────────────────────────────────

    def populate_video(self, formats: list[FormatItem]) -> None:
        self._video_formats = formats
        self._video_combo.clear()
        if not formats:
            self._video_combo.addItem("Aucun format vidéo disponible")
            self._video_info.setText("")
            return
        for f in formats:
            self._video_combo.addItem(f.label, f.format_id)
        self._video_info.setText(f"{len(formats)} format(s) vidéo disponible(s)")

    def populate_audio(self, formats: list[FormatItem]) -> None:
        self._audio_formats = formats
        self._audio_source_combo.clear()
        # Add "best auto" option
        self._audio_source_combo.addItem("🔄  Meilleure qualité disponible (auto)", "__best__")
        for f in formats:
            self._audio_source_combo.addItem(f.label, f.format_id)

    def get_mode(self) -> str:
        return "audio" if self._audio_radio.isChecked() else "video"

    def set_mode(self, mode: str) -> None:
        if mode == "audio":
            self._audio_radio.setChecked(True)
        else:
            self._video_radio.setChecked(True)
        self._update_sections()

    def get_selected_video_format(self) -> FormatItem | None:
        idx = self._video_combo.currentIndex()
        if 0 <= idx < len(self._video_formats):
            return self._video_formats[idx]
        return None

    def get_selected_audio_source(self) -> FormatItem | None:
        data = self._audio_source_combo.currentData()
        if data == "__best__" or data is None:
            return None  # let yt-dlp pick best
        for f in self._audio_formats:
            if f.format_id == data:
                return f
        return None

    def get_audio_output_format(self) -> str:
        return self._audio_fmt_combo.currentData() or "mp3"

    def get_audio_bitrate(self) -> str:
        return self._audio_br_combo.currentData() or "192"

    def clear(self) -> None:
        self._video_formats.clear()
        self._audio_formats.clear()
        self._video_combo.clear()
        self._audio_source_combo.clear()
        self._video_info.setText("")
        self._audio_note.setText("")
        self.hide()

    def show_populated(self) -> None:
        self._update_sections()
        self.show()

    # ── Internals ──────────────────────────────────────────────────

    def _on_mode_toggled(self, id_: int, checked: bool) -> None:
        if checked:
            self._update_sections()
            self.mode_changed.emit(self.get_mode())

    def _update_sections(self) -> None:
        if self.get_mode() == "video":
            self._video_section.show()
            self._audio_section.hide()
        else:
            self._video_section.hide()
            self._audio_section.show()
            self._on_audio_fmt_changed()

    def _on_audio_fmt_changed(self) -> None:
        fmt = self.get_audio_output_format()
        if fmt in LOSSLESS_FORMATS:
            self._audio_br_combo.setEnabled(False)
            self._audio_note.setText(
                "ℹ️  Format sans perte — le bitrate ne s'applique pas. "
                "La qualité dépend directement du flux source."
            )
        else:
            self._audio_br_combo.setEnabled(True)
            self._audio_note.setText(
                "ℹ️  La qualité de sortie ne peut pas dépasser celle du flux source. "
                "Un bitrate supérieur au source n'améliorera pas la qualité réelle."
            )
