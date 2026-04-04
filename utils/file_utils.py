"""
MediaFlow — File-system utilities.
Filename sanitisation, safe path handling, disk-space checks.
"""

import os
import re
import string
from pathlib import Path


# Characters forbidden on Windows
_WINDOWS_FORBIDDEN = set('<>:"/\\|?*')
_SAFE_CHARS = set(string.ascii_letters + string.digits + " ._-()[]{}!@#&+=',")


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Return a Windows-safe filename derived from *name*."""
    if not name:
        return "download"

    # Strip leading/trailing whitespace and dots
    name = name.strip().strip(".")

    # Replace forbidden characters
    cleaned = []
    for ch in name:
        if ch in _WINDOWS_FORBIDDEN:
            cleaned.append("_")
        elif ord(ch) < 32:
            continue  # control characters
        else:
            cleaned.append(ch)
    name = "".join(cleaned)

    # Collapse consecutive whitespace / underscores
    name = re.sub(r"[\s_]+", " ", name).strip()

    # Truncate
    if len(name) > max_length:
        name = name[:max_length].rstrip()

    # Avoid Windows reserved names
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    stem = Path(name).stem.upper()
    if stem in reserved:
        name = f"_{name}"

    return name or "download"


def unique_filepath(directory: str | Path, filename: str) -> Path:
    """Return a filepath that does not collide with existing files."""
    directory = Path(directory)
    target = directory / filename
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        candidate = directory / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def disk_free_bytes(path: str | Path) -> int | None:
    """Return free bytes on the volume containing *path*, or None."""
    try:
        stat = os.statvfs(str(path)) if hasattr(os, "statvfs") else None
        if stat:
            return stat.f_bavail * stat.f_frsize
        # Windows fallback via ctypes
        import ctypes
        free = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            str(path), None, None, ctypes.byref(free),
        )
        return free.value
    except Exception:
        return None


def ensure_directory(path: str | Path) -> Path:
    """Create directory if it does not exist and return it as Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def format_filesize(size_bytes: int | float | None) -> str:
    """Human-readable file size string."""
    if size_bytes is None or size_bytes < 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
