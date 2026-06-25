"""
ScriptTab.py — 脚本执行 Tab

提供一个 Python 代码编辑器，可编写脚本调用 Notes 库，点击 Run 执行并查看输出。
"""

from __future__ import annotations
import sys
import io
import traceback

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QSplitter, QLabel,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor, QColor, QTextCharFormat, QSyntaxHighlighter

# ── 预导入的引擎模块（供 exec 环境使用） ──────────────────────────────────────
_SCRIPT_GLOBALS = {
    # Engine 核心
    'Chord': None,
    'Note': None,
    'Scale': None,
    'Interval': None,
    'Int': None,
    'JazzKey': None,
    # 音程常量
    'Per1': None, 'Unison': None, 'Min2': None, 'Maj2': None,
    'Min3': None, 'Maj3': None, 'Per4': None,
    'Aug4': None, 'Tritone': None, 'Dim5': None, 'Per5': None, 'Fifth': None,
    'Min6': None, 'Maj6': None, 'Min7': None, 'Maj7': None,
    'Oct': None, 'Octave': None,
    'Min9': None, 'Maj9': None, 'Min10': None, 'Maj10': None,
    'Per11': None, 'Aug11': None, 'Dim12': None,
    'Per12': None, 'Twelfth': None, 'Min13': None, 'Maj13': None,
    'Min14': None, 'Maj14': None, 'DuoOct': None,
    # 播放
    'play_chord': None,
    'play_note': None,
    'play_arpeggio': None,
}


def _inject_globals():
    """延迟导入引擎模块到全局字典"""
    from Engine.Note import Note
    from Engine.Chord import Chord
    from Engine.Scale import Scale
    from Engine.interval import Interval, Int
    from Engine.interval import (
        Per1, Min2, Maj2, Min3, Maj3, Per4,
        Aug4, Dim5, Per5,
        Min6, Maj6, Min7, Maj7, Oct,
        Min9, Maj9, Min10, Maj10, Per11, Aug11, Dim12,
        Per12, Min13, Maj13, Min14, Maj14, DuoOct,
        Tritone, Fifth, Octave, Twelfth, Unison,
    )
    from Engine.jazz_key import JazzKey
    from GUI.SoundPlayer import play_chord, play_note, play_arpeggio

    _SCRIPT_GLOBALS.update({
        'Note': Note, 'Chord': Chord, 'Scale': Scale,
        'Interval': Interval, 'Int': Int, 'JazzKey': JazzKey,
        'Per1': Per1, 'Min2': Min2, 'Maj2': Maj2,
        'Min3': Min3, 'Maj3': Maj3, 'Per4': Per4,
        'Aug4': Aug4, 'Dim5': Dim5, 'Per5': Per5,
        'Min6': Min6, 'Maj6': Maj6, 'Min7': Min7, 'Maj7': Maj7,
        'Oct': Oct,
        'Min9': Min9, 'Maj9': Maj9, 'Min10': Min10, 'Maj10': Maj10,
        'Per11': Per11, 'Aug11': Aug11, 'Dim12': Dim12,
        'Per12': Per12, 'Min13': Min13, 'Maj13': Maj13,
        'Min14': Min14, 'Maj14': Maj14, 'DuoOct': DuoOct,
        'Tritone': Tritone, 'Fifth': Fifth, 'Octave': Octave,
        'Twelfth': Twelfth, 'Unison': Unison,
        'play_chord': play_chord,
        'play_note': play_note,
        'play_arpeggio': play_arpeggio,
    })


class ScriptRunner(QThread):
    """在后台线程运行用户脚本，避免阻塞 UI"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, code: str, parent=None):
        super().__init__(parent)
        self.code = code

    def run(self):
        _inject_globals()
        local_ns: dict = {}

        # 捕获 stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            exec(self.code, _SCRIPT_GLOBALS, local_ns)
            output = sys.stdout.getvalue()
            if output:
                self.output_signal.emit(output.rstrip())
        except Exception:
            tb = traceback.format_exc()
            self.output_signal.emit(tb)
        finally:
            sys.stdout = old_stdout
            self.finished_signal.emit()


class PythonHighlighter(QSyntaxHighlighter):
    """简易 Python 语法高亮器"""

    _keywords = [
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
        'try', 'while', 'with', 'yield',
    ]
    _builtins = [
        'print', 'range', 'len', 'list', 'dict', 'set', 'str', 'int',
        'float', 'bool', 'tuple', 'enumerate', 'zip', 'map', 'filter',
        'sorted', 'reversed', 'type', 'isinstance', 'hasattr', 'getattr',
        'Chord', 'Note', 'Scale', 'Interval', 'Int', 'JazzKey',
        'play_chord', 'play_note', 'play_arpeggio',
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fmt_keyword = QTextCharFormat()
        self._fmt_keyword.setForeground(QColor('#569CD6'))
        self._fmt_keyword.setFontWeight(QFont.Bold)

        self._fmt_builtin = QTextCharFormat()
        self._fmt_builtin.setForeground(QColor('#DCDCAA'))

        self._fmt_string = QTextCharFormat()
        self._fmt_string.setForeground(QColor('#CE9178'))

        self._fmt_comment = QTextCharFormat()
        self._fmt_comment.setForeground(QColor('#6A9955'))
        self._fmt_comment.setFontItalic(True)

        self._fmt_number = QTextCharFormat()
        self._fmt_number.setForeground(QColor('#B5CEA8'))

        self._fmt_operator = QTextCharFormat()
        self._fmt_operator.setForeground(QColor('#D4D4D4'))

    def highlightBlock(self, text: str):
        # 注释
        import re
        # 单行注释
        for m in re.finditer(r'#.*$', text):
            self.setFormat(m.start(), m.end() - m.start(), self._fmt_comment)
        # 字符串（单引号、双引号）
        for m in re.finditer(r'(""".*?"""|\'\'\'.*?\'\'\'|".*?"|\'.*?\')', text):
            self.setFormat(m.start(), m.end() - m.start(), self._fmt_string)
        # 数字
        for m in re.finditer(r'\b\d+\.?\d*\b', text):
            self.setFormat(m.start(), m.end() - m.start(), self._fmt_number)
        # 关键字
        for kw in self._keywords:
            for m in re.finditer(rf'\b{re.escape(kw)}\b', text):
                self.setFormat(m.start(), m.end() - m.start(), self._fmt_keyword)
        # 内置/引擎名
        for b in self._builtins:
            for m in re.finditer(rf'\b{re.escape(b)}\b', text):
                self.setFormat(m.start(), m.end() - m.start(), self._fmt_builtin)


class ScriptTab(QWidget):
    """脚本编辑器 Tab——编写 Python 代码并运行"""

    _DEFAULT_CODE = (
        '# 编写调用 Notes 库的 Python 脚本\n'
        '# 可用对象: Chord, Note, Scale, JazzKey, play_chord, play_note\n'
        '# 示例:\n'
        'c = Chord("Cmaj7")\n'
        'print("和弦:", c)\n'
        'print("音名:", c.GetNames())\n'
        'print("音符:", c.Notes())\n'
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._runner: ScriptRunner | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── 顶部工具栏 ──
        toolbar = QHBoxLayout()
        title = QLabel("📝 Python 脚本编辑器")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #CCCCCC;")
        toolbar.addWidget(title)
        toolbar.addStretch()

        self._run_btn = QPushButton("▶  运行 (F5)")
        self._run_btn.setMinimumWidth(120)
        self._run_btn.setMinimumHeight(32)
        self._run_btn.setStyleSheet(self._button_style("#4CAF50", "#45A049"))
        self._run_btn.clicked.connect(self._run_script)
        toolbar.addWidget(self._run_btn)

        self._clear_btn = QPushButton("清空输出")
        self._clear_btn.setMinimumWidth(100)
        self._clear_btn.setMinimumHeight(32)
        self._clear_btn.setStyleSheet(self._button_style("#555555", "#666666"))
        self._clear_btn.clicked.connect(self._clear_output)
        toolbar.addWidget(self._clear_btn)

        layout.addLayout(toolbar)

        # ── 分割区域：编辑器 / 输出 ──
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background: #3C3C3C; height: 3px; }")

        # 编辑器
        self._editor = QTextEdit()
        self._editor.setFont(QFont("Consolas", 13))
        self._editor.setPlaceholderText("在这里编写 Python 脚本...")
        self._editor.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                padding: 8px;
                selection-background-color: #264F78;
            }
        """)
        self._editor.setPlainText(self._DEFAULT_CODE)
        # 语法高亮
        self._highlighter = PythonHighlighter(self._editor.document())

        splitter.addWidget(self._editor)

        # 输出区域
        self._output = QTextEdit()
        self._output.setFont(QFont("Consolas", 12))
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("输出将显示在这里...")
        self._output.setStyleSheet("""
            QTextEdit {
                background-color: #252526;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        splitter.addWidget(self._output)
        splitter.setSizes([420, 200])

        layout.addWidget(splitter)

    def _run_script(self):
        code = self._editor.toPlainText().strip()
        if not code:
            return

        self._run_btn.setEnabled(False)
        self._run_btn.setText("⏳ 运行中...")

        self._append_output("━━━ 运行 ━━━", color="#888888")

        self._runner = ScriptRunner(code)
        self._runner.output_signal.connect(self._on_output)
        self._runner.finished_signal.connect(self._on_finished)
        self._runner.start()

    def _on_output(self, text: str):
        self._append_output(text)

    def _on_finished(self):
        self._run_btn.setEnabled(True)
        self._run_btn.setText("▶  运行 (F5)")
        self._append_output("━━━ 完成 ━━━\n", color="#888888")

    def _append_output(self, text: str, color: str = "#CCCCCC"):
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(text + "\n", fmt)
        self._output.setTextCursor(cursor)
        # 滚动到底部
        self._output.ensureCursorVisible()

    def _clear_output(self):
        self._output.clear()

    @staticmethod
    def _button_style(bg: str, bg_hover: str) -> str:
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                padding: 4px 16px;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #999999;
            }}
        """
