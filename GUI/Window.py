"""
Window.py — 主窗口

包含两个 Tab：
  - 脚本 Tab（ScriptTab）：编写 Python 脚本调用 Notes 库
  - 和弦按钮 Tab（ChordTab）：12 级数和弦按钮矩阵，支持调性切换
"""

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor, QKeySequence
from PyQt5.QtWidgets import QShortcut

from GUI.ScriptTab import ScriptTab
from GUI.ChordTab import ChordTab


class MainWindow(QMainWindow):
    """Notes 库主窗口"""

    WINDOW_TITLE = "🎵 Notes — 音乐理论工具"
    DEFAULT_WIDTH = 1100
    DEFAULT_HEIGHT = 750

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._apply_dark_theme()

    def _setup_ui(self):
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # ── 中央 Tab 控件 ──
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3C3C3C;
                background-color: #1E1E1E;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #AAAAAA;
                padding: 8px 24px;
                margin-right: 2px;
                font-size: 13px;
                font-weight: bold;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border-bottom: 2px solid #4CAF50;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3C3C3C;
                color: #DDDDDD;
            }
        """)

        # Tab 1: 脚本
        self._script_tab = ScriptTab()
        self._tabs.addTab(self._script_tab, "📝 脚本")

        # Tab 2: 和弦按钮矩阵
        self._chord_tab = ChordTab()
        self._tabs.addTab(self._chord_tab, "🎹 和弦")

        layout.addWidget(self._tabs)

        # ── 快捷键 ──
        QShortcut(QKeySequence("F5"), self, self._script_tab._run_script)

    def _apply_dark_theme(self):
        """应用深色主题"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, QColor(204, 204, 204))
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ToolTipBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ToolTipText, QColor(204, 204, 204))
        palette.setColor(QPalette.Text, QColor(204, 204, 204))
        palette.setColor(QPalette.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ButtonText, QColor(204, 204, 204))
        palette.setColor(QPalette.Highlight, QColor(38, 79, 120))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)
        self.setStyleSheet("QMainWindow { background-color: #1E1E1E; }")


def run():
    """启动 GUI 应用程序"""
    import sys
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run()

