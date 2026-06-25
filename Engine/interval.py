"""
interval.py — Interval 类常量

设计原则（ROADMAP E0/F2）：
- 放弃 Enum，改用类常量，每个常量是唯一对象。
- __eq__ 使用身份相等（Aug4 ≠ Dim5）。
- enharmonic_eq(other) 比较半音数（等音程）。
- simple_eq(other)     比较 value % 12（复合音程折叠）。
- __hash__ 使用 id()。
"""

from __future__ import annotations


class Interval:
    __slots__ = ("value", "name")
    _registry: dict[str, "Interval"] = {}

    def __init__(self, semitones: int, name: str):
        self.value = semitones
        self.name = name
        Interval._registry[name] = self

    # ── 等价层级 ────────────────────────────────────────────────────────────
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Interval):
            return self is other          # 身份相等，Aug4 ≠ Dim5
        return NotImplemented

    def __hash__(self) -> int:
        return id(self)

    def enharmonic_eq(self, other: "Interval") -> bool:
        """等音程相等：半音数相同（Aug4.enharmonic_eq(Dim5) == True）"""
        return self.value == other.value

    def simple_eq(self, other: "Interval") -> bool:
        """模12相等：复合音程折叠（Maj9.simple_eq(Maj2) == True）"""
        return self.value % 12 == other.value % 12

    # ── 比较运算（按半音数） ─────────────────────────────────────────────────
    def __lt__(self, other: "Interval") -> bool:
        return self.value < other.value

    def __le__(self, other: "Interval") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "Interval") -> bool:
        return self.value > other.value

    def __ge__(self, other: "Interval") -> bool:
        return self.value >= other.value

    # ── 算术运算（返回最接近的已注册 Interval，按半音数 mod 24 查找） ─────────
    def __add__(self, other: "Interval") -> "Interval":
        if isinstance(other, Interval):
            target = (self.value + other.value) % 24
            return _by_value(target)
        return NotImplemented

    def __sub__(self, other: "Interval") -> "Interval":
        if isinstance(other, Interval):
            target = (self.value - other.value) % 24
            return _by_value(target)
        return NotImplemented

    def Normalized(self) -> "Interval":
        """折叠到单八度内（mod 12）"""
        return _by_value(self.value % 12)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Interval({self.name}, {self.value})"


def _by_value(v: int) -> Interval:
    """
    按半音数返回第一个注册的 Interval（优先取先注册的"主名"）。
    用于算术运算结果，不用于等价判断。
    """
    for itv in Interval._registry.values():
        if itv.value == v:
            return itv
    raise ValueError(f"No Interval with value {v}")


# ── 常量声明（按 ROADMAP 顺序，同半音数的不同 spelling 各自独立） ─────────────
Per1    = Unison   = Interval(0,  "Per1")
Min2               = Interval(1,  "Min2")
Maj2               = Interval(2,  "Maj2")
Min3               = Interval(3,  "Min3")
Maj3               = Interval(4,  "Maj3")
Per4               = Interval(5,  "Per4")
Aug4    = Tritone  = Interval(6,  "Aug4")   # Tritone 作为显式别名（同对象）
Dim5               = Interval(6,  "Dim5")
Per5    = Fifth    = Interval(7,  "Per5")
Min6               = Interval(8,  "Min6")
Maj6               = Interval(9,  "Maj6")
Min7               = Interval(10, "Min7")
Maj7               = Interval(11, "Maj7")
Oct     = Octave   = Interval(12, "Oct")
Min9               = Interval(13, "Min9")
Maj9               = Interval(14, "Maj9")
Min10              = Interval(15, "Min10")
Maj10              = Interval(16, "Maj10")
Per11              = Interval(17, "Per11")
Aug11              = Interval(18, "Aug11")
Dim12              = Interval(18, "Dim12")  # 等音于 Aug11，但身份不同
Per12   = Twelfth  = Interval(19, "Per12")
Min13              = Interval(20, "Min13")
Maj13              = Interval(21, "Maj13")
Min14              = Interval(22, "Min14")
Maj14              = Interval(23, "Maj14")
DuoOct             = Interval(24, "DuoOct")

# ── 短别名，向后兼容 ────────────────────────────────────────────────────────
Int = Interval
