"""
ChordTab.py — 和弦按钮矩阵 Tab

顶部：主音选择器
主体：12 列（根音半音上行）× 6 行（和弦类型）的按钮矩阵，
      按下后解析并播放对应和弦。

行定义：
  大七 | 小七 | 属七 | 半减七(m7b5) | 增七 | 减七
"""
from __future__ import annotations

import json
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QComboBox, QLabel, QScrollArea,
    QSizePolicy, QFrame, QApplication,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox, QLineEdit,
)
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

import re

from Engine.Note import Note, _SHARP_NAMES
from Engine.Chord import Chord
from GUI.SoundPlayer import play_chord, stop_all

# ── 和弦类型行定义 (中文标签, chord_type后缀, 颜色组) ──────────────────────
_CHORD_TYPE_ROWS = [
    # 七和弦（大小属半减增减）
    ("大七",     "maj7",  "seventh"),
    ("小七",     "m7",    "seventh"),
    ("属七",     "7",     "seventh"),
    ("半减七",   "m7b5",  "seventh"),
    ("增七",     "aug7",  "seventh"),
    ("减七",     "dim7",  "seventh"),
]

# ── 可用调性 ─────────────────────────────────────────────────────────────────
_NOTE_NAMES = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F',
               'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']

_NOTE_MAP: dict[str, str] = {
    'C': 'C', 'C#/Db': 'C#', 'D': 'D', 'D#/Eb': 'D#',
    'E': 'E', 'F': 'F', 'F#/Gb': 'F#', 'G': 'G',
    'G#/Ab': 'G#', 'A': 'A', 'A#/Bb': 'A#', 'B': 'B',
}

# ── 级数名（列标） ────────────────────────────────────────────────────────────
_DEGREE_NAMES = ['Ⅰ', '♭Ⅱ', 'Ⅱ', '♭Ⅲ', 'Ⅲ', 'Ⅳ',
                 '♯Ⅳ', 'Ⅴ', '♭Ⅵ', 'Ⅵ', '♭Ⅶ', 'Ⅶ']

# ── 度数解析器 ─────────────────────────────────────────────────────────────

# Major scale degree → semitone offset from tonic (referential)
_DEGREE_TO_SEMITONE: dict[str, int] = {
    'I': 0, '1': 0,
    'II': 2, '2': 2,
    'III': 4, '3': 4,
    'IV': 5, '4': 5,
    'V': 7, '5': 7,
    'VI': 9, '6': 9,
    'VII': 11, '7': 11,
}


def _parse_degree_part(part: str, tonic_pc: int) -> int:
    """Parse a single degree (e.g. 'V', 'bVII', '3', '#4') → absolute pitch class."""
    m = re.match(r'^([b#]+)(.*)$', part.strip())
    if m:
        alteration_str, degree_str = m.group(1), m.group(2).upper()
    else:
        alteration_str, degree_str = '', part.strip().upper()

    alt_offset = 0
    for ch in alteration_str:
        if ch == 'b':
            alt_offset -= 1
        elif ch == '#':
            alt_offset += 1

    base_offset = _DEGREE_TO_SEMITONE.get(degree_str)
    if base_offset is None:
        raise ValueError(f"无法识别的度数: {degree_str}")

    return (tonic_pc + base_offset + alt_offset) % 12


def _resolve_degree_root_bass(expr: str, key_note: str) -> tuple[str | None, str | None]:
    """Resolve degree slash expression to (root_note, bass_note_or_None).

    Slash chords (e.g. '3/7', 'V/IV') are interpreted as "X with bass Y"
    — both chord degree and bass degree are resolved independently against
    the tonic.  Non-slash expressions return (root, None).
    """
    try:
        tonic_pc = Note(key_note)._pitch % 12
        if '/' in expr:
            left, right = expr.split('/', 1)
            chord_pc = _parse_degree_part(left, tonic_pc)
            bass_pc = _parse_degree_part(right, tonic_pc)
            return (
                _SHARP_NAMES[chord_pc % 12],
                _SHARP_NAMES[bass_pc % 12],
            )
        else:
            pc = _parse_degree_part(expr, tonic_pc)
            return (_SHARP_NAMES[pc % 12], None)
    except Exception:
        return (None, None)


def _format_degree_chord(expr: str, suffix: str) -> str:
    """Format degree expression with suffix: '3/7' + 'm' → '3m/7', 'bVII' + '7' → 'bVII7'."""
    if '/' in expr:
        left, right = expr.split('/', 1)
        return f'{left}{suffix}/{right}'
    return f'{expr}{suffix}'


# ── 默认度数型和弦 ──────────────────────────────────────────────────────────

_DEFAULT_DEGREE_CHORDS: list[dict] = [
    {"label": "4/5",  "degree_expr": "4/5",  "chord_suffix": ""},
    {"label": "5/6",  "degree_expr": "5/6",  "chord_suffix": ""},
    {"label": "5/4",  "degree_expr": "5/4",  "chord_suffix": ""},
    {"label": "3/7",  "degree_expr": "3/7",  "chord_suffix": ""},
]

# ── 可选和弦后缀（供添加/编辑行使用） ──────────────────────────────────────────
_COMMON_CHORD_SUFFIXES = [
    '', 'm', 'aug', 'dim', '5',
    'maj7', 'M7', 'm7', '7', 'mM7', 'dim7', 'm7b5', 'aug7', 'augM7',
    '6', 'm6', 'aug6', 'dim6', '6/9',
    'maj9', 'm9', '9', 'aug9', 'dim9',
    'maj11', 'm11', '11', 'aug11', 'dim11',
    'maj13', 'm13', '13', 'aug13', 'dim13',
    'sus2', 'sus4',
]

# ── 颜色方案 ─────────────────────────────────────────────────────────────────
_BTN_BG       = '#3A3A3A'
_BTN_BG_HOVER = '#4E4E4E'
_HIGHLIGHT    = '#FFD54F'


class ChordCellButton(QPushButton):
    """单个和弦格子按钮，支持可渐变的高亮边框"""

    hovered_with_reasons = pyqtSignal(list)

    def __init__(self, chord: Chord, parent=None, display_name: str | None = None):
        super().__init__(parent)
        self._chord = chord

        # 高亮状态
        self._highlighted = False
        self._highlight_colors: list[QColor] = []
        self._highlight_index = 0
        self._highlight_timer: QTimer | None = None
        self._highlight_reasons: list[dict] = []

        # 外部播放回调: callable(chord) → 若设置则替代默认播放逻辑
        self._play_callback = None

        _display = display_name if display_name is not None else str(chord)
        self.setText(_display)
        self.setMinimumSize(76, 40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFont(QFont("Consolas", 10))
        self.setCursor(Qt.PointingHandCursor)

        notes_str = ' '.join(str(n) for n in chord.Notes())
        self.setToolTip(f"{chord}\n{notes_str}")

        self.clicked.connect(self._on_click)
        self._apply_style()

    def set_play_callback(self, callback):
        """设置外部播放回调 callback(chord)。

        设置后，按钮点击时将调用此回调而非默认的 play_chord 逻辑。
        """
        self._play_callback = callback

    # ── 高亮 API ─────────────────────────────────────────────────────────

    def set_highlight(self, colors: list[str] | None = None,
                     reasons: list[dict] | None = None):
        """开启高亮。

        Args:
            colors: 高亮颜色列表（如 ['#FFD54F', '#FF6B6B', '#4ECDC4']）。
                    不传或传 None 时默认白色高亮。
                    多个颜色时按时间自动渐变切换。
            reasons: 高亮原因列表，每项为 {'name': str, 'description': str}。
        """
        if not colors:
            colors = ['#FFFFFF']

        self._highlight_colors = [QColor(c) for c in colors]
        self._highlight_index = 0
        self._highlighted = True
        self._highlight_reasons = reasons or []

        if len(self._highlight_colors) > 1:
            if self._highlight_timer is None:
                self._highlight_timer = QTimer(self)
                self._highlight_timer.timeout.connect(self._cycle_highlight)
            self._highlight_timer.start(800)
        else:
            self._stop_timer()

        self.update()

    def clear_highlight(self):
        """关闭高亮。"""
        self._highlighted = False
        self._highlight_reasons = []
        self._stop_timer()
        self.update()

    def is_highlighted(self) -> bool:
        """返回当前是否处于高亮状态。"""
        return self._highlighted

    # ── 鼠标悬浮 ─────────────────────────────────────────────────────────

    def enterEvent(self, event):
        """鼠标进入按钮时，若处于高亮状态则发射 reasons 信号。"""
        super().enterEvent(event)
        if self._highlighted and self._highlight_reasons:
            self.hovered_with_reasons.emit(self._highlight_reasons)

    def leaveEvent(self, event):
        """鼠标离开按钮时，发射空列表清空状态栏。"""
        super().leaveEvent(event)
        if self._highlighted and self._highlight_reasons:
            self.hovered_with_reasons.emit([])

    # ── 内部 ─────────────────────────────────────────────────────────────

    def _stop_timer(self):
        if self._highlight_timer and self._highlight_timer.isActive():
            self._highlight_timer.stop()

    def _cycle_highlight(self):
        self._highlight_index = (self._highlight_index + 1) % len(self._highlight_colors)
        self.update()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {_BTN_BG}; color: #CCCCCC;
                border: 2px solid {_BTN_BG_HOVER}; border-radius: 6px;
                font-weight: bold; padding: 2px 1px;
            }}
            QPushButton:hover {{ background-color: {_BTN_BG_HOVER}; border-color: #888888; }}
            QPushButton:pressed {{ border-color: {_HIGHLIGHT}; border-width: 3px; }}
        """)

    def _on_click(self):
        if self._play_callback is not None:
            self._play_callback(self._chord)
        else:
            pitches = [n._pitch for n in self._chord.Notes()]
            play_chord(pitches)
        QTimer.singleShot(300, self._apply_style)

    def rebuild(self, root_name: str, chord_suffix: str,
                display_name: str | None = None):
        try:
            self._chord = Chord(f"{root_name}{chord_suffix}")
        except Exception:
            self._chord = Chord("C")
        _display = display_name if display_name is not None else str(self._chord)
        self.setText(_display)
        self.setToolTip(
            f"{self._chord}\n{' '.join(str(n) for n in self._chord.Notes())}"
        )

    # ── 绘制 ─────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        """先走默认绘制，再叠加内收渐变高亮边框。"""
        super().paintEvent(event)

        if not self._highlighted or not self._highlight_colors:
            return

        color = self._highlight_colors[self._highlight_index % len(self._highlight_colors)]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 从外向内绘制多层递减透明度的圆角矩形，形成内收渐变边缘
        border_width = 10
        for i in range(border_width):
            alpha = int(200 * (1.0 - i / border_width))
            c = QColor(color)
            c.setAlpha(max(alpha, 0))
            pen = QPen(c, 2.5)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            rect = QRectF(self.rect()).adjusted(i, i, -i, -i)
            painter.drawRoundedRect(rect, 6.0 - i * 0.5, 6.0 - i * 0.5)

        painter.end()


# ── 和弦行编辑对话框 ─────────────────────────────────────────────────────────

class ChordRowDialog(QDialog):
    """用于添加或编辑和弦类型行的对话框。"""

    def __init__(self, parent=None, edit_label: str = '',
                 edit_suffix: str = '', edit_group: str = 'seventh'):
        super().__init__(parent)
        self.setWindowTitle('编辑和弦行' if edit_label else '添加和弦行')
        self.setMinimumWidth(360)
        self.setStyleSheet(_dialog_style())

        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        # 中文标签
        self._label_edit = QLineEdit(edit_label)
        self._label_edit.setPlaceholderText('如: 大七')
        self._label_edit.setMinimumHeight(28)
        layout.addRow(QLabel('显示名称:'), self._label_edit)

        # 和弦后缀 — 下拉 + 自定义
        suffix_layout = QHBoxLayout()
        self._suffix_combo = QComboBox()
        self._suffix_combo.setEditable(True)
        self._suffix_combo.addItems(_COMMON_CHORD_SUFFIXES)
        if edit_suffix:
            idx = self._suffix_combo.findText(edit_suffix)
            if idx >= 0:
                self._suffix_combo.setCurrentIndex(idx)
            else:
                self._suffix_combo.setCurrentText(edit_suffix)
        self._suffix_combo.setMinimumHeight(28)
        self._suffix_combo.setStyleSheet(_combo_style())
        suffix_layout.addWidget(self._suffix_combo)
        layout.addRow(QLabel('和弦后缀:'), suffix_layout)

        # 分组
        self._group_combo = QComboBox()
        self._group_combo.addItems(['seventh', 'triad', 'extended', 'suspended', 'other'])
        if edit_group:
            idx = self._group_combo.findText(edit_group)
            if idx >= 0:
                self._group_combo.setCurrentIndex(idx)
        self._group_combo.setMinimumHeight(28)
        self._group_combo.setStyleSheet(_combo_style())
        layout.addRow(QLabel('分组:'), self._group_combo)

        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def _validate_and_accept(self):
        label = self._label_edit.text().strip()
        suffix = self._suffix_combo.currentText().strip()
        if not label:
            QMessageBox.warning(self, '输入错误', '显示名称不能为空。')
            return
        if not suffix:
            QMessageBox.warning(self, '输入错误', '和弦后缀不能为空。')
            return
        self.accept()

    def get_result(self) -> tuple[str, str, str]:
        """返回 (显示名称, 和弦后缀, 分组)。"""
        return (
            self._label_edit.text().strip(),
            self._suffix_combo.currentText().strip(),
            self._group_combo.currentText().strip(),
        )


# ── 度数和弦编辑对话框 ─────────────────────────────────────────────────────

class DegreeChordDialog(QDialog):
    """用于添加或编辑度数和弦（如 V/IV, 3/7）的对话框。"""

    _COMMON_SUFFIXES = [
        '7', 'maj7', 'm7', 'm7b5', 'dim7', 'aug7',
        '', 'm', 'aug', 'dim', '6', 'm6',
        '9', 'maj9', 'm9', '11', '13', 'sus2', 'sus4',
    ]

    def __init__(self, parent=None, edit_data: dict | None = None):
        super().__init__(parent)
        is_edit = edit_data is not None
        self.setWindowTitle('编辑度数和弦' if is_edit else '添加度数和弦')
        self.setMinimumWidth(420)
        self.setStyleSheet(_dialog_style())

        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        # 显示标签
        self._label_edit = QLineEdit(edit_data['label'] if is_edit else '')
        self._label_edit.setPlaceholderText('留空则自动使用度数表达式')
        self._label_edit.setMinimumHeight(28)
        layout.addRow(QLabel('显示标签:'), self._label_edit)

        # 度数表达式
        self._expr_edit = QLineEdit(edit_data['degree_expr'] if is_edit else '')
        self._expr_edit.setPlaceholderText('如: V/IV, bVII, 3/7, #IV/V')
        self._expr_edit.setMinimumHeight(28)
        self._expr_edit.setToolTip(
            '罗马数字(I-VII)或阿拉伯数字(1-7)。\n'
            '斜线 "/" 表示副属/借用关系：V/IV = IV的属和弦。\n'
            '变音前缀: b=降, #=升。\n'
            '示例: V/IV, bVII, #IV/V, 3/7'
        )
        layout.addRow(QLabel('度数表达式:'), self._expr_edit)

        # 和弦后缀
        suffix_layout = QHBoxLayout()
        self._suffix_combo = QComboBox()
        self._suffix_combo.setEditable(True)
        self._suffix_combo.addItems(self._COMMON_SUFFIXES)
        if is_edit:
            suffix = edit_data.get('chord_suffix', '7')
            idx = self._suffix_combo.findText(suffix)
            if idx >= 0:
                self._suffix_combo.setCurrentIndex(idx)
            else:
                self._suffix_combo.setCurrentText(suffix)
        else:
            self._suffix_combo.setCurrentText('7')
        self._suffix_combo.setMinimumHeight(28)
        self._suffix_combo.setStyleSheet(_combo_style())
        suffix_layout.addWidget(self._suffix_combo)
        layout.addRow(QLabel('和弦后缀:'), suffix_layout)

        # 预览
        self._preview_label = QLabel('')
        self._preview_label.setStyleSheet(
            'color: #81C784; font-size: 12px; font-family: Consolas;'
        )
        layout.addRow(QLabel('预览:'), self._preview_label)

        # 实时预览
        self._expr_edit.textChanged.connect(self._update_preview)
        self._suffix_combo.currentTextChanged.connect(self._update_preview)
        self._update_preview()

        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def _update_preview(self):
        expr = self._expr_edit.text().strip()
        suffix = self._suffix_combo.currentText().strip()
        if not expr:
            self._preview_label.setText('(输入度数表达式)')
            return
        root, bass = _resolve_degree_root_bass(expr, 'C')
        if root is None:
            self._preview_label.setText('⚠ 无法解析度数表达式')
        else:
            try:
                chord_str = f"{root}{suffix}/{bass}" if bass else f"{root}{suffix}"
                ch = Chord(chord_str)
                notes = ' '.join(str(n) for n in ch.Notes())
                formatted = _format_degree_chord(expr, suffix)
                self._preview_label.setText(f"{formatted}  C调 → {ch}  [{notes}]")
            except Exception:
                self._preview_label.setText(f"{_format_degree_chord(expr, suffix)} (无法构建和弦)")

    def _validate_and_accept(self):
        expr = self._expr_edit.text().strip()
        if not expr:
            QMessageBox.warning(self, '输入错误', '度数表达式不能为空。')
            return
        # 验证解析
        root, _bass = _resolve_degree_root_bass(expr, 'C')
        if root is None:
            QMessageBox.warning(
                self, '解析错误',
                f'无法解析度数表达式 "{expr}"。\n'
                '请使用罗马数字(I-VII)或阿拉伯数字(1-7)，\n'
                '可选前缀 b/#，可选斜线如 V/IV。'
            )
            return
        if not self._label_edit.text().strip():
            self._label_edit.setText(expr)
        suffix = self._suffix_combo.currentText().strip()
        if not suffix:
            QMessageBox.warning(self, '输入错误',
                              '和弦后缀不能为空（至少填 "" 表示大三和弦）。')
            return
        self.accept()

    def get_result(self) -> dict:
        return {
            "label": self._label_edit.text().strip(),
            "degree_expr": self._expr_edit.text().strip(),
            "chord_suffix": self._suffix_combo.currentText().strip(),
        }


def _dialog_style() -> str:
    return """
        QDialog {
            background-color: #2B2B2B; color: #CCCCCC;
        }
        QLabel {
            color: #CCCCCC; font-size: 13px; font-weight: bold;
        }
        QLineEdit {
            background-color: #3A3A3A; color: #CCCCCC;
            border: 1px solid #555555; border-radius: 4px;
            padding: 4px 8px; font-size: 13px;
        }
        QLineEdit:focus { border-color: #FFD54F; }
        QDialogButtonBox QPushButton {
            background-color: #3A3A3A; color: #CCCCCC;
            border: 1px solid #555555; border-radius: 4px;
            padding: 6px 20px; font-size: 13px; min-width: 80px;
        }
        QDialogButtonBox QPushButton:hover {
            background-color: #4E4E4E; border-color: #FFD54F;
        }
    """


class ChordTab(QWidget):
    """和弦按钮矩阵 Tab"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_key = 'C'
        self._cells: list[list[ChordCellButton]] = []
        self._root_names: list[str] = []
        self._transition_knowledge: list[dict] = []
        # 和弦类型行 — 可增删改的实例副本
        self._chord_type_rows: list[tuple[str, str, str]] = list(_CHORD_TYPE_ROWS)
        # 记录行标签控件，用于删除行时清理
        self._row_label_widgets: list[QWidget] = []
        # 度数型和弦 — 可增删改的特殊斜线和弦列表
        self._degree_chords: list[dict] = [dict(d) for d in _DEFAULT_DEGREE_CHORDS]
        self._degree_cells: list[ChordCellButton] = []
        self._degree_row_widgets: list[QWidget] = []
        # 记录上一次按下的和弦 voicing，用于 ALT + MinVoiceLeading
        self._prev_voicing: list | None = None
        self._load_transition_knowledge()
        self._setup_ui()
        self._rebuild_all()

        # 全局事件过滤器：无论焦点在哪个控件，空格抬起都停止所有音
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        """全局事件过滤器 — 监听空格按下停止所有音符。"""
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Space:
            # 避免在文本编辑框中误触发
            from PyQt5.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit
            if not isinstance(obj, (QLineEdit, QTextEdit, QPlainTextEdit)):
                stop_all()
                return True  # 吃掉事件，防止按钮把空格当作点击二次触发
        return super().eventFilter(obj, event)

    # ── 和弦过渡知识库 ──────────────────────────────────────────────────────

    def _load_transition_knowledge(self):
        """从 JSON 文件加载和弦过渡知识库。"""
        json_path = os.path.join(os.path.dirname(__file__), 'ChordTransitionKnowledge.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._transition_knowledge = data.get('ChordTransitionKnowledge', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self._transition_knowledge = []
            print(f"[ChordTab] 加载过渡知识库失败: {e}")

    # ── UI ───────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 标题
        title = QLabel("🎹 和弦按钮矩阵")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #CCCCCC;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 调性选择栏
        key_bar = QHBoxLayout()
        key_bar.setSpacing(12)
        lbl = QLabel("主音 (Tonic):")
        lbl.setStyleSheet("color: #CCCCCC; font-size: 13px; font-weight: bold;")
        key_bar.addWidget(lbl)

        self._key_combo = QComboBox()
        self._key_combo.addItems(_NOTE_NAMES)
        self._key_combo.setCurrentText('C')
        self._key_combo.setMinimumWidth(100)
        self._key_combo.setStyleSheet(_combo_style())
        self._key_combo.currentTextChanged.connect(self._on_key_changed)
        key_bar.addWidget(self._key_combo)

        key_bar.addStretch()

        self._key_display = QLabel("C")
        self._key_display.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #FFD54F;"
            "background-color: #333333; border-radius: 6px; padding: 6px 22px;"
        )
        self._key_display.setAlignment(Qt.AlignCenter)
        key_bar.addWidget(self._key_display)
        layout.addLayout(key_bar)

        # 图例
        leg = QHBoxLayout()
        d = QLabel("●")
        d.setStyleSheet("color: #888888; font-size: 14px;")
        leg.addWidget(d)
        t = QLabel("按钮矩阵")
        t.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        leg.addWidget(t)
        leg.addStretch()
        layout.addLayout(leg)

        # 滚动区域（包住矩阵）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        matrix = QWidget()
        self._grid = QGridLayout(matrix)
        self._grid.setSpacing(4)
        self._grid.setContentsMargins(4, 4, 4, 4)

        scroll.setWidget(matrix)
        layout.addWidget(scroll, stretch=1)

        # 底部提示
        hint = QLabel("💡 点击按钮播放和弦 | 上方切换主音自动更新矩阵")
        hint.setStyleSheet("color: #888888; font-size: 12px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        # 状态栏
        self._status_label = QLabel()
        self._status_label.setStyleSheet(
            "color: #B0BEC5; font-size: 12px;"
            "background-color: #1E1E1E; border-radius: 4px; padding: 4px 12px;"
        )
        self._status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._status_label.setMinimumHeight(28)
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

    # ── 逻辑 ─────────────────────────────────────────────────────────────────

    def _on_chord_play(self, chord: Chord):
        """和弦按钮按下时的播放逻辑。

        若 ALT 键处于按下状态且存在上一个和弦的 voicing，
        则使用 MinVoiceLeading 计算新和弦的声部引导 voicing。
        """
        target_notes = chord.Notes()

        if (QApplication.keyboardModifiers() & Qt.AltModifier) and self._prev_voicing:
            voicing = Chord.MinVoiceLeading(self._prev_voicing, target_notes)
        else:
            voicing = target_notes

        pitches = [n._pitch for n in voicing]
        play_chord(pitches)

        # 记录本次实际播放的 voicing，供下次 ALT+点击使用
        self._prev_voicing = voicing

    def _on_key_changed(self, text: str):
        self._current_key = _NOTE_MAP.get(text, text)
        self._rebuild_all()

    # ── 和弦过渡高亮 ────────────────────────────────────────────────────────

    def _handle_transition(self, row_idx: int, col_idx: int):
        """当和弦按钮被点击时，根据过渡知识库高亮目标和弦按钮。"""
        if not self._transition_knowledge:
            return

        chord_suffix = self._chord_type_rows[row_idx][1]

        # 找到所有 Match 字段匹配的 TransitionItem
        matches = [
            item for item in self._transition_knowledge
            if item.get('Match') == chord_suffix
        ]
        if not matches:
            return

        # 清除所有高亮
        for row in self._cells:
            for cell in row:
                cell.clear_highlight()

        # 按目标单元格聚合权重与原因
        # targets: {(target_row, target_col): {'functional': bool, 'coloristic': bool,
        #                                       'reasons': list[dict]}}
        targets: dict[tuple[int, int], dict] = {}

        root_name = self._root_names[col_idx]
        root_pc = Note(root_name)._pitch % 12

        for item in matches:
            target_interval = item.get('TargetInterval', 0)
            target_type = item.get('TargetType', '')

            # 计算目标根音 pitch class
            target_pc = (root_pc + target_interval) % 12
            target_root_name = _SHARP_NAMES[target_pc]

            # 在 _root_names 中查找目标列
            try:
                target_col = self._root_names.index(target_root_name)
            except ValueError:
                continue

            # 在 _CHORD_TYPE_ROWS 中查找目标行
            target_row = None
            for i, (_, suffix, _) in enumerate(self._chord_type_rows):
                if suffix == target_type:
                    target_row = i
                    break

            if target_row is None:
                continue  # 目标类型不在当前矩阵中（如 Maj6）

            key = (target_row, target_col)
            if key not in targets:
                targets[key] = {'functional': False, 'coloristic': False, 'reasons': []}

            if item.get('FunctionalWeight', 0) != 0:
                targets[key]['functional'] = True
            if item.get('ColoristicWeight', 0) != 0:
                targets[key]['coloristic'] = True
            targets[key]['reasons'].append({
                'name': item.get('Name', ''),
                'description': item.get('Description', ''),
            })

        # 应用高亮
        for (r, c), weights in targets.items():
            colors = []
            if weights['functional']:
                colors.append('#4CAF50')   # 绿色 — 功能权重
            if weights['coloristic']:
                colors.append('#42A5F5')   # 蓝色 — 色彩权重
            if colors:
                self._cells[r][c].set_highlight(colors, reasons=weights.get('reasons', []))

    def _rebuild_all(self, full: bool = False):
        """重建/更新整个矩阵。

        Args:
            full: 若为 True，强制清除并重建整个网格（用于行增删改）。
        """
        tonic_pc = Note(self._current_key)._pitch % 12
        self._root_names = [_SHARP_NAMES[(tonic_pc + i) % 12] for i in range(12)]

        # 首次调用 或 强制重建：清除并重新构建网格
        if not self._cells or full:
            self._full_rebuild_grid()
            return

        # 增量更新：仅刷新按钮内容
        for row_idx, (_, suffix, _) in enumerate(self._chord_type_rows):
            for col, root_name in enumerate(self._root_names):
                if row_idx < len(self._cells) and col < len(self._cells[row_idx]):
                    degree_name = _DEGREE_NAMES[col]
                    display = f"{degree_name}{suffix}"
                    self._cells[row_idx][col].rebuild(root_name, suffix, display)

        self._rebuild_degree_cells()

        self._key_display.setText(self._current_key)

    # ── 网格重建 ─────────────────────────────────────────────────────────

    def _full_rebuild_grid(self):
        """完全清除并重建网格（标题 + 所有按钮行）。"""
        # 清除旧控件
        for i in reversed(range(self._grid.count())):
            w = self._grid.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._cells.clear()
        self._row_label_widgets.clear()
        self._degree_cells.clear()
        self._degree_row_widgets.clear()

        # 重建
        self._build_headers()
        self._build_cells()
        self._build_degree_cells()
        self._build_footer_buttons()
        self._key_display.setText(self._current_key)

    # ── 行 CRUD ──────────────────────────────────────────────────────────

    def _add_row(self):
        """弹出对话框添加新的和弦类型行。"""
        dlg = ChordRowDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        label, suffix, group = dlg.get_result()
        self._chord_type_rows.append((label, suffix, group))
        self._rebuild_all(full=True)

    def _edit_row(self, row_idx: int):
        """弹出对话框编辑指定行的和弦类型。"""
        label, suffix, group = self._chord_type_rows[row_idx]
        dlg = ChordRowDialog(self, edit_label=label,
                             edit_suffix=suffix, edit_group=group)
        if dlg.exec_() != QDialog.Accepted:
            return
        new_label, new_suffix, new_group = dlg.get_result()
        self._chord_type_rows[row_idx] = (new_label, new_suffix, new_group)
        self._rebuild_all(full=True)

    def _delete_row(self, row_idx: int):
        """删除指定和弦行（至少保留一行）。"""
        if len(self._chord_type_rows) <= 1:
            QMessageBox.warning(self, '无法删除', '至少需要保留一行和弦类型。')
            return
        label = self._chord_type_rows[row_idx][0]
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除和弦行 "{label}" 吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        del self._chord_type_rows[row_idx]
        self._rebuild_all(full=True)

    def _build_headers(self):
        """列标题行（级数名）"""
        hf = QFont("Consolas", 11, QFont.Bold)
        for col, name in enumerate(self._root_names):
            degree = _DEGREE_NAMES[col]
            # 工具提示显示实际音名
            lbl = QLabel(degree)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(hf)
            lbl.setMinimumHeight(28)
            lbl.setToolTip(f"{degree} = {name}")
            lbl.setStyleSheet(
                "color: #FFD54F; background-color: #2A2A2A;"
                "border-radius: 4px; padding: 4px 2px; font-weight: bold;"
            )
            self._grid.addWidget(lbl, 0, col + 1)

    def _build_cells(self):
        """行标题（含编辑/删除按钮）+ 12 列和弦按钮"""
        rf = QFont("Microsoft YaHei", 10, QFont.Bold)
        for row_idx, (cn_label, suffix, _group) in enumerate(self._chord_type_rows):
            gr = row_idx + 1

            # 行标题容器（标签 + 编辑/删除按钮）
            row_header = QWidget()
            row_header_layout = QHBoxLayout(row_header)
            row_header_layout.setContentsMargins(2, 2, 2, 2)
            row_header_layout.setSpacing(2)

            rl = QLabel(cn_label)
            rl.setAlignment(Qt.AlignCenter)
            rl.setFont(rf)
            rl.setMinimumWidth(48)
            rl.setMaximumWidth(56)
            color = '#81C784'
            rl.setStyleSheet(
                f"color: {color}; background-color: #2A2A2A;"
                "border-radius: 4px; padding: 4px 2px; font-weight: bold;"
            )
            row_header_layout.addWidget(rl)

            # 编辑按钮
            edit_btn = QPushButton('✎')
            edit_btn.setFixedSize(20, 20)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setToolTip(f'编辑 "{cn_label}" 行')
            edit_btn.setStyleSheet(_row_btn_style())
            edit_btn.clicked.connect(
                lambda checked, r=row_idx: self._edit_row(r)
            )
            row_header_layout.addWidget(edit_btn)

            # 删除按钮
            del_btn = QPushButton('✕')
            del_btn.setFixedSize(20, 20)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setToolTip(f'删除 "{cn_label}" 行')
            del_btn.setStyleSheet(_row_btn_style('#E57373'))
            del_btn.clicked.connect(
                lambda checked, r=row_idx: self._delete_row(r)
            )
            row_header_layout.addWidget(del_btn)

            self._grid.addWidget(row_header, gr, 0)
            self._row_label_widgets.append(row_header)

            # 12 个单元格
            row_cells: list[ChordCellButton] = []
            for col, root_name in enumerate(self._root_names):
                try:
                    ch = Chord(f"{root_name}{suffix}")
                except Exception:
                    ch = Chord("C")
                degree_name = _DEGREE_NAMES[col]
                display = f"{degree_name}{suffix}"
                btn = ChordCellButton(ch, self, display_name=display)
                btn.set_play_callback(self._on_chord_play)
                self._grid.addWidget(btn, gr, col + 1)
                # 连接过渡高亮处理
                btn.clicked.connect(
                    lambda checked, r=row_idx, c=col: self._handle_transition(r, c)
                )
                btn.hovered_with_reasons.connect(self._on_status_hover)
                row_cells.append(btn)
            self._cells.append(row_cells)

    # ── 度数型和弦行 ──────────────────────────────────────────────────────

    def _build_degree_cells(self):
        """度数型和弦行（标题 + 可变数量的度数型和弦按钮）。"""
        if not self._degree_chords:
            return

        num_chord_rows = len(self._chord_type_rows)
        degree_row = num_chord_rows + 1

        # 行标题
        row_header = QWidget()
        row_header_layout = QHBoxLayout(row_header)
        row_header_layout.setContentsMargins(2, 2, 2, 2)
        row_header_layout.setSpacing(2)

        rf = QFont("Microsoft YaHei", 10, QFont.Bold)
        rl = QLabel('度数')
        rl.setAlignment(Qt.AlignCenter)
        rl.setFont(rf)
        rl.setMinimumWidth(48)
        rl.setMaximumWidth(56)
        rl.setStyleSheet(
            'color: #CE93D8; background-color: #2A2A2A;'
            'border-radius: 4px; padding: 4px 2px; font-weight: bold;'
        )
        row_header_layout.addWidget(rl)

        # 添加度数型和弦按钮
        add_btn = QPushButton('✚')
        add_btn.setFixedSize(20, 20)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolTip('添加度数和弦 (V/IV, bVII, ...)')
        add_btn.setStyleSheet(_row_btn_style('#CE93D8'))
        add_btn.clicked.connect(self._add_degree_chord)
        row_header_layout.addWidget(add_btn)

        self._grid.addWidget(row_header, degree_row, 0)
        self._degree_row_widgets.append(row_header)

        # 度数型和弦按钮
        self._degree_cells.clear()
        col = 1
        for idx, dc in enumerate(self._degree_chords):
            label = dc['label']
            expr = dc['degree_expr']
            suffix = dc['chord_suffix']

            # 解析为实际 Chord
            root, bass = _resolve_degree_root_bass(expr, self._current_key)
            if root is None:
                ch = Chord('C')
                display = f"{label}?"
            else:
                try:
                    chord_str = f"{root}{suffix}/{bass}" if bass else f"{root}{suffix}"
                    ch = Chord(chord_str)
                except Exception:
                    ch = Chord('C')
                display = label

            btn = ChordCellButton(ch, self, display_name=display)
            btn.set_play_callback(self._on_chord_play)
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, i=idx: self._on_degree_cell_context(pos, i)
            )
            btn.setToolTip(
                f"{_format_degree_chord(expr, suffix)}  [{self._current_key}调]\n"
                f"{ch}\n"
                f"{' '.join(str(n) for n in ch.Notes())}\n"
                f"右键: 编辑 / 删除"
            )
            self._grid.addWidget(btn, degree_row, col)
            self._degree_cells.append(btn)
            col += 1

        # 空白占位列
        for c in range(col, 13):
            placeholder = QLabel('')
            placeholder.setStyleSheet('background: transparent;')
            self._grid.addWidget(placeholder, degree_row, c)
            self._degree_row_widgets.append(placeholder)

    def _rebuild_degree_cells(self):
        """增量更新度数型和弦按钮（调性切换后调用）。"""
        for idx, dc in enumerate(self._degree_chords):
            if idx >= len(self._degree_cells):
                break
            btn = self._degree_cells[idx]
            expr = dc['degree_expr']
            suffix = dc['chord_suffix']
            label = dc['label']

            root, bass = _resolve_degree_root_bass(expr, self._current_key)
            if root is None:
                ch = Chord('C')
                display = f"{label}?"
            else:
                try:
                    chord_str = f"{root}{suffix}/{bass}" if bass else f"{root}{suffix}"
                    ch = Chord(chord_str)
                except Exception:
                    ch = Chord('C')
                display = label

            btn._chord = ch
            btn.setText(display)
            btn.setToolTip(
                f"{_format_degree_chord(expr, suffix)}  [{self._current_key}调]\n"
                f"{ch}\n"
                f"{' '.join(str(n) for n in ch.Notes())}\n"
                f"右键: 编辑 / 删除"
            )

    # ── 底部按钮行 ───────────────────────────────────────────────────────

    def _build_footer_buttons(self):
        """矩阵底部按钮（添加和弦行）。"""
        num_chord_rows = len(self._chord_type_rows)
        has_degree = bool(self._degree_chords)
        footer_row = num_chord_rows + 1 + (1 if has_degree else 0)

        self._add_row_btn = QPushButton('＋ 添加和弦行')
        self._add_row_btn.setCursor(Qt.PointingHandCursor)
        self._add_row_btn.setStyleSheet(_add_btn_style())
        self._add_row_btn.clicked.connect(self._add_row)
        self._grid.addWidget(self._add_row_btn, footer_row, 0, 1, 1)

    # ── 度数型和弦 CRUD ─────────────────────────────────────────────────

    def _add_degree_chord(self):
        """弹出对话框添加度数型和弦。"""
        dlg = DegreeChordDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_result()
        self._degree_chords.append(data)
        self._rebuild_all(full=True)

    def _edit_degree_chord(self, idx: int):
        """弹出对话框编辑指定度数型和弦。"""
        dlg = DegreeChordDialog(self, edit_data=self._degree_chords[idx])
        if dlg.exec_() != QDialog.Accepted:
            return
        self._degree_chords[idx] = dlg.get_result()
        self._rebuild_all(full=True)

    def _delete_degree_chord(self, idx: int):
        """删除指定度数型和弦。"""
        label = self._degree_chords[idx]['label']
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除度数和弦 "{label}" 吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        del self._degree_chords[idx]
        self._rebuild_all(full=True)

    def _on_degree_cell_context(self, pos, idx: int):
        """度数型和弦按钮右键菜单。"""
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(_context_menu_style())

        edit_action = menu.addAction('✎  编辑')
        del_action = menu.addAction('✕  删除')

        action = menu.exec_(self._degree_cells[idx].mapToGlobal(pos))
        if action == edit_action:
            self._edit_degree_chord(idx)
        elif action == del_action:
            self._delete_degree_chord(idx)


    def _on_status_hover(self, reasons: list[dict]):
        """鼠标悬浮高亮按钮时，在状态栏显示过渡原因。"""
        if not reasons:
            self._status_label.clear()
            return
        lines = [f"{r['name']}: {r['description']}" for r in reasons]
        self._status_label.setText(' | '.join(lines))


def _combo_style() -> str:
    return """
        QComboBox {
            background-color: #2D2D2D; color: #CCCCCC;
            border: 1px solid #3C3C3C; border-radius: 4px;
            padding: 4px 8px; font-size: 13px; min-height: 24px;
        }
        QComboBox:hover { border-color: #555555; }
        QComboBox::drop-down { border: none; width: 24px; }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #AAAAAA;
            margin-right: 6px;
        }
        QComboBox QAbstractItemView {
            background-color: #2D2D2D; color: #CCCCCC;
            border: 1px solid #3C3C3C;
            selection-background-color: #264F78; outline: none;
        }
    """


def _add_btn_style() -> str:
    return """
        QPushButton {
            background-color: #2D5A2D; color: #A5D6A7;
            border: 1px solid #3E7A3E; border-radius: 4px;
            padding: 4px 14px; font-size: 12px; font-weight: bold;
        }
        QPushButton:hover {
            background-color: #3E7A3E; border-color: #66BB6A; color: #C8E6C9;
        }
    """


def _row_btn_style(color: str = '#90A4AE') -> str:
    return f"""
        QPushButton {{
            background-color: transparent; color: {color};
            border: 1px solid #555555; border-radius: 3px;
            font-size: 10px; padding: 0px;
        }}
        QPushButton:hover {{
            background-color: #4E4E4E; border-color: #FFD54F;
        }}
    """


def _context_menu_style() -> str:
    return """
        QMenu {
            background-color: #2D2D2D; color: #CCCCCC;
            border: 1px solid #555555; padding: 4px;
        }
        QMenu::item {
            padding: 6px 28px 6px 16px;
        }
        QMenu::item:selected {
            background-color: #264F78;
        }
    """
