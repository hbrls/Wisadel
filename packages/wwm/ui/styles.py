"""
Style definitions for WWM UI

定义应用的全局样式、颜色、字体和间距常量。
"""

from PySide6.QtGui import QColor, QFont

# Color palette
COLORS = {
    "primary": "#0078D4",        # Primary blue
    "primary_dark": "#005A9E",   # Primary dark
    "primary_light": "#E6F2FB",  # Primary light
    "secondary": "#6B6B6B",      # Secondary gray
    "accent": "#107C10",         # Accent green
    "error": "#D13438",          # Error red
    "warning": "#FFB900",        # Warning yellow
    "success": "#107C10",        # Success green
    "text_primary": "#323130",   # Primary text
    "text_secondary": "#605E5C", # Secondary text
    "background": "#FFFFFF",     # Background
    "surface": "#F3F2F1",        # Surface color
    "border": "#EDEBE9",         # Border color
    "hover": "#F5F5F5",           # Hover state
    "selected": "#E5F1FB",       # Selected state
}

# Font definitions
FONTS = {
    "default": QFont("Segoe UI", 10),
    "title": QFont("Segoe UI", 14, QFont.Weight.Bold),
    "subtitle": QFont("Segoe UI", 12, QFont.Weight.Medium),
    "small": QFont("Segoe UI", 9),
    "monospace": QFont("Consolas", 10),
}

# Spacing constants
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
}

# Border radius
BORDER_RADIUS = {
    "none": 0,
    "sm": 2,
    "md": 4,
    "lg": 8,
}


def apply_stylesheet(app):
    """Apply the global stylesheet to the application.
    
    Args:
        app: QApplication instance
    """
    stylesheet = f"""
    /* Global styles */
    QMainWindow {{
        background-color: {COLORS['background']};
    }}
    
    QWidget {{
        font-family: "Segoe UI", sans-serif;
        font-size: 10pt;
        color: {COLORS['text_primary']};
    }}
    
    /* Tab widget */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        background-color: {COLORS['background']};
    }}
    
    QTabBar::tab {{
        background-color: {COLORS['surface']};
        padding: 8px 16px;
        margin-right: 2px;
        border: 1px solid {COLORS['border']};
        border-bottom: none;
    }}
    
    QTabBar::tab:selected {{
        background-color: {COLORS['background']};
        border-bottom: 2px solid {COLORS['primary']};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {COLORS['hover']};
    }}
    
    /* Push buttons */
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: {BORDER_RADIUS['md']}px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['primary_dark']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['primary_dark']};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['text_secondary']};
    }}
    
    /* Status bar */
    QStatusBar {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_secondary']};
        border-top: 1px solid {COLORS['border']};
    }}
    
    /* Scroll bars */
    QScrollBar:vertical {{
        width: 12px;
        background: {COLORS['surface']};
    }}
    
    QScrollBar::handle:vertical {{
        background: {COLORS['border']};
        min-height: 20px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['secondary']};
    }}
    
    QScrollBar:horizontal {{
        height: 12px;
        background: {COLORS['surface']};
    }}
    
    QScrollBar::handle:horizontal {{
        background: {COLORS['border']};
        min-width: 20px;
        border-radius: 6px;
    }}
    """
    app.setStyleSheet(stylesheet)
