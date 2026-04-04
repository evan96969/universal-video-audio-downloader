"""
Universal Downloader — FFmpeg detection, management, and auto-download.
"""

import io
import logging
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request

log = logging.getLogger("mediaflow")

# URL for a well-known static FFmpeg build (Windows essentials, GPL)
_FFMPEG_DOWNLOAD_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
    "latest/ffmpeg-master-latest-win64-gpl.zip"
)


def _default_ffmpeg_dir() -> Path:
    """Return the default directory where auto-downloaded FFmpeg lives."""
    base = Path(os.getenv("APPDATA", Path.home())) / "UniversalDownloader"
    return base / "ffmpeg"


def find_ffmpeg(custom_path: str = "") -> str | None:
    """Return the absolute path to ffmpeg, or None if not found."""
    # 1. User-configured path
    if custom_path:
        p = Path(custom_path)
        if p.is_file() and p.exists():
            return str(p)
        # Maybe user gave folder instead of binary
        candidate = p / "ffmpeg.exe"
        if candidate.is_file():
            return str(candidate)

    # 2. Auto-downloaded location
    auto_dir = _default_ffmpeg_dir()
    auto_exe = auto_dir / "ffmpeg.exe"
    if auto_exe.is_file():
        return str(auto_exe)

    # 3. Bundled alongside app (for PyInstaller builds)
    import sys
    app_dir = Path(getattr(sys, "_MEIPASS", Path(sys.argv[0]).resolve().parent))
    for name in ("ffmpeg.exe", "ffmpeg"):
        bundled = app_dir / name
        if bundled.is_file():
            return str(bundled)

    # 4. System PATH
    found = shutil.which("ffmpeg")
    if found:
        return found

    return None


def find_ffprobe(custom_path: str = "") -> str | None:
    """Return the absolute path to ffprobe, or None."""
    if custom_path:
        base = Path(custom_path).parent if Path(custom_path).is_file() else Path(custom_path)
        probe = base / "ffprobe.exe"
        if probe.is_file():
            return str(probe)
        probe = base / "ffprobe"
        if probe.is_file():
            return str(probe)

    # Auto-downloaded location
    auto_dir = _default_ffmpeg_dir()
    auto_probe = auto_dir / "ffprobe.exe"
    if auto_probe.is_file():
        return str(auto_probe)

    import sys
    app_dir = Path(getattr(sys, "_MEIPASS", Path(sys.argv[0]).resolve().parent))
    for name in ("ffprobe.exe", "ffprobe"):
        bundled = app_dir / name
        if bundled.is_file():
            return str(bundled)

    return shutil.which("ffprobe")


def get_ffmpeg_version(ffmpeg_path: str) -> str | None:
    """Return the version string reported by ffmpeg, or None on error."""
    try:
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        first_line = result.stdout.strip().splitlines()[0]
        return first_line
    except Exception:
        return None


def check_ffmpeg(custom_path: str = "") -> tuple[bool, str]:
    """
    Check FFmpeg availability.
    Returns (available: bool, message: str).
    """
    path = find_ffmpeg(custom_path)
    if path is None:
        return False, (
            "FFmpeg introuvable. Veuillez installer FFmpeg et l'ajouter au PATH, "
            "ou configurez son emplacement dans les paramètres."
        )
    version = get_ffmpeg_version(path)
    if version:
        log.info("FFmpeg trouvé : %s", version)
        return True, f"FFmpeg détecté : {path}"
    return True, f"FFmpeg trouvé à {path} (version inconnue)"


def download_ffmpeg(progress_callback=None) -> str:
    """
    Download FFmpeg from GitHub and extract ffmpeg.exe + ffprobe.exe
    to the app data directory.

    Args:
        progress_callback: Optional callable(status_text: str, percent: int)
            called to report progress.  percent is 0-100 or -1 for indeterminate.

    Returns:
        Path to ffmpeg.exe on success.

    Raises:
        RuntimeError on any failure.
    """
    dest_dir = _default_ffmpeg_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)

    def _report(msg: str, pct: int = -1):
        if progress_callback:
            progress_callback(msg, pct)

    _report("Connexion au serveur GitHub…", 0)

    try:
        req = Request(_FFMPEG_DOWNLOAD_URL, headers={"User-Agent": "UniversalDownloader/1.0"})
        resp = urlopen(req, timeout=60)

        # Try to get content length for progress
        content_length = resp.headers.get("Content-Length")
        total = int(content_length) if content_length else None

        _report("Téléchargement de FFmpeg…", 5)

        # Download in chunks
        data = io.BytesIO()
        downloaded = 0
        chunk_size = 256 * 1024  # 256 KB
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            data.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = int(5 + (downloaded / total) * 75)  # 5-80%
                size_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                _report(f"Téléchargement… {size_mb:.1f} / {total_mb:.1f} Mo", min(pct, 80))
            else:
                size_mb = downloaded / (1024 * 1024)
                _report(f"Téléchargement… {size_mb:.1f} Mo", -1)

    except Exception as e:
        raise RuntimeError(f"Impossible de télécharger FFmpeg : {e}") from e

    _report("Extraction de FFmpeg…", 85)

    try:
        data.seek(0)
        with zipfile.ZipFile(data) as zf:
            # Find ffmpeg.exe and ffprobe.exe inside the zip
            ffmpeg_found = False
            ffprobe_found = False
            for member in zf.namelist():
                basename = os.path.basename(member)
                if basename == "ffmpeg.exe":
                    _report("Extraction de ffmpeg.exe…", 90)
                    with zf.open(member) as src, open(dest_dir / "ffmpeg.exe", "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    ffmpeg_found = True
                elif basename == "ffprobe.exe":
                    _report("Extraction de ffprobe.exe…", 95)
                    with zf.open(member) as src, open(dest_dir / "ffprobe.exe", "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    ffprobe_found = True

                if ffmpeg_found and ffprobe_found:
                    break

            if not ffmpeg_found:
                raise RuntimeError("ffmpeg.exe non trouvé dans l'archive téléchargée.")

    except zipfile.BadZipFile as e:
        raise RuntimeError(f"L'archive téléchargée est corrompue : {e}") from e

    ffmpeg_exe = str(dest_dir / "ffmpeg.exe")
    _report("FFmpeg installé avec succès !", 100)
    log.info("FFmpeg auto-installé : %s", ffmpeg_exe)
    return ffmpeg_exe


def ensure_ffmpeg(custom_path: str = "", progress_callback=None) -> str | None:
    """
    Ensure FFmpeg is available.  If not found, download it automatically.

    Args:
        custom_path: User-configured path (may be empty).
        progress_callback: Optional callable(status: str, percent: int).

    Returns:
        Path to ffmpeg.exe, or None if everything fails.
    """
    path = find_ffmpeg(custom_path)
    if path:
        return path

    try:
        return download_ffmpeg(progress_callback)
    except Exception as e:
        log.error("Échec du téléchargement automatique de FFmpeg : %s", e)
        return None
