"""
MediaFlow — Format parsing & display service.
Transforms raw yt-dlp format dicts into user-friendly lists.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from utils.file_utils import format_filesize

log = logging.getLogger("mediaflow")


@dataclass
class FormatItem:
    """A single selectable format entry shown to the user."""
    format_id: str
    label: str                            # human-readable label
    kind: str                             # "video+audio" | "video" | "audio"
    ext: str
    resolution: str = ""
    fps: int | None = None
    vcodec: str = ""
    acodec: str = ""
    abr: float | None = None             # audio bitrate (kbps)
    filesize: int | None = None           # bytes, may be estimated
    width: int = 0
    height: int = 0
    quality_sort: int = 0                 # higher = better


def _is_none_codec(codec: str | None) -> bool:
    return codec is None or codec in ("none", "")


def parse_video_formats(raw_formats: list[dict]) -> list[FormatItem]:
    """Return video-relevant formats, sorted best → worst."""
    results: list[FormatItem] = []
    seen: set[str] = set()

    for fmt in raw_formats:
        vcodec = fmt.get("vcodec", "none") or "none"
        acodec = fmt.get("acodec", "none") or "none"
        if _is_none_codec(vcodec):
            continue  # skip audio-only

        height = fmt.get("height") or 0
        width = fmt.get("width") or 0
        if height == 0 and width == 0:
            continue

        fps = fmt.get("fps")
        ext = fmt.get("ext", "?")
        fid = fmt.get("format_id", "?")

        has_audio = not _is_none_codec(acodec)
        kind = "video+audio" if has_audio else "video"

        # Build resolution string
        res = f"{width}x{height}" if width and height else f"{height}p"

        # Deduplicate based on key characteristics
        dedup_key = f"{res}_{fps}_{ext}_{kind}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Build label
        parts = [res]
        if fps and fps > 1:
            parts.append(f"{int(fps)} fps")
        parts.append(ext)
        vc_short = _short_codec(vcodec)
        if vc_short:
            parts.append(vc_short)
        parts.append("vidéo + audio" if has_audio else "vidéo seule")

        filesize = fmt.get("filesize") or fmt.get("filesize_approx")

        if filesize:
            parts.append(f"~{format_filesize(filesize)}")

        label = " • ".join(parts)

        quality = height * 100 + (fps or 0)

        results.append(FormatItem(
            format_id=fid,
            label=label,
            kind=kind,
            ext=ext,
            resolution=res,
            fps=int(fps) if fps else None,
            vcodec=vcodec,
            acodec=acodec,
            filesize=filesize,
            width=width,
            height=height,
            quality_sort=quality,
        ))

    results.sort(key=lambda f: f.quality_sort, reverse=True)
    return results


def parse_audio_formats(raw_formats: list[dict]) -> list[FormatItem]:
    """Return audio-only formats, sorted best → worst."""
    results: list[FormatItem] = []
    seen: set[str] = set()

    for fmt in raw_formats:
        vcodec = fmt.get("vcodec", "none") or "none"
        acodec = fmt.get("acodec", "none") or "none"
        if not _is_none_codec(vcodec):
            continue  # has video track
        if _is_none_codec(acodec):
            continue  # no audio either

        abr = fmt.get("abr") or fmt.get("tbr") or 0
        ext = fmt.get("ext", "?")
        fid = fmt.get("format_id", "?")

        dedup_key = f"{acodec}_{int(abr)}_{ext}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        filesize = fmt.get("filesize") or fmt.get("filesize_approx")

        parts = [ext.upper()]
        ac_short = _short_codec(acodec)
        if ac_short:
            parts.append(ac_short)
        if abr:
            parts.append(f"{int(abr)} kbps")
        if filesize:
            parts.append(f"~{format_filesize(filesize)}")

        label = " • ".join(parts)

        results.append(FormatItem(
            format_id=fid,
            label=label,
            kind="audio",
            ext=ext,
            acodec=acodec,
            abr=abr,
            filesize=filesize,
            quality_sort=int(abr * 100),
        ))

    results.sort(key=lambda f: f.quality_sort, reverse=True)
    return results


def get_best_audio_format_id(raw_formats: list[dict]) -> str | None:
    """Return the format_id of the best audio-only stream."""
    audio = parse_audio_formats(raw_formats)
    return audio[0].format_id if audio else None


def _short_codec(codec: str) -> str:
    """Shorten common codec names for display."""
    if _is_none_codec(codec):
        return ""
    c = codec.lower()
    mapping = {
        "avc1": "H.264", "h264": "H.264",
        "hev1": "H.265", "hevc": "H.265", "h265": "H.265",
        "vp9": "VP9", "vp09": "VP9",
        "av01": "AV1", "av1": "AV1",
        "mp4a": "AAC", "aac": "AAC",
        "opus": "Opus",
        "vorbis": "Vorbis",
        "mp3": "MP3",
        "flac": "FLAC",
    }
    for key, val in mapping.items():
        if key in c:
            return val
    return codec
