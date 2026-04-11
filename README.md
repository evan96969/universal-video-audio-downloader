# Universal Video/Audio Downloader

Application desktop moderne pour télécharger du contenu multimédia public depuis YouTube, Instagram, TikTok, X/Twitter et d'autres plateformes compatibles.

> **⚠️ Usage responsable** : cette application est conçue pour télécharger uniquement du contenu publiquement accessible. Aucun contournement de DRM, paywall ou protection n'est implémenté.

---

## Fonctionnalités

- 🔗 Coller un lien et analyser automatiquement le contenu
- 🎬 Téléchargement vidéo avec choix de la résolution, fps, codec
- 🎵 Téléchargement audio avec conversion (MP3, M4A, WAV, FLAC, Opus)
- 📊 Formats réellement disponibles affichés (pas de qualités inventées)
- 🔀 Fusion automatique vidéo + audio via FFmpeg
- 📁 Choix du dossier de destination
- 📈 Barre de progression avec vitesse, taille, temps restant
- 📋 Journal d'activité en temps réel
- 📜 Historique des téléchargements récents
- ⚙️ Paramètres persistants (dossier, format préféré, etc.)
- 🌙 Interface sombre, moderne et élégante
- 🔧 **FFmpeg téléchargé et configuré automatiquement**
- 📐 **Fenêtre adaptée à la taille de l'écran**

## Plateformes supportées

YouTube, Instagram, TikTok, X/Twitter, Facebook, Dailymotion, Vimeo, SoundCloud, et [toute plateforme publique supportée par yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

---

## Prérequis

| Outil | Version | Lien |
|-------|---------|------|
| Python | 3.12+ | https://www.python.org/downloads/ |
| pip | dernière version | Inclus avec Python |

> 💡 **FFmpeg** est téléchargé et configuré automatiquement au premier lancement. Aucune installation manuelle n'est nécessaire.

---

## Installation

```bash
# Cloner ou extraire le projet
cd mediaflow

# Créer un environnement virtuel (recommandé)
python -m venv .venv
.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

## Lancement en mode développement

```bash
python main.py
```

Ou double-cliquer sur `run_dev.bat`.

---

## Compiler en .exe (Windows)

```bash
# Installer PyInstaller si nécessaire
pip install pyinstaller

# Lancer le build
build.bat
```

L'exécutable sera dans `dist/MediaFlow/MediaFlow.exe`.

> 💡 Placez `ffmpeg.exe` dans le dossier `dist/MediaFlow/` pour que l'application le détecte automatiquement.

---

## Structure du projet

```
mediaflow/
├── main.py                      # Point d'entrée
├── requirements.txt             # Dépendances Python
├── mediaflow.spec               # Config PyInstaller
├── run_dev.bat                  # Lancement dev
├── build.bat                    # Build .exe
├── assets/                      # Ressources (icônes, etc.)
├── config/
│   └── settings.py              # Gestionnaire de paramètres persistants
├── core/
│   ├── analyzer.py              # Analyse URL via yt-dlp
│   ├── converter.py             # Constantes formats audio
│   ├── downloader.py            # Moteur de téléchargement
│   └── ffmpeg_utils.py          # Détection et gestion FFmpeg
├── services/
│   ├── format_service.py        # Parsing et affichage des formats
│   └── history_service.py       # Historique des téléchargements
├── workers/
│   ├── analyze_worker.py        # Thread d'analyse en arrière-plan
│   └── download_worker.py       # Thread de téléchargement
├── ui/
│   ├── main_window.py           # Fenêtre principale
│   ├── styles/
│   │   └── theme.py             # Thème sombre QSS
│   └── widgets/
│       ├── url_bar.py           # Barre d'URL
│       ├── media_card.py        # Carte d'informations média
│       ├── format_selector.py   # Sélecteur qualité vidéo/audio
│       ├── progress_panel.py    # Panneau de progression
│       ├── log_panel.py         # Journal d'activité
│       ├── settings_dialog.py   # Dialogue des paramètres
│       └── history_panel.py     # Historique récent
└── utils/
    ├── file_utils.py            # Utilitaires fichiers
    └── logger.py                # Système de logs
```

## YouTube — Contournement de la détection anti-bot

YouTube peut bloquer les téléchargements avec le message **"Sign in to confirm you're not a bot"**. Ce projet utilise plusieurs techniques pour contourner ce problème :

1. **Client Android** (activé par défaut) : au lieu du client web classique, l'application se présente comme l'application Android officielle de YouTube. Cela suffit dans la grande majorité des cas.
2. **User-Agent mobile réaliste** : un en-tête User-Agent mobile (Pixel 5 / Android 11) est envoyé avec chaque requête.
3. **Fichier de cookies (optionnel)** : en dernier recours, si vous êtes toujours bloqué, vous pouvez exporter vos cookies YouTube depuis votre navigateur au format Netscape et les placer dans `cookies.txt` à la racine du projet. L'application les utilisera automatiquement.

> 💡 **Dans la plupart des cas, aucun cookie n'est nécessaire.** Le client Android contourne la détection anti-bot de manière transparente.

### Comment exporter ses cookies (si nécessaire)

1. Installez l'extension [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) dans votre navigateur
2. Connectez-vous à YouTube
3. Exportez les cookies au format Netscape
4. Collez le contenu dans le fichier `cookies.txt` à la racine du projet

## Limites connues

- Les contenus privés, protégés par mot de passe ou nécessitant une authentification ne sont pas supportés (par design)
- Les playlists sont ignorées (seule la première vidéo est traitée)
- La taille estimée des fichiers dépend des informations fournies par la plateforme source et peut être approximative
- Certaines plateformes peuvent modifier leurs API sans préavis, ce qui peut temporairement affecter la compatibilité

## Licence

Usage personnel uniquement. Respectez les conditions d'utilisation des plateformes concernées.
