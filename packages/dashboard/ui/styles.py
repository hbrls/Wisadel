"""Dashboard 样式定义"""

_tab_styles = """
    QPushButton[class="tab"] {
        background: #e8e8e8;
        color: #333;
        border: none;
        padding: 8px 16px;
    }
    QPushButton[class="tab"]:hover {
        background: #d0d0d0;
    }
    QPushButton[class="tab"]:pressed {
        background: #b8b8b8;
    }
    QPushButton[class="tab-active"] {
        background: #0078d4;
        color: white;
        border-left: 4px solid #0078d4;
        padding: 8px 16px;
    }
    QPushButton[class="tab-active"]:hover {
        background: #1084d8;
    }
    QPushButton[class="tab-active"]:pressed {
        background: #006cbf;
    }
"""

MAIN_STYLESHEET = """
    QMainWindow {
        background: #f5f5f5;
    }
    QLabel {
        color: #333;
    }
    QPushButton {
        padding: 8px 20px;
        border-radius: 4px;
        background: #0078d4;
        color: white;
        border: none;
    }
    QPushButton:hover {
        background: #1084d8;
    }
    QPushButton:pressed {
        background: #006cbf;
    }
    QPushButton:disabled {
        background: #cccccc;
    }
    QPushButton[class="default"] {
        background: #ffffff;
        color: #333333;
        border: 1px solid #cccccc;
    }
    QPushButton[class="default"]:hover {
        background: #f5f5f5;
    }
    QPushButton[class="default"]:pressed {
        background: #e8e8e8;
    }
""" + _tab_styles + """
    QGroupBox {
        border: 1px solid #cccccc;
        background-color: #f9f9f9;
        border-radius: 4px;
        margin-top: 8px;
        padding: 6px 10px;
        font-size: 9px;
        color: #666666;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
        background-color: #f5f5f5;
    }
    QGroupBox QLabel {
        color: #333333;
        font-family: Consolas, Monaco, monospace;
        font-size: 11px;
    }
"""
