"""
Universal Downloader — Main application window.
Assembles all UI widgets and wires signals.
"""

import logging
import os
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QThread, Signal as QtSignal
from PySide6.QtGui import QIcon, QScreen
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QMessageBox, QTabWidget,
    QScrollArea, QFrame, QSplitter, QSizePolicy, QApplication,
    QProgressDialog,
)

from config.settings import Settings
from core.analyzer import MediaInfo, validate_url
from core.ffmpeg_utils import find_ffmpeg, check_ffmpeg, ensure_ffmpeg, download_ffmpeg
from services.format_service import parse_video_formats, parse_audio_formats
from services.history_service import HistoryService
from utils.logger import get_log_emitter, setup_logger
from workers.analyze_worker import AnalyzeWorker
from workers.download_worker import DownloadWorker

from ui.widgets.url_bar import UrlBar
from ui.widgets.media_card import MediaCard
from ui.widgets.format_selector import FormatSelector
from ui.widgets.progress_panel import ProgressPanel
from ui.widgets.log_panel import LogPanel
from ui.widgets.settings_dialog import SettingsDialog
from ui.widgets.history_panel import HistoryPanel

log = logging.getLogger("mediaflow")


class _FFmpegDownloadThread(QThread):
    """Background thread for downloading FFmpeg."""
    progress = QtSignal(str, int)   # (status_text, percent)
    finished = QtSignal(str)        # path to ffmpeg.exe
    error = QtSignal(str)

    def run(self):
        try:
            path = download_ffmpeg(progress_callback=self._on_progress)
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, msg: str, pct: int):
        self.progress.emit(msg, pct)


class MainWindow(QMainWindow):
    """Top-level Universal Downloader window."""

    APP_NAME = "Universal Downloader"
    VERSION = "1.0.0"

    def __init__(self) -> None:
        super().__init__()

        # Services
        self._settings = Settings()
        self._history = HistoryService(self._settings.data_dir)

        # State
        self._current_media: MediaInfo | None = None
        self._analyze_worker: AnalyzeWorker | None = None
        self._download_worker: DownloadWorker | None = None

        # Logger
        self._logger = setup_logger()

        self._init_ui()
        self._connect_log()
        self._check_ffmpeg_startup()

    # ── UI build ───────────────────────────────────────────────────

    def _init_ui(self) -> None:
        self.setWindowTitle(f"{self.APP_NAME} — Media Downloader")

        # Adaptive window sizing: 80% of the user's screen
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableSize()
            default_w = int(avail.width() * 0.80)
            default_h = int(avail.height() * 0.80)
            min_w = max(820, int(avail.width() * 0.45))
            min_h = max(600, int(avail.height() * 0.45))
        else:
            default_w, default_h = 1060, 780
            min_w, min_h = 820, 600

        w = self._settings.get("window_width", default_w)
        h = self._settings.get("window_height", default_h)
        self.resize(w, h)
        self.setMinimumSize(min_w, min_h)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────
        top_bar = QHBoxLayout()
        settings_btn = QPushButton("⚙  Paramètres")
        settings_btn.setFixedHeight(34)
        settings_btn.clicked.connect(self._open_settings)
        top_bar.addStretch()
        top_bar.addWidget(settings_btn)
        root.addLayout(top_bar)

        header = QVBoxLayout()
        header.setSpacing(8)
        header.setAlignment(Qt.AlignCenter)

        main_title = QLabel("Universal Video/Audio Downloader")
        main_title.setStyleSheet("font-size: 38px; font-weight: bold; color: #212529; margin-top: 20px;")
        main_title.setAlignment(Qt.AlignCenter)
        header.addWidget(main_title)

        subtitle = QLabel("Téléchargez vidéos et audios depuis YouTube, Instagram, TikTok et +1000 sites")
        subtitle.setStyleSheet("font-size: 16px; color: #495057; margin-bottom: 24px;")
        subtitle.setAlignment(Qt.AlignCenter)
        header.addWidget(subtitle)

        root.addLayout(header)
        root.addSpacing(16)

        # ── Content area with tabs ─────────────────────────────────
        self._tabs = QTabWidget()

        # -- Tab 1: Download
        download_tab = QWidget()
        dl_layout = QVBoxLayout(download_tab)
        dl_layout.setContentsMargins(0, 12, 0, 0)
        dl_layout.setSpacing(14)

        # URL bar
        self._url_bar = UrlBar()
        self._url_bar.analyze_requested.connect(self._on_analyze)
        dl_layout.addWidget(self._url_bar)

        # Error label (hidden by default)
        self._error_label = QLabel("")
        self._error_label.setStyleSheet(
            "color: #ff6b6b; font-size: 12px; font-weight: 600; padding: 4px 0;"
        )
        self._error_label.hide()
        dl_layout.addWidget(self._error_label)

        # Scroll area for main content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        self._content_layout = QVBoxLayout(scroll_content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(14)

        # Media card
        self._media_card = MediaCard()
        self._content_layout.addWidget(self._media_card)

        # Format selector
        self._format_selector = FormatSelector()
        self._format_selector.mode_changed.connect(self._on_mode_changed)
        self._content_layout.addWidget(self._format_selector)

        # Output directory row
        self._output_frame = QFrame()
        self._output_frame.setProperty("class", "card")
        out_layout = QHBoxLayout(self._output_frame)
        out_layout.setContentsMargins(16, 12, 16, 12)
        out_layout.setSpacing(10)

        out_label = QLabel("📁  Dossier :")
        out_label.setStyleSheet("font-weight: 600;")
        out_layout.addWidget(out_label)

        self._output_edit = QLineEdit()
        self._output_edit.setText(self._settings.get("output_dir"))
        self._output_edit.setMinimumHeight(36)
        out_layout.addWidget(self._output_edit, stretch=1)

        browse_btn = QPushButton("Parcourir…")
        browse_btn.setFixedHeight(36)
        browse_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(browse_btn)

        self._content_layout.addWidget(self._output_frame)
        self._output_frame.hide()

        # Options row
        self._options_frame = QFrame()
        self._options_frame.setProperty("class", "card")
        opt_layout = QHBoxLayout(self._options_frame)
        opt_layout.setContentsMargins(16, 10, 16, 10)
        opt_layout.setSpacing(16)

        from PySide6.QtWidgets import QCheckBox
        self._chk_open_folder = QCheckBox("Ouvrir le dossier après")
        self._chk_open_folder.setChecked(self._settings.get("open_folder_after", False))
        opt_layout.addWidget(self._chk_open_folder)

        self._chk_thumbnail = QCheckBox("Miniature")
        self._chk_thumbnail.setChecked(self._settings.get("download_thumbnail", False))
        opt_layout.addWidget(self._chk_thumbnail)

        self._chk_subtitles = QCheckBox("Sous-titres")
        self._chk_subtitles.setChecked(self._settings.get("download_subtitles", False))
        opt_layout.addWidget(self._chk_subtitles)

        self._chk_metadata = QCheckBox("Métadonnées")
        self._chk_metadata.setChecked(self._settings.get("embed_metadata", True))
        opt_layout.addWidget(self._chk_metadata)

        opt_layout.addStretch()
        self._content_layout.addWidget(self._options_frame)
        self._options_frame.hide()

        # Action buttons
        from ui.widgets.animated_button import AnimatedButton
        self._action_row = QHBoxLayout()
        self._action_row.setSpacing(10)

        self._download_btn = AnimatedButton("⬇  Télécharger")
        self._download_btn.setColors("#28a745", "#218838", "#ffffff")
        self._download_btn.setMinimumHeight(44)
        self._download_btn.setMinimumWidth(180)
        self._download_btn.setEnabled(False)
        self._download_btn.clicked.connect(self._on_download)
        self._action_row.addWidget(self._download_btn)

        self._cancel_btn = AnimatedButton("✕  Annuler")
        self._cancel_btn.setColors("#e53935", "#c62828", "#ffffff")
        self._cancel_btn.setMinimumHeight(44)
        self._cancel_btn.hide()
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._action_row.addWidget(self._cancel_btn)

        self._open_folder_btn = AnimatedButton("📂  Ouvrir le dossier")
        self._open_folder_btn.setColors("#6c757d", "#5a6268", "#ffffff")
        self._open_folder_btn.setMinimumHeight(44)
        self._open_folder_btn.hide()
        self._open_folder_btn.clicked.connect(self._open_output_folder)
        self._action_row.addWidget(self._open_folder_btn)

        self._action_row.addStretch()
        self._content_layout.addLayout(self._action_row)

        # Progress panel
        self._progress = ProgressPanel()
        self._content_layout.addWidget(self._progress)

        self._content_layout.addStretch()

        scroll.setWidget(scroll_content)
        dl_layout.addWidget(scroll, stretch=1)

        self._tabs.addTab(download_tab, "⬇  Téléchargement")

        # -- Tab 2: Log
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(0, 12, 0, 0)
        self._log_panel = LogPanel()
        log_layout.addWidget(self._log_panel)
        self._tabs.addTab(log_tab, "📋  Journal")

        # -- Tab 3: History
        history_tab = QWidget()
        hist_layout = QVBoxLayout(history_tab)
        hist_layout.setContentsMargins(0, 12, 0, 0)
        self._history_panel = HistoryPanel(self._history)
        hist_layout.addWidget(self._history_panel)
        self._tabs.addTab(history_tab, "📜  Historique")

        root.addWidget(self._tabs, stretch=1)

        # ── Footer ─────────────────────────────────────────────────
        footer = QLabel(
            f"{self.APP_NAME} v{self.VERSION} — Téléchargement de contenu public uniquement"
        )
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 11px; color: #5c5c72; padding-top: 8px;")
        root.addWidget(footer)

    # ── Logger connection ──────────────────────────────────────────

    def _connect_log(self) -> None:
        emitter = get_log_emitter()
        emitter.new_entry.connect(self._log_panel.append)

    # ── FFmpeg check on start ──────────────────────────────────────

    def _check_ffmpeg_startup(self) -> None:
        ffmpeg_path = self._settings.get("ffmpeg_path", "")
        found = find_ffmpeg(ffmpeg_path)
        if found:
            log.info("FFmpeg trouvé : %s", found)
            return

        # FFmpeg not found — auto-download with a progress dialog
        log.info("FFmpeg introuvable, téléchargement automatique…")
        self._ffmpeg_progress = QProgressDialog(
            "Téléchargement de FFmpeg…", None, 0, 100, self
        )
        self._ffmpeg_progress.setWindowTitle("Installation de FFmpeg")
        self._ffmpeg_progress.setMinimumWidth(420)
        self._ffmpeg_progress.setCancelButton(None)  # no cancel
        self._ffmpeg_progress.setAutoClose(True)
        self._ffmpeg_progress.setAutoReset(True)
        self._ffmpeg_progress.setValue(0)
        self._ffmpeg_progress.show()

        self._ffmpeg_thread = _FFmpegDownloadThread()
        self._ffmpeg_thread.progress.connect(self._on_ffmpeg_dl_progress)
        self._ffmpeg_thread.finished.connect(self._on_ffmpeg_dl_done)
        self._ffmpeg_thread.error.connect(self._on_ffmpeg_dl_error)
        self._ffmpeg_thread.start()

    def _on_ffmpeg_dl_progress(self, text: str, pct: int) -> None:
        if hasattr(self, '_ffmpeg_progress') and self._ffmpeg_progress:
            self._ffmpeg_progress.setLabelText(text)
            if pct >= 0:
                self._ffmpeg_progress.setValue(pct)

    def _on_ffmpeg_dl_done(self, path: str) -> None:
        if hasattr(self, '_ffmpeg_progress') and self._ffmpeg_progress:
            self._ffmpeg_progress.setValue(100)
            self._ffmpeg_progress.close()
        log.info("✅ FFmpeg installé automatiquement : %s", path)

    def _on_ffmpeg_dl_error(self, message: str) -> None:
        if hasattr(self, '_ffmpeg_progress') and self._ffmpeg_progress:
            self._ffmpeg_progress.close()
        log.error("❌ Impossible d'installer FFmpeg : %s", message)
        QMessageBox.warning(
            self, "FFmpeg",
            f"Impossible de télécharger FFmpeg automatiquement.\n\n"
            f"{message}\n\n"
            f"Vous pouvez l'installer manuellement et configurer son chemin "
            f"dans les paramètres.",
        )

    # ── Analysis ───────────────────────────────────────────────────

    def _on_analyze(self, url: str) -> None:
        # Validate
        if not url:
            self._show_error("Veuillez coller un lien avant de lancer l'analyse.")
            return
        if not validate_url(url):
            self._show_error("L'URL saisie ne semble pas valide. Vérifiez le format.")
            return

        # Reset state
        self._reset_state()
        self._hide_error()
        self._url_bar.set_analyzing(True)
        log.info("Analyse lancée pour : %s", url)

        # Run analysis in background
        ffmpeg = find_ffmpeg(self._settings.get("ffmpeg_path", ""))
        self._analyze_worker = AnalyzeWorker(url, ffmpeg)
        self._analyze_worker.finished.connect(self._on_analyze_done)
        self._analyze_worker.error.connect(self._on_analyze_error)
        self._analyze_worker.start()

    def _on_analyze_done(self, media: MediaInfo) -> None:
        self._url_bar.set_analyzing(False)
        self._current_media = media

        # Populate UI
        self._media_card.set_media(media)

        video_fmts = parse_video_formats(media.formats)
        audio_fmts = parse_audio_formats(media.formats)

        self._format_selector.populate_video(video_fmts)
        self._format_selector.populate_audio(audio_fmts)

        # Restore last mode
        last_mode = self._settings.get("last_mode", "video")
        self._format_selector.set_mode(last_mode)
        self._format_selector.show_populated()

        # Show output dir and options
        self._output_frame.show()
        self._options_frame.show()
        self._download_btn.setEnabled(True)
        self._open_folder_btn.hide()

        log.info(
            "Analyse réussie : %s — %d vidéo(s), %d audio(s)",
            media.title, len(video_fmts), len(audio_fmts),
        )

    def _on_analyze_error(self, message: str) -> None:
        self._url_bar.set_analyzing(False)
        self._show_error(message)
        log.error("Échec de l'analyse : %s", message)

    # ── Download ───────────────────────────────────────────────────

    def _on_download(self) -> None:
        if not self._current_media:
            return

        output_dir = self._output_edit.text().strip()
        if not output_dir:
            self._show_error("Veuillez choisir un dossier de sortie.")
            return

        # Ensure output dir exists
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self._show_error(f"Impossible de créer le dossier : {e}")
            return

        # Save output dir
        self._settings.set("output_dir", output_dir)

        mode = self._format_selector.get_mode()
        self._settings.set("last_mode", mode)
        self._hide_error()

        ffmpeg = find_ffmpeg(self._settings.get("ffmpeg_path", ""))

        # Check FFmpeg for operations that need it
        if mode == "audio" or (mode == "video" and self._format_selector.get_selected_video_format()
                               and self._format_selector.get_selected_video_format().kind == "video"):
            if not ffmpeg:
                self._show_error(
                    "FFmpeg est requis pour cette opération mais n'a pas été trouvé. "
                    "Installez FFmpeg ou configurez son chemin dans les paramètres."
                )
                return

        self._download_btn.setEnabled(False)
        self._cancel_btn.show()
        self._url_bar.set_enabled(False)
        self._progress.reset()
        self._progress.show()
        self._progress.set_status("Démarrage du téléchargement…")
        self._open_folder_btn.hide()

        if mode == "video":
            video_fmt = self._format_selector.get_selected_video_format()
            if not video_fmt:
                self._show_error("Veuillez sélectionner un format vidéo.")
                self._restore_after_download()
                return

            log.info("Téléchargement vidéo : %s — format %s", self._current_media.title, video_fmt.label)

            self._download_worker = DownloadWorker(
                url=self._current_media.url,
                mode="video",
                video_format=video_fmt,
                output_dir=output_dir,
                raw_formats=self._current_media.formats,
                ffmpeg_path=ffmpeg,
                embed_metadata=self._chk_metadata.isChecked(),
                download_thumbnail=self._chk_thumbnail.isChecked(),
                download_subtitles=self._chk_subtitles.isChecked(),
                overwrite=self._settings.get("overwrite_existing", False),
            )
        else:
            audio_source = self._format_selector.get_selected_audio_source()
            audio_fmt = self._format_selector.get_audio_output_format()
            audio_br = self._format_selector.get_audio_bitrate()

            log.info(
                "Téléchargement audio : %s — %s %s kbps",
                self._current_media.title, audio_fmt, audio_br,
            )

            self._download_worker = DownloadWorker(
                url=self._current_media.url,
                mode="audio",
                audio_source_format=audio_source,
                audio_output_format=audio_fmt,
                audio_bitrate=audio_br,
                output_dir=output_dir,
                raw_formats=self._current_media.formats,
                ffmpeg_path=ffmpeg,
                embed_metadata=self._chk_metadata.isChecked(),
                download_thumbnail=self._chk_thumbnail.isChecked(),
                overwrite=self._settings.get("overwrite_existing", False),
            )

        self._download_worker.progress.connect(self._on_dl_progress)
        self._download_worker.status.connect(self._on_dl_status)
        self._download_worker.finished.connect(self._on_dl_finished)
        self._download_worker.error.connect(self._on_dl_error)
        self._download_worker.start()

    def _on_dl_progress(
        self, pct: float, downloaded: int, total: int,
        speed: float, eta: float,
    ) -> None:
        self._progress.update_progress(pct, downloaded, total, speed, eta)

    def _on_dl_status(self, text: str) -> None:
        self._progress.set_status(text)
        log.info(text)

    def _on_dl_finished(self, filepath: str) -> None:
        self._progress.set_complete()
        self._restore_after_download()
        self._open_folder_btn.show()

        log.info("✅ Fichier enregistré : %s", filepath)

        # Save to history
        self._history.add(
            title=self._current_media.title if self._current_media else "—",
            url=self._current_media.url if self._current_media else "",
            filepath=filepath,
            status="success",
            platform=self._current_media.platform if self._current_media else "",
            mode=self._format_selector.get_mode(),
        )
        self._history_panel.refresh()

        # Auto-open folder
        if self._chk_open_folder.isChecked():
            self._open_output_folder()

    def _on_dl_error(self, message: str) -> None:
        self._progress.set_error(message)
        self._restore_after_download()
        log.error("❌ Erreur : %s", message)

        if self._current_media:
            self._history.add(
                title=self._current_media.title,
                url=self._current_media.url,
                filepath="",
                status="error",
                platform=self._current_media.platform,
                mode=self._format_selector.get_mode(),
            )
            self._history_panel.refresh()

    def _on_cancel(self) -> None:
        if self._download_worker:
            self._download_worker.cancel()
            log.info("Annulation demandée…")
            self._progress.set_status("Annulation en cours…")

    # ── Helpers ────────────────────────────────────────────────────

    def _restore_after_download(self) -> None:
        self._download_btn.setEnabled(True)
        self._cancel_btn.hide()
        self._url_bar.set_enabled(True)

    def _reset_state(self) -> None:
        """Clear previous analysis results."""
        self._current_media = None
        self._media_card.clear()
        self._format_selector.clear()
        self._output_frame.hide()
        self._options_frame.hide()
        self._download_btn.setEnabled(False)
        self._progress.reset()
        self._progress.hide()
        self._open_folder_btn.hide()

    def _show_error(self, text: str) -> None:
        self._error_label.setText(f"⚠  {text}")
        self._error_label.show()

    def _hide_error(self) -> None:
        self._error_label.setText("")
        self._error_label.hide()

    def _browse_output(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier de sortie",
            self._output_edit.text(),
        )
        if d:
            self._output_edit.setText(d)

    def _open_output_folder(self) -> None:
        folder = self._output_edit.text().strip()
        if folder and os.path.isdir(folder):
            subprocess.Popen(["explorer", os.path.normpath(folder)])

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _on_settings_changed(self) -> None:
        # Refresh output dir from settings
        self._output_edit.setText(self._settings.get("output_dir"))
        self._chk_open_folder.setChecked(self._settings.get("open_folder_after", False))
        self._chk_thumbnail.setChecked(self._settings.get("download_thumbnail", False))
        self._chk_subtitles.setChecked(self._settings.get("download_subtitles", False))
        self._chk_metadata.setChecked(self._settings.get("embed_metadata", True))

    def _on_mode_changed(self, mode: str) -> None:
        self._settings.set("last_mode", mode)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._settings.set("window_width", self.width())
        self._settings.set("window_height", self.height())

    def closeEvent(self, event) -> None:
        # Cancel any running worker
        if self._download_worker and self._download_worker.isRunning():
            self._download_worker.cancel()
            self._download_worker.wait(3000)
        if self._analyze_worker and self._analyze_worker.isRunning():
            self._analyze_worker.wait(3000)
        super().closeEvent(event)
