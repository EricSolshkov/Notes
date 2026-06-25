"""
Note.py — 向后兼容入口

真正的实现已拆分到：
  Engine/interval.py  ← Interval 类常量
  Engine/Note.py      ← Note 类（本文件）

P0 重构（ROADMAP F1/E1/E0）：
  - Note 改为 _pitch + _spelling 双轨制
  - 消除 __global_signal__ 全局可变状态
  - Interval 改为类常量，放弃 Enum
"""

# ── Interval 类常量（从 interval.py 导入，向后兼容全部旧名称） ──────────────
from .interval import (
    Interval, Int,
    Per1, Unison, Min2, Maj2, Min3, Maj3, Per4,
    Aug4, Tritone, Dim5, Per5, Fifth,
    Min6, Maj6, Min7, Maj7, Oct, Octave,
    Min9, Maj9, Min10, Maj10, Per11, Aug11, Dim12,
    Per12, Twelfth, Min13, Maj13, Min14, Maj14, DuoOct,
)

# ── Note 类 ──────────────────────────────────────────────────────────────────

from typing import Optional

# 自然音在一个八度内的 pitch class（C=0 起）
_LETTER_PITCH = [0, 2, 4, 5, 7, 9, 11]   # C D E F G A B
_LETTER_NAME  = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
_SHARP_NAMES  = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
_FLAT_NAMES   = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']


def _parse_note_string(s: str) -> tuple:
    """
    解析音名字符串，返回 (pitch, (letter_idx, accidental))。
    支持：'C' 'C4' 'C#' 'C#4' '#C' 'bC' 'Cb' 'Cb4' 'Dbb' 'C##' 'Cx'。
    无八度时默认第4八度。
    """
    s = s.strip()

    # 提取变音记号前缀（# 或 b 在字母前）
    prefix_acc = 0
    if s.startswith('bb'):
        prefix_acc = -2
        s = s[2:]
    elif s and s[0] == '#':
        prefix_acc = 1
        s = s[1:]
    elif s and s[0] == 'b' and len(s) > 1 and s[1].upper() in _LETTER_NAME:
        prefix_acc = -1
        s = s[1:]

    if not s:
        raise ValueError("Empty note string after accidental prefix")

    # 提取字母名
    letter_char = s[0].upper()
    if letter_char not in _LETTER_NAME:
        raise ValueError(f"Invalid note letter: {letter_char!r}")
    letter_idx = _LETTER_NAME.index(letter_char)
    s = s[1:]

    # 提取变音记号后缀
    suffix_acc = 0
    i = 0
    while i < len(s) and s[i] in '#bx':
        i += 1
    acc_str = s[:i]
    s = s[i:]

    if acc_str:
        if acc_str == 'x':
            suffix_acc = 2
        elif all(c == '#' for c in acc_str):
            suffix_acc = len(acc_str)
        elif all(c == 'b' for c in acc_str):
            suffix_acc = -len(acc_str)
        else:
            raise ValueError(f"Invalid accidental: {acc_str!r}")

    accidental = prefix_acc + suffix_acc

    # 提取八度数字（支持负数如 C-1）
    octave = 4
    if s and (s.lstrip('-').isdigit()):
        octave = int(s)

    pitch = octave * 12 + _LETTER_PITCH[letter_idx] + accidental
    return pitch, (letter_idx, accidental)


class Note:
    """
    音符类（双轨制）。

    _pitch: int                          — 绝对半音编号（C0=0）
    _spelling: Optional[tuple[int,int]]  — (letter_idx, accidental)，None 表示无音名语义
    """
    __slots__ = ("_pitch", "_spelling")

    def __init__(self, note, signal: str = '#'):
        if isinstance(note, Note):
            object.__setattr__(self, '_pitch', note._pitch)
            object.__setattr__(self, '_spelling', note._spelling)
        elif isinstance(note, int):
            object.__setattr__(self, '_pitch', note)
            object.__setattr__(self, '_spelling', None)
        elif isinstance(note, str):
            pitch, spelling = _parse_note_string(note)
            object.__setattr__(self, '_pitch', pitch)
            object.__setattr__(self, '_spelling', spelling)
        elif note is None:
            object.__setattr__(self, '_pitch', 48)
            object.__setattr__(self, '_spelling', (0, 0))
        else:
            raise TypeError(f"Cannot construct Note from {type(note)}")

    def __setattr__(self, name, value):
        raise AttributeError("Note is immutable")

    # ── 等价层级（ROADMAP E0） ───────────────────────────────────────────────
    def __eq__(self, other) -> bool:
        if isinstance(other, Note):
            return self._pitch == other._pitch
        return NotImplemented

    def __hash__(self) -> int:
        return self._pitch

    def pitch_class_eq(self, other: 'Note') -> bool:
        """模12：C4 == C5，C# == C#5"""
        return self._pitch % 12 == other._pitch % 12

    def spelling_eq(self, other: 'Note') -> bool:
        """严格：pitch 相同 且 spelling 相同（C#4 ≠ Db4）"""
        if self._pitch != other._pitch:
            return False
        if self._spelling is None or other._spelling is None:
            return True   # 无 spelling 退化为 pitch 相等
        return self._spelling == other._spelling

    # ── 比较运算 ─────────────────────────────────────────────────────────────
    def __lt__(self, other) -> bool:
        return self._pitch < other._pitch

    def __le__(self, other) -> bool:
        return self._pitch <= other._pitch

    def __gt__(self, other) -> bool:
        return self._pitch > other._pitch

    def __ge__(self, other) -> bool:
        return self._pitch >= other._pitch

    # ── 算术运算 ─────────────────────────────────────────────────────────────
    def __add__(self, other):
        if other is None:
            return None
        if isinstance(other, Interval):
            return Note(self._pitch + other.value)
        if isinstance(other, list) and other and isinstance(other[0], Interval):
            return [Note(self._pitch + o.value) for o in other]
        if isinstance(other, int):
            return Note(self._pitch + other)
        return NotImplemented

    def __radd__(self, other):
        if other is None:
            return None
        if isinstance(other, list) and other and isinstance(other[0], Interval):
            return [Note(self._pitch + o.value) for o in other]
        return NotImplemented

    def __sub__(self, other):
        from .interval import _by_value
        if other is None:
            return None
        if isinstance(other, Interval):
            return Note(self._pitch - other.value)
        if isinstance(other, list) and other and isinstance(other[0], Interval):
            return [Note(self._pitch - o.value) for o in other]
        if isinstance(other, Note):
            return _by_value((self._pitch - other._pitch) % 24)
        if isinstance(other, list) and other and isinstance(other[0], Note):
            return [_by_value((self._pitch - o._pitch) % 24) for o in other]
        if isinstance(other, int):
            return Note(self._pitch - other)
        return NotImplemented

    def __rsub__(self, other):
        if other is None:
            return None
        if isinstance(other, list) and other and isinstance(other[0], Note):
            return [o - self for o in other]
        return NotImplemented

    # ── 显示 ─────────────────────────────────────────────────────────────────
    def _spelling_str(self) -> str:
        letter_idx, accidental = self._spelling
        name = _LETTER_NAME[letter_idx]
        if accidental > 0:
            name += '#' * accidental
        elif accidental < 0:
            name += 'b' * (-accidental)
        return name

    def __str__(self) -> str:
        if self._spelling is not None:
            return self._spelling_str()
        return _SHARP_NAMES[self._pitch % 12]

    def __repr__(self) -> str:
        if self._spelling is not None:
            return f"{self._spelling_str()}{self._pitch // 12}"
        return f"{_SHARP_NAMES[self._pitch % 12]}{self._pitch // 12}"

    # ── 工具方法 ─────────────────────────────────────────────────────────────
    def respell(self, target_letter: int) -> 'Note':
        """重拼为指定字母名（0=C … 6=B），pitch 不变。"""
        natural_pc = _LETTER_PITCH[target_letter]
        my_pc = self._pitch % 12
        diff = (my_pc - natural_pc + 6) % 12 - 6
        new_note = Note.__new__(Note)
        object.__setattr__(new_note, '_pitch', self._pitch)
        object.__setattr__(new_note, '_spelling', (target_letter, diff))
        return new_note

    # ── 属性 ─────────────────────────────────────────────────────────────────
    @property
    def pitch(self) -> int:
        return self._pitch

    @property
    def pitch_class(self) -> int:
        return self._pitch % 12

    @property
    def octave(self) -> int:
        return self._pitch // 12

    @property
    def spelling(self):
        return self._spelling

    # ── 向后兼容属性 ──────────────────────────────────────────────────────────
    @property
    def __note__(self) -> int:
        return self._pitch

    @property
    def __signal__(self) -> str:
        if self._spelling is not None:
            return 'b' if self._spelling[1] < 0 else '#'
        return '#'


# ── 向后兼容：SetGlobalSignal 废弃存根 ───────────────────────────────────────
def SetGlobalSignal(s: str):
    """已废弃（ROADMAP E1）。保留签名以避免 ImportError。"""
    import warnings
    warnings.warn(
        "SetGlobalSignal() is deprecated and has no effect.",
        DeprecationWarning,
        stacklevel=2,
    )


if __name__ == "__main__":
    c4 = Note("C4")
    cs4 = Note("C#4")
    db4 = Note("Db4")
    print(f"C#4 == Db4: {cs4 == db4}")                      # True (pitch eq)
    print(f"C#4.spelling_eq(Db4): {cs4.spelling_eq(db4)}")   # False
    print(f"C4.pitch_class_eq(C5): {c4.pitch_class_eq(Note('C5'))}")  # True
    print(repr(c4), repr(cs4), repr(db4))
    print(repr(c4 + Maj3))   # E4
