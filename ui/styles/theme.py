"""
MediaFlow — Dark theme stylesheet.
A modern, premium dark UI theme for PySide6.
"""

# Colour palette
BG_DARK       = "#ffffff"
BG_PANEL      = "#f8f9fa"
BG_CARD       = "#ffffff"
BG_INPUT      = "#ffffff"
BG_HOVER      = "#f1f3f5"
BG_SELECTED   = "#e9ecef"

ACCENT        = "#e52e2e"
ACCENT_HOVER  = "#cc0000"
ACCENT_DARK   = "#b71c1c"

TEXT_PRIMARY   = "#212529"
TEXT_SECONDARY = "#495057"
TEXT_MUTED     = "#adb5bd"

SUCCESS       = "#28a745"
WARNING       = "#ffc107"
ERROR         = "#dc3545"

BORDER        = "#dee2e6"
BORDER_FOCUS  = ACCENT

RADIUS        = "6px"
RADIUS_SM     = "4px"
RADIUS_LG     = "12px"


def get_stylesheet() -> str:
    """Return the full application QSS stylesheet."""
    return f"""
    /* ── Global ────────────────────────────────────────────────── */
    QWidget {{
        background-color: {BG_DARK};
        color: {TEXT_PRIMARY};
        font-family: "Segoe UI", "Arial", sans-serif;
        font-size: 13px;
    }}

    /* ── Main Window ───────────────────────────────────────────── */
    QMainWindow {{
        background-color: {BG_DARK};
    }}

    /* ── Scroll Area ───────────────────────────────────────────── */
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}

    /* ── Labels ────────────────────────────────────────────────── */
    QLabel {{
        background: transparent;
        color: {TEXT_PRIMARY};
        padding: 0px;
    }}
    QLabel[class="heading"] {{
        font-size: 20px;
        font-weight: 700;
        color: {TEXT_PRIMARY};
    }}
    QLabel[class="subheading"] {{
        font-size: 14px;
        font-weight: 600;
        color: {TEXT_SECONDARY};
    }}
    QLabel[class="muted"] {{
        color: {TEXT_MUTED};
        font-size: 12px;
    }}

    /* ── LineEdit ───────────────────────────────────────────────── */
    QLineEdit {{
        background-color: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: {RADIUS};
        padding: 10px 14px;
        font-size: 14px;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT};
    }}
    QLineEdit:focus {{
        border-color: {ACCENT};
    }}
    QLineEdit:disabled {{
        background-color: {BG_PANEL};
        color: {TEXT_MUTED};
    }}

    /* ── Buttons ───────────────────────────────────────────────── */
    QPushButton {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: {RADIUS};
        padding: 9px 20px;
        font-size: 13px;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        border-color: {TEXT_MUTED};
    }}
    QPushButton:pressed {{
        background-color: {BG_SELECTED};
    }}
    QPushButton:disabled {{
        background-color: {BG_PANEL};
        color: {TEXT_MUTED};
        border-color: {BG_PANEL};
    }}

    QPushButton[class="primary"] {{
        background-color: {ACCENT};
        border: none;
        color: #ffffff;
    }}
    QPushButton[class="primary"]:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton[class="primary"]:pressed {{
        background-color: {ACCENT_DARK};
    }}
    QPushButton[class="primary"]:disabled {{
        background-color: {BG_HOVER};
        color: {TEXT_MUTED};
    }}

    QPushButton[class="success"] {{
        background-color: {SUCCESS};
        border: none;
        color: #0f0f14;
        font-weight: 700;
    }}
    QPushButton[class="success"]:hover {{
        background-color: #00e0db;
    }}
    QPushButton[class="success"]:disabled {{
        background-color: {BG_HOVER};
        color: {TEXT_MUTED};
    }}

    QPushButton[class="danger"] {{
        background-color: {ERROR};
        border: none;
        color: #ffffff;
    }}
    QPushButton[class="danger"]:hover {{
        background-color: #ff8787;
    }}

    /* ── ComboBox ──────────────────────────────────────────────── */
    QComboBox {{
        background-color: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: {RADIUS};
        padding: 8px 12px;
        font-size: 13px;
        color: {TEXT_PRIMARY};
        min-height: 22px;
    }}
    QComboBox:hover {{
        border-color: {TEXT_MUTED};
    }}
    QComboBox:focus {{
        border-color: {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {TEXT_SECONDARY};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_SM};
        selection-background-color: {ACCENT};
        selection-color: #ffffff;
        padding: 4px;
        outline: none;
    }}
    QComboBox QAbstractItemView::item {{
        padding: 6px 10px;
        min-height: 24px;
    }}

    /* ── CheckBox ──────────────────────────────────────────────── */
    QCheckBox {{
        spacing: 8px;
        font-size: 13px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {BORDER};
        background-color: {BG_INPUT};
    }}
    QCheckBox::indicator:hover {{
        border-color: {ACCENT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
    }}

    /* ── RadioButton ───────────────────────────────────────────── */
    QRadioButton {{
        spacing: 8px;
        font-size: 13px;
        background: transparent;
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 9px;
        border: 2px solid {BORDER};
        background-color: {BG_INPUT};
    }}
    QRadioButton::indicator:hover {{
        border-color: {ACCENT};
    }}
    QRadioButton::indicator:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
    }}

    /* ── ProgressBar ───────────────────────────────────────────── */
    QProgressBar {{
        background-color: {BG_INPUT};
        border: none;
        border-radius: {RADIUS_SM};
        height: 10px;
        text-align: center;
        font-size: 0px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT}, stop:1 {SUCCESS}
        );
        border-radius: {RADIUS_SM};
    }}

    /* ── TextEdit / PlainTextEdit (log) ────────────────────────── */
    QTextEdit, QPlainTextEdit {{
        background-color: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: {RADIUS};
        padding: 8px;
        font-family: "Cascadia Code", "Consolas", monospace;
        font-size: 12px;
        color: {TEXT_SECONDARY};
        selection-background-color: {ACCENT};
    }}

    /* ── GroupBox ───────────────────────────────────────────────── */
    QGroupBox {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_LG};
        margin-top: 12px;
        padding: 20px 16px 14px 16px;
        font-size: 13px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 6px;
        color: {TEXT_SECONDARY};
    }}

    /* ── TabWidget ──────────────────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: {RADIUS};
        background-color: {BG_PANEL};
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-bottom: none;
        border-top-left-radius: {RADIUS};
        border-top-right-radius: {RADIUS};
        padding: 8px 20px;
        margin-right: 2px;
        color: {TEXT_SECONDARY};
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background-color: {BG_PANEL};
        color: {ACCENT};
        border-bottom: 2px solid {ACCENT};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {BG_HOVER};
        color: {TEXT_PRIMARY};
    }}

    /* ── ScrollBar ─────────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: {BG_PANEL};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {BG_HOVER};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_MUTED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {BG_PANEL};
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BG_HOVER};
        border-radius: 4px;
        min-width: 30px;
    }}

    /* ── Tooltip ────────────────────────────────────────────────── */
    QToolTip {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 4px;
        color: {TEXT_PRIMARY};
        padding: 6px 10px;
        font-size: 12px;
    }}

    /* ── Splitter ───────────────────────────────────────────────── */
    QSplitter::handle {{
        background-color: {BORDER};
    }}

    /* ── Frame panels ──────────────────────────────────────────── */
    QFrame[class="card"] {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_LG};
        padding: 16px;
    }}
    """
