"""
MediaFlow — Audio conversion helpers.
Provides format information for the audio output selector.
"""

AUDIO_FORMATS: list[dict[str, str]] = [
    {"id": "mp3",  "label": "MP3",  "description": "Format universel, bonne compatibilité"},
    {"id": "m4a",  "label": "M4A",  "description": "AAC dans conteneur M4A, bonne qualité"},
    {"id": "wav",  "label": "WAV",  "description": "Non compressé, taille élevée"},
    {"id": "flac", "label": "FLAC", "description": "Compression sans perte (lossless)"},
    {"id": "opus", "label": "Opus", "description": "Moderne, efficace, bonne qualité"},
]

AUDIO_BITRATES: list[dict[str, str]] = [
    {"id": "320", "label": "320 kbps — Excellente qualité"},
    {"id": "256", "label": "256 kbps — Très bonne qualité"},
    {"id": "192", "label": "192 kbps — Bonne qualité (recommandé)"},
    {"id": "128", "label": "128 kbps — Qualité standard"},
    {"id": "96",  "label": "96 kbps  — Qualité réduite"},
    {"id": "64",  "label": "64 kbps  — Faible qualité"},
]

# For lossless formats bitrate is irrelevant
LOSSLESS_FORMATS = {"wav", "flac"}
