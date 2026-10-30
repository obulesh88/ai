"""HEMA futuristic theme: dark cyberpunk, blue/cyan neon, glass panels."""

BG_DEEP = "#04060c"
BG_NAVY = "#0a1220"
PANEL = "rgba(10, 22, 38, 180)"
PANEL_SOLID = "#0b1626"
BORDER = "rgba(0, 229, 255, 90)"
CYAN = "#00e5ff"
BLUE = "#2f6bff"
VIOLET = "#7b5cff"
TEXT = "#d8f6ff"
TEXT_DIM = "#6f9bb3"
OK = "#28e0a6"
WARN = "#ffc457"
DANGER = "#ff4d6d"

FONT_UI = "Segoe UI, Inter, Helvetica Neue, Arial"
FONT_MONO = "Cascadia Mono, Consolas, DejaVu Sans Mono, monospace"

RADIUS = 14


def palette():
    """Dark QPalette so native-drawn bits (spin/combo arrows, menus) match the theme."""
    from PySide6.QtGui import QColor, QPalette
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG_NAVY))
    pal.setColor(QPalette.WindowText, QColor(TEXT))
    pal.setColor(QPalette.Base, QColor("#070f1a"))
    pal.setColor(QPalette.AlternateBase, QColor(PANEL_SOLID))
    pal.setColor(QPalette.Text, QColor(TEXT))
    pal.setColor(QPalette.Button, QColor("#12243a"))
    pal.setColor(QPalette.ButtonText, QColor(TEXT))
    pal.setColor(QPalette.BrightText, QColor("#ffffff"))
    pal.setColor(QPalette.Highlight, QColor(BLUE))
    pal.setColor(QPalette.HighlightedText, QColor("#04121a"))
    pal.setColor(QPalette.ToolTipBase, QColor(PANEL_SOLID))
    pal.setColor(QPalette.ToolTipText, QColor(TEXT))
    pal.setColor(QPalette.PlaceholderText, QColor(TEXT_DIM))
    return pal


def stylesheet() -> str:
    return f"""
    QWidget {{
        color: {TEXT};
        font-family: "{FONT_UI}";
        font-size: 13px;
    }}
    QMainWindow, #RootBackground {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {BG_DEEP}, stop:0.45 {BG_NAVY}, stop:1 {BG_DEEP});
    }}
    QLabel#AppTitle {{
        color: {CYAN};
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 6px;
    }}
    QLabel#AppSubtitle {{ color: {TEXT_DIM}; font-size: 11px; letter-spacing: 3px; }}
    QLabel#PageTitle {{
        color: {TEXT};
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 1px;
    }}
    QLabel#PageHint {{ color: {TEXT_DIM}; font-size: 11px; }}
    QLabel#Greeting {{
        color: {TEXT};
        font-size: 18px;
        font-weight: 500;
        letter-spacing: 0px;
    }}
    QLabel#RailLabel {{ color: {TEXT_DIM}; font-size: 9px; letter-spacing: 2px; font-weight: 600; }}
    QLabel#RailValue {{ color: {TEXT}; font-size: 11px; font-family: "{FONT_MONO}"; }}
    QPushButton#NavButton {{
        text-align: left;
        background: transparent;
        border: none;
        border-left: 2px solid transparent;
        border-radius: 8px;
        padding: 9px 12px;
        color: {TEXT_DIM};
        font-size: 12px;
    }}
    QPushButton#NavButton:hover {{
        background: rgba(0, 229, 255, 20);
        color: {TEXT};
    }}
    QPushButton#NavButton:checked {{
        color: {CYAN};
        background: rgba(0, 229, 255, 26);
        border-left: 2px solid {CYAN};
        font-weight: 600;
    }}
    QPushButton#Primary {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {BLUE}, stop:1 {CYAN});
        color: #04121a;
        font-weight: 700;
        border: none;
    }}
    QPushButton#Ghost {{
        background: transparent;
        border: 1px solid rgba(0, 229, 255, 45);
        color: {TEXT_DIM};
        padding: 7px 12px;
    }}
    QPushButton#Ghost:hover {{ color: {CYAN}; border-color: {CYAN}; }}
    QPushButton#Ghost:disabled {{ color: rgba(111,155,179,90); border-color: rgba(0,229,255,25); }}
    QPushButton#Small {{
        padding: 4px 10px;
        font-size: 10px;
        border-radius: 8px;
        background: rgba(20, 44, 70, 120);
    }}
    QLabel#PanelTitle {{
        color: {CYAN};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 2px;
    }}
    QLabel#StatusPill {{
        color: {TEXT};
        background: rgba(0, 229, 255, 26);
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 4px 10px;
        font-size: 11px;
    }}
    QPushButton {{
        color: {TEXT};
        background: rgba(20, 44, 70, 140);
        border: 1px solid rgba(0, 229, 255, 60);
        border-radius: 10px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{ background: rgba(0, 229, 255, 40); border-color: {CYAN}; }}
    QPushButton:pressed {{ background: rgba(0, 229, 255, 70); }}
    QPushButton#QuickTile {{
        text-align: left;
        padding: 12px 14px;
        font-size: 13px;
        font-weight: 600;
        background: rgba(14, 32, 52, 150);
    }}
    QPushButton#SendButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {BLUE}, stop:1 {CYAN});
        color: #04121a;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
    }}
    QPushButton#SendButton:hover {{ background: {CYAN}; }}
    QPushButton#SendButton:disabled {{ background: rgba(47,107,255,70); color: {TEXT_DIM}; }}
    QLineEdit {{
        background: rgba(6, 14, 24, 200);
        border: 1px solid rgba(0, 229, 255, 60);
        border-radius: 10px;
        padding: 10px 12px;
        selection-background-color: {BLUE};
    }}
    QLineEdit:focus {{ border: 1px solid {CYAN}; }}
    QComboBox {{
        background: rgba(6, 14, 24, 200);
        border: 1px solid rgba(0, 229, 255, 60);
        border-radius: 8px;
        padding: 6px 10px;
    }}
    QComboBox QAbstractItemView {{
        background: {PANEL_SOLID};
        border: 1px solid {BORDER};
        selection-background-color: rgba(0, 229, 255, 70);
    }}
    QTextBrowser, QPlainTextEdit, QTextEdit, QListWidget {{
        background: rgba(4, 10, 18, 140);
        border: 1px solid rgba(0, 229, 255, 28);
        border-radius: 10px;
        padding: 6px;
        font-family: "{FONT_MONO}";
    }}
    QListWidget#Plain {{
        background: transparent;
        border: none;
        padding: 0px;
        font-family: "{FONT_UI}";
        font-size: 11px;
    }}
    QListWidget#Plain::item {{ padding: 4px 2px; }}
    QListWidget#Plain::item:selected {{ background: rgba(0, 229, 255, 40); border-radius: 6px; }}
    QListWidget::item {{ padding: 5px 4px; border-bottom: 1px solid rgba(0,229,255,18); }}
    QListWidget::item:selected {{ background: rgba(0, 229, 255, 50); border-radius: 6px; }}
    QScrollBar:vertical {{ background: transparent; width: 7px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: rgba(0, 229, 255, 30); border-radius: 3px; min-height: 24px; }}
    QScrollBar::handle:vertical:hover {{ background: rgba(0, 229, 255, 90); }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 6px; margin: 0px; }}
    QScrollBar::handle:horizontal {{ background: rgba(0, 229, 255, 50); border-radius: 3px; min-width: 24px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    QSpinBox, QDoubleSpinBox {{
        background: rgba(6, 14, 24, 200);
        border: 1px solid rgba(0, 229, 255, 60);
        border-radius: 8px;
        padding: 5px 8px;
        min-height: 24px;
        color: {TEXT};
        selection-background-color: {BLUE};
    }}
    QSpinBox:focus {{ border: 1px solid {CYAN}; }}
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 16px;
        background: rgba(0, 229, 255, 20);
        border: none;
        border-radius: 4px;
        margin: 2px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: rgba(0, 229, 255, 60); }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QTabWidget::pane {{ border: 1px solid rgba(0, 229, 255, 40); border-radius: 12px; top: -1px; }}
    QTabBar::tab {{
        color: {TEXT_DIM};
        background: transparent;
        padding: 7px 10px;
        border-bottom: 2px solid transparent;
        font-size: 10px;
        letter-spacing: 1px;
    }}
    QTabBar::tab:selected {{ color: {CYAN}; border-bottom: 2px solid {CYAN}; }}
    QProgressBar {{
        background: rgba(6, 14, 24, 200);
        border: 1px solid rgba(0, 229, 255, 45);
        border-radius: 6px;
        height: 12px;
        text-align: center;
        font-size: 9px;
        color: {TEXT};
    }}
    QProgressBar::chunk {{
        border-radius: 5px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {BLUE}, stop:1 {CYAN});
    }}
    QLabel#ApprovalBanner {{
        background: rgba(255, 196, 87, 40);
        border: 1px solid {WARN};
        border-radius: 10px;
        padding: 8px 12px;
        color: {TEXT};
    }}
    QGroupBox {{
        border: 1px solid rgba(0, 229, 255, 40);
        border-radius: 10px;
        margin-top: 14px;
        padding: 10px;
    }}
    QGroupBox::title {{ color: {CYAN}; subcontrol-origin: margin; left: 12px; padding: 0 4px; }}
    QStatusBar {{ color: {TEXT_DIM}; background: rgba(4, 10, 18, 200); }}
    QDialog {{ background: {BG_NAVY}; }}
    QToolTip {{
        background: {PANEL_SOLID};
        color: {TEXT};
        border: 1px solid {BORDER};
        padding: 4px;
    }}
    """
