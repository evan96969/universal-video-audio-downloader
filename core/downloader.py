"""
MediaFlow — Download engine.
Drives yt-dlp downloads with real-time progress hooks.
"""

import logging
import os
from pathlib import Path
from typing import Any, Callable

import yt_dlp

from core.ffmpeg_utils import find_ffmpeg
from services.format_service import FormatItem, get_best_audio_format_id
from utils.file_utils import sanitize_filename, unique_filepath

log = logging.getLogger("mediaflow")

# Callback signature: (percent, downloaded_bytes, total_bytes, speed, eta)
ProgressCallback = Callable[[float, int, int | None, float | None, float | None], None]
StatusCallback = Callable[[str], None]


class Downloader:
    """Encapsulates a single yt-dlp download operation."""

    def __init__(
        self,
        ffmpeg_path: str | None = None,
        embed_metadata: bool = True,
        download_thumbnail: bool = False,
        download_subtitles: bool = False,
        overwrite: bool = False,
    ) -> None:
        self._ffmpeg = ffmpeg_path or find_ffmpeg()
        self._embed_metadata = embed_metadata
        self._download_thumbnail = download_thumbnail
        self._download_subtitles = download_subtitles
        self._overwrite = overwrite
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    # --- Video download -----------------------------------------------------

    def download_video(
        self,
        url: str,
        format_item: FormatItem,
        output_dir: str,
        raw_formats: list[dict],
        on_progress: ProgressCallback | None = None,
        on_status: StatusCallback | None = None,
    ) -> Path:
        """
        Download a video.
        If the chosen format is video-only, also grabs the best audio and merges.
        Returns the final file path.
        """
        self._cancelled = False
        title = "download"

        # We let yt-dlp handle filename template
        outtmpl = os.path.join(output_dir, "%(title).200s.%(ext)s")

        if format_item.kind == "video+audio":
            format_spec = format_item.format_id
            if on_status:
                on_status("Téléchargement vidéo + audio (format combiné)…")
        else:
            best_audio_id = get_best_audio_format_id(raw_formats)
            if best_audio_id:
                format_spec = f"{format_item.format_id}+{best_audio_id}"
                if on_status:
                    on_status("Téléchargement vidéo + audio séparés, puis fusion…")
            else:
                format_spec = format_item.format_id
                if on_status:
                    on_status("Téléchargement vidéo seule (aucun flux audio trouvé)…")

        opts = self._base_opts(outtmpl, on_progress)
        opts["format"] = format_spec
        opts["merge_output_format"] = format_item.ext if format_item.ext in ("mp4", "mkv", "webm") else "mp4"

        if self._download_subtitles:
            opts["writesubtitles"] = True
            opts["subtitleslangs"] = ["all"]

        if self._download_thumbnail:
            opts["writethumbnail"] = True

        return self._run(url, opts, on_status)

    # --- Audio download -----------------------------------------------------

    def download_audio(
        self,
        url: str,
        audio_format: str,       # mp3, m4a, wav, flac
        audio_bitrate: str,      # e.g. "192"
        source_format: FormatItem | None,
        output_dir: str,
        on_progress: ProgressCallback | None = None,
        on_status: StatusCallback | None = None,
    ) -> Path:
        """
        Download and convert to the requested audio format.
        Returns the final file path.
        """
        self._cancelled = False

        outtmpl = os.path.join(output_dir, "%(title).200s.%(ext)s")

        opts = self._base_opts(outtmpl, on_progress)

        if source_format:
            opts["format"] = source_format.format_id
        else:
            opts["format"] = "bestaudio/best"

        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": audio_bitrate,
        }]

        if self._embed_metadata:
            opts["postprocessors"].append({"key": "FFmpegMetadata"})

        if self._download_thumbnail:
            opts["writethumbnail"] = True
            opts["postprocessors"].append({"key": "EmbedThumbnail"})

        if on_status:
            on_status(f"Téléchargement audio → conversion {audio_format.upper()} {audio_bitrate} kbps…")

        return self._run(url, opts, on_status)

    # --- Internals ----------------------------------------------------------

    def _base_opts(self, outtmpl: str, on_progress: ProgressCallback | None) -> dict:
        opts: dict[str, Any] = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "restrictfilenames": False,
            "windowsfilenames": True,
            "overwrites": self._overwrite,
            "progress_hooks": [],
        }

        if self._ffmpeg:
            opts["ffmpeg_location"] = self._ffmpeg

        if self._embed_metadata:
            opts.setdefault("postprocessors", []).append({"key": "FFmpegMetadata"})

        if on_progress:
            opts["progress_hooks"].append(self._make_hook(on_progress))

        return opts

    def _make_hook(self, callback: ProgressCallback):
        def hook(d: dict) -> None:
            if self._cancelled:
                raise yt_dlp.utils.DownloadCancelled("Téléchargement annulé par l'utilisateur.")

            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed")
                eta = d.get("eta")
                pct = (downloaded / total * 100) if total else 0
                callback(pct, downloaded, total, speed, eta)

            elif d.get("status") == "finished":
                callback(100, d.get("total_bytes", 0), d.get("total_bytes", 0), None, None)

        return hook

    def _run(self, url: str, opts: dict, on_status: StatusCallback | None) -> Path:
        """Execute the download and return the final file path."""
        final_path: str = ""

        # Track the final filename via a post-hook
        original_pp_hooks = opts.get("postprocessor_hooks", [])

        def pp_hook(d: dict) -> None:
            nonlocal final_path
            if d.get("status") == "finished":
                info = d.get("info_dict", {})
                fp = info.get("filepath") or info.get("filename", "")
                if fp:
                    final_path = fp

        opts["postprocessor_hooks"] = [pp_hook] + original_pp_hooks

        try:
            log.info("Lancement du téléchargement : %s", url)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)

            if not final_path and info:
                # Fallback: construct from template
                final_path = info.get("requested_downloads", [{}])[0].get("filepath", "")
                if not final_path:
                    final_path = ydl.prepare_filename(info)

            log.info("Téléchargement terminé : %s", final_path)
            if on_status:
                on_status("Téléchargement terminé ✓")

            return Path(final_path)

        except yt_dlp.utils.DownloadCancelled:
            log.info("Téléchargement annulé.")
            if on_status:
                on_status("Téléchargement annulé.")
            raise
        except yt_dlp.utils.DownloadError as exc:
            msg = str(exc)
            log.error("Erreur de téléchargement : %s", msg)
            raise RuntimeError(f"Erreur de téléchargement : {msg}") from exc
        except PermissionError as exc:
            log.error("Permission refusée : %s", exc)
            raise RuntimeError(
                "Permission refusée. Vérifiez les droits d'écriture sur le dossier de destination."
            ) from exc
        except OSError as exc:
            if "No space" in str(exc) or "space" in str(exc).lower():
                raise RuntimeError("Espace disque insuffisant.") from exc
            log.error("Erreur disque : %s", exc)
            raise RuntimeError(f"Erreur disque : {exc}") from exc
