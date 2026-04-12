"""
MediaFlow — URL analyser powered by yt-dlp.
Extracts metadata and available formats from a public URL.
"""

import logging
import os
import re
from dataclasses import dataclass, field

import yt_dlp

log = logging.getLogger("mediaflow")

# Simple URL validation
_URL_RE = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE
)


@dataclass
class MediaInfo:
    """Structured result of a successful URL analysis."""
    url: str = ""
    title: str = ""
    platform: str = ""
    uploader: str = ""
    duration: float | int | None = None   # seconds (may be float from some platforms)
    thumbnail_url: str = ""
    webpage_url: str = ""
    formats: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @property
    def duration_str(self) -> str:
        if self.duration is None:
            return "—"
        total = int(self.duration)
        m, s = divmod(total, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

def validate_url(url: str) -> bool:
    """Basic syntactic URL check."""
    return bool(_URL_RE.match(url.strip()))

class Analyzer:
    """Wraps yt-dlp extract_info to fetch metadata + format list."""

    def __init__(self, ffmpeg_path: str | None = None) -> None:
        self._ffmpeg = ffmpeg_path

    def analyze(self, url: str) -> MediaInfo:
        """
        Analyse *url* and return a MediaInfo.
        Raises RuntimeError on failure.
        """
        url = url.strip()
        if not validate_url(url):
            raise ValueError("URL invalide ou non reconnue.")

        log.info("Analyse de l'URL : %s", url)

        COOKIES_PATH = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '..', 'cookies.txt')
        
        ydl_opts: dict = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "socket_timeout": 30,
            "rm_cachedir": True,
            "extractor_retries": 3,
            "fragment_retries": 3,
            "retry_sleep_functions": {'extractor': lambda n: 2 ** n},
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            },
            "cookiefile": COOKIES_PATH if os.path.exists(COOKIES_PATH) and os.path.getsize(COOKIES_PATH) > 0 else None
        }


        if self._ffmpeg:
            ydl_opts["ffmpeg_location"] = self._ffmpeg

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as exc:
            msg = str(exc)
            if "Private" in msg or "private" in msg:
                raise RuntimeError("Ce contenu est privé et ne peut pas être téléchargé.") from exc
            if "unavailable" in msg.lower():
                raise RuntimeError("Ce contenu est indisponible.") from exc
            if "not supported" in msg.lower() or "Unsupported" in msg:
                raise RuntimeError("Cette plateforme n'est pas prise en charge.") from exc
            if "age" in msg.lower():
                raise RuntimeError("Ce contenu est soumis à une restriction d'âge.") from exc
            raise RuntimeError(f"Échec de l'analyse : {msg}") from exc
        except Exception as exc:
            raise RuntimeError(f"Erreur inattendue lors de l'analyse : {exc}") from exc

        if info is None:
            raise RuntimeError("Aucune information n'a pu être extraite.")

        formats_raw = info.get("formats") or []

        media = MediaInfo(
            url=url,
            title=info.get("title", "Sans titre"),
            platform=info.get("extractor_key", info.get("extractor", "Inconnu")),
            uploader=info.get("uploader", info.get("channel", "")),
            duration=info.get("duration"),
            thumbnail_url=info.get("thumbnail", ""),
            webpage_url=info.get("webpage_url", url),
            formats=formats_raw,
            raw=info,
        )

        log.info(
            "Analyse terminée — %s (%s) — %d format(s) trouvé(s)",
            media.title, media.platform, len(formats_raw),
        )
        return media
