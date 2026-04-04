"""Quick import verification for all MediaFlow modules."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

from config.settings import Settings
print("  [OK] config.settings")

from utils.logger import setup_logger, get_log_emitter
print("  [OK] utils.logger")

from utils.file_utils import sanitize_filename, format_filesize
print("  [OK] utils.file_utils")

from core.ffmpeg_utils import find_ffmpeg, check_ffmpeg
print("  [OK] core.ffmpeg_utils")

from core.analyzer import Analyzer, MediaInfo, validate_url
print("  [OK] core.analyzer")

from core.converter import AUDIO_FORMATS, AUDIO_BITRATES
print("  [OK] core.converter")

from core.downloader import Downloader
print("  [OK] core.downloader")

from services.format_service import parse_video_formats, parse_audio_formats, FormatItem
print("  [OK] services.format_service")

from services.history_service import HistoryService
print("  [OK] services.history_service")

from workers.analyze_worker import AnalyzeWorker
print("  [OK] workers.analyze_worker")

from workers.download_worker import DownloadWorker
print("  [OK] workers.download_worker")

from ui.styles.theme import get_stylesheet
print("  [OK] ui.styles.theme")

from ui.widgets.url_bar import UrlBar
print("  [OK] ui.widgets.url_bar")

from ui.widgets.media_card import MediaCard
print("  [OK] ui.widgets.media_card")

from ui.widgets.format_selector import FormatSelector
print("  [OK] ui.widgets.format_selector")

from ui.widgets.progress_panel import ProgressPanel
print("  [OK] ui.widgets.progress_panel")

from ui.widgets.log_panel import LogPanel
print("  [OK] ui.widgets.log_panel")

from ui.widgets.settings_dialog import SettingsDialog
print("  [OK] ui.widgets.settings_dialog")

from ui.widgets.history_panel import HistoryPanel
print("  [OK] ui.widgets.history_panel")

from ui.main_window import MainWindow
print("  [OK] ui.main_window")

# Quick logic checks
print()
print("Running logic checks...")

r1 = sanitize_filename("Test Video Cool")
print(f"  sanitize_filename test: {repr(r1)}")

assert validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == True
print("  [OK] URL validation (valid)")

assert validate_url("not a url") == False
print("  [OK] URL validation (invalid)")

assert format_filesize(1024) == "1.0 KB"
print("  [OK] format_filesize KB")

assert format_filesize(1048576) == "1.0 MB"
print("  [OK] format_filesize MB")

s = Settings()
print(f"  Settings dir: {s.data_dir}")

ok, msg = check_ffmpeg()
print(f"  FFmpeg: {'found' if ok else 'NOT FOUND'} - {msg}")

print()
print("=== ALL CHECKS PASSED ===")
