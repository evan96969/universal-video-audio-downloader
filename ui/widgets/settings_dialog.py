"""
MediaFlow — Settings dialog.
Persistent preferences window.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QComboBox, QFileDialog, QGroupBox,
    QFormLayout, QWidget, QMessageBox,
)
import shutil
import os
from pathlib import Path

from config.settings import Settings
from core.converter import AUDIO_FORMATS, AUDIO_BITRATES
from core.ffmpeg_utils import check_ffmpeg


class SettingsDialog(QDialog):
    """Modal settings dialog."""

    settings_changed = Signal()

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Paramètres — Universal Downloader")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._build()
        self._load()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 24, 24, 24)

        # ── Output ─────────────────────────────────────────────────
        out_group = QGroupBox("Dossier de sortie")
        out_layout = QHBoxLayout(out_group)
        self._output_edit = QLineEdit()
        self._output_edit.setMinimumHeight(36)
        out_layout.addWidget(self._output_edit, stretch=1)
        browse_btn = QPushButton("Parcourir…")
        browse_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(browse_btn)
        root.addWidget(out_group)

        # ── FFmpeg ─────────────────────────────────────────────────
        ff_group = QGroupBox("FFmpeg")
        ff_layout = QVBoxLayout(ff_group)

        ff_row = QHBoxLayout()
        self._ffmpeg_edit = QLineEdit()
        self._ffmpeg_edit.setPlaceholderText("Laisser vide pour utiliser le PATH système")
        self._ffmpeg_edit.setMinimumHeight(36)
        ff_row.addWidget(self._ffmpeg_edit, stretch=1)
        ff_browse = QPushButton("Parcourir…")
        ff_browse.clicked.connect(self._browse_ffmpeg)
        ff_row.addWidget(ff_browse)
        ff_layout.addLayout(ff_row)

        self._ff_status = QLabel("")
        self._ff_status.setStyleSheet("font-size: 12px; color: #8b8b9e;")
        ff_layout.addWidget(self._ff_status)

        ff_check = QPushButton("Vérifier FFmpeg")
        ff_check.clicked.connect(self._check_ffmpeg)
        ff_layout.addWidget(ff_check)

        root.addWidget(ff_group)

        # ── Cookies / Auth ─────────────────────────────────────────
        auth_group = QGroupBox("Authentification / Cookies")
        auth_layout = QVBoxLayout(auth_group)
        auth_layout.setSpacing(8)

        cookie_desc = QLabel('Certains sites bloquent les téléchargements. Installez l\'extension "Get cookies.txt LOCALLY", que vous pouvez télécharger <a href="https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc">ici</a>, puis importez le fichier exporté.')
        cookie_desc.setOpenExternalLinks(True)
        cookie_desc.setWordWrap(True)
        cookie_desc.setStyleSheet("color: #8b8b9e; font-size: 13px;")
        auth_layout.addWidget(cookie_desc)
        
        cookie_row = QHBoxLayout()
        self._cookie_edit = QLineEdit()
        self._cookie_edit.setPlaceholderText("Chemin vers cookies.txt")
        self._cookie_edit.setMinimumHeight(36)
        cookie_row.addWidget(self._cookie_edit, stretch=1)

        cookie_browse = QPushButton("Importer…")
        cookie_browse.clicked.connect(self._browse_cookies)
        cookie_row.addWidget(cookie_browse)
        auth_layout.addLayout(cookie_row)

        self._chk_remember_cookies = QCheckBox("Se souvenir de mes cookies (ne pas redemander au démarrage)")
        auth_layout.addWidget(self._chk_remember_cookies)

        root.addWidget(auth_group)

        # ── Defaults ───────────────────────────────────────────────
        def_group = QGroupBox("Préférences par défaut")
        def_form = QFormLayout(def_group)
        def_form.setSpacing(10)

        self._pref_video_ext = QComboBox()
        self._pref_video_ext.addItems(["mp4", "mkv", "webm"])
        self._pref_video_ext.setMinimumHeight(32)
        def_form.addRow("Format vidéo préféré :", self._pref_video_ext)

        self._pref_audio_fmt = QComboBox()
        for af in AUDIO_FORMATS:
            self._pref_audio_fmt.addItem(af["label"], af["id"])
        self._pref_audio_fmt.setMinimumHeight(32)
        def_form.addRow("Format audio préféré :", self._pref_audio_fmt)

        self._pref_audio_br = QComboBox()
        for ab in AUDIO_BITRATES:
            self._pref_audio_br.addItem(ab["label"], ab["id"])
        self._pref_audio_br.setMinimumHeight(32)
        def_form.addRow("Bitrate audio préféré :", self._pref_audio_br)

        root.addWidget(def_group)

        # ── Options ────────────────────────────────────────────────
        opt_group = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_group)
        opt_layout.setSpacing(8)

        self._chk_open_folder = QCheckBox("Ouvrir le dossier après le téléchargement")
        opt_layout.addWidget(self._chk_open_folder)

        self._chk_thumbnail = QCheckBox("Télécharger la miniature")
        opt_layout.addWidget(self._chk_thumbnail)

        self._chk_subtitles = QCheckBox("Télécharger les sous-titres")
        opt_layout.addWidget(self._chk_subtitles)

        self._chk_metadata = QCheckBox("Intégrer les métadonnées dans le fichier")
        opt_layout.addWidget(self._chk_metadata)

        self._chk_overwrite = QCheckBox("Écraser les fichiers existants")
        opt_layout.addWidget(self._chk_overwrite)

        root.addWidget(opt_group)

        # ── Buttons ────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        reset_btn = QPushButton("Réinitialiser")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(reset_btn)

        save_btn = QPushButton("Enregistrer")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        root.addLayout(btn_row)

    # ── Load / Save ────────────────────────────────────────────────

    def _load(self) -> None:
        s = self._settings
        self._output_edit.setText(s.get("output_dir"))
        self._ffmpeg_edit.setText(s.get("ffmpeg_path", ""))

        idx = self._pref_video_ext.findText(s.get("preferred_video_ext", "mp4"))
        if idx >= 0:
            self._pref_video_ext.setCurrentIndex(idx)

        idx = self._pref_audio_fmt.findData(s.get("preferred_audio_format", "mp3"))
        if idx >= 0:
            self._pref_audio_fmt.setCurrentIndex(idx)

        idx = self._pref_audio_br.findData(s.get("preferred_audio_bitrate", "192"))
        if idx >= 0:
            self._pref_audio_br.setCurrentIndex(idx)

        self._chk_open_folder.setChecked(s.get("open_folder_after", False))
        self._chk_thumbnail.setChecked(s.get("download_thumbnail", False))
        self._chk_subtitles.setChecked(s.get("download_subtitles", False))
        self._chk_metadata.setChecked(s.get("embed_metadata", True))
        self._chk_overwrite.setChecked(s.get("overwrite_existing", False))
        self._cookie_edit.setText(s.get("cookie_file_path", ""))
        self._chk_remember_cookies.setChecked(s.get("remember_cookies", False))

    def _save(self) -> None:
        s = self._settings
        s.set("output_dir", self._output_edit.text())
        s.set("ffmpeg_path", self._ffmpeg_edit.text())
        s.set("preferred_video_ext", self._pref_video_ext.currentText())
        s.set("preferred_audio_format", self._pref_audio_fmt.currentData())
        s.set("preferred_audio_bitrate", self._pref_audio_br.currentData())
        s.set("open_folder_after", self._chk_open_folder.isChecked())
        s.set("download_thumbnail", self._chk_thumbnail.isChecked())
        s.set("download_subtitles", self._chk_subtitles.isChecked())
        s.set("embed_metadata", self._chk_metadata.isChecked())
        s.set("overwrite_existing", self._chk_overwrite.isChecked())
        s.set("cookie_file_path", self._cookie_edit.text() if self._chk_remember_cookies.isChecked() else "")
        s.set("remember_cookies", self._chk_remember_cookies.isChecked())
        
        # Copy to root/cookies.txt
        root_cookie = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "cookies.txt")
        src_cookie = self._cookie_edit.text().strip()
        if src_cookie and os.path.isfile(src_cookie):
            try:
                shutil.copy2(src_cookie, root_cookie)
            except Exception:
                pass
        elif not self._chk_remember_cookies.isChecked() and os.path.isfile(root_cookie):
            try:
                os.remove(root_cookie)
            except Exception:
                pass

        self.settings_changed.emit()
        self.accept()

    def _reset(self) -> None:
        self._settings.reset()
        self._load()

    # ── Browse buttons ─────────────────────────────────────────────

    def _browse_output(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Dossier de sortie", self._output_edit.text())
        if d:
            self._output_edit.setText(d)

    def _browse_cookies(self) -> None:
        f, _ = QFileDialog.getOpenFileName(
            self, "Fichier Cookie", "",
            "Texte (*.txt);;Tous (*)",
        )
        if f:
            self._cookie_edit.setText(f)

    def _browse_ffmpeg(self) -> None:
        f, _ = QFileDialog.getOpenFileName(
            self, "Emplacement de FFmpeg", "",
            "Exécutable (ffmpeg.exe ffmpeg);;Tous (*)",
        )
        if f:
            self._ffmpeg_edit.setText(f)

    def _check_ffmpeg(self) -> None:
        ok, msg = check_ffmpeg(self._ffmpeg_edit.text())
        self._ff_status.setText(msg)
        self._ff_status.setStyleSheet(
            f"font-size: 12px; color: {'#00cec9' if ok else '#ff6b6b'};"
        )
