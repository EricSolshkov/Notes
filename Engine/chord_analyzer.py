"""
chord_analyzer.py — 和弦分析（P1 E3/F5）

包含 Structure / Get3rd..Get13th / Name / Names。
Name() 使用评分函数替代 if-elif（F5），支持不完整和弦识别。
"""

from __future__ import annotations
from .Note import Note
from .interval import (
    Interval, _by_value,
    Min2, Maj2, Min3, Maj3, Per4, Dim5, Per5,
    Min6, Maj6, Min7, Maj7, Oct,
    Min9, Maj9, Min10, Maj10, Per11, Aug11,
    Min13, Maj13, Min14, Per12, DuoOct,
)
from .chord_types import _type, _extender, _modifier, _omit


# ── 音程权重（F5 评分函数用） ───────────────────────────────────────────────────
_interval_weights: dict[int, float] = {
    Min3.value: 1.8, Maj3.value: 1.8,
    Maj2.value: 1.5, Per4.value: 1.5,
    Dim5.value: 1.3, Min6.value: 1.3,
    Min7.value: 1.4, Maj7.value: 1.4,
    Per5.value: 0.15,
    Maj9.value: 0.5, Min9.value: 0.7,
    Per11.value: 0.4, Aug11.value: 0.6,
    Maj13.value: 0.4, Min13.value: 0.6,
    Maj6.value: 0.8,
}


def _score_type_match(input_vals: frozenset[int], type_itvs: list[Interval]) -> float:
    """计算输入音程集合与和弦类型的匹配分数（0~1）。"""
    type_vals = [i.value for i in type_itvs]
    matched  = sum(_interval_weights.get(v, 0.3) for v in type_vals if v in input_vals)
    missing  = sum(_interval_weights.get(v, 0.3) for v in type_vals if v not in input_vals)
    spurious = sum(0.3 for v in input_vals if v not in type_vals)
    total = matched + missing + spurious
    return matched / total if total > 0 else 0.0


# ── 音程提取辅助 ──────────────────────────────────────────────────────────────

def Get3rd(notes: list[Note]):
    root = notes[0]
    for n in notes[1:]:
        diff = (n._pitch - root._pitch) % 24
        if diff in (Min3.value, Min3.value + 12):
            return root + Min3
        if diff in (Maj3.value, Maj3.value + 12):
            return root + Maj3
    for n in notes[1:]:
        diff = (n._pitch - root._pitch) % 24
        if diff in (Maj2.value, Per4.value):
            return n
    return None


def Get5th(notes: list[Note]):
    root = notes[0]
    for n in notes[1:]:
        diff = (n._pitch - root._pitch) % 24
        if diff in (Dim5.value, Per5.value, Min6.value):
            return n
    for n in notes[1:]:
        if (n._pitch - root._pitch) % 24 == Per12.value:
            return n
    return None


def Get7th(notes: list[Note]):
    root = notes[0]
    for n in notes[1:]:
        diff = (n._pitch - root._pitch) % 24
        if diff in (Maj7.value, Min7.value):
            return n
    fifth = Get5th(notes)
    if fifth is not None and (fifth._pitch - root._pitch) % 24 == Dim5.value:
        for n in notes[1:]:
            if (n._pitch - root._pitch) % 24 == Maj6.value:
                return n
    return None


def Get6th(notes: list[Note]):
    root = notes[0]
    seventh = Get7th(notes)
    if seventh is not None and (seventh._pitch - root._pitch) % 24 == Maj6.value:
        return None
    for n in notes[1:]:
        if (n._pitch - root._pitch) % 24 == Maj6.value:
            return n
    return None


def Get9th(notes: list[Note]):
    root = notes[0]
    for n in notes[1:]:
        diff = (n._pitch - root._pitch) % 24
        if diff in (Maj9.value, Min9.value, Min10.value):
            return n
    return None


def Get11th(notes: list[Note]):
    root = notes[0]
    for n in notes[1:]:
        diff = (n._pitch - root._pitch) % 24
        if diff in (Per11.value, Maj10.value, Aug11.value):
            return n
    return None


def Get13th(notes: list[Note]):
    root = notes[0]
    for n in notes[1:]:
        diff = (n._pitch - root._pitch) % 24
        if diff in (Maj13.value, Min13.value, Min14.value):
            return n
    return None


def Structure(notes: list[Note]):
    structure = {
        "3":  Get3rd(notes),
        "5":  Get5th(notes),
        "6":  Get6th(notes),
        "7":  Get7th(notes),
        "9":  Get9th(notes),
        "11": Get11th(notes),
        "13": Get13th(notes),
    }
    other = [n for n in notes[1:] if n not in structure.values()]
    return structure, other


# ── F5 评分函数驱动的 Name() ──────────────────────────────────────────────────

def Name(notes: list[Note]) -> tuple:
    """
    分析音列，返回最可能的和弦命名。
    返回: (root: Note, typename: str, unresolved: list[Note], cost: float)
    """
    from .chord_parser import parse_chord_name

    root = notes[0]
    # 计算所有音相对根音的半音差（mod 24）
    input_vals: frozenset[int] = frozenset(
        (n._pitch - root._pitch) % 24 for n in notes[1:]
    )

    # ── 评分找最佳基础类型 ───────────────────────────────────────────────────
    best_type = ""
    best_score = -1.0
    for t, itvs in _type.items():
        score = _score_type_match(input_vals, itvs)
        if score > best_score:
            best_score = score
            best_type = t

    # 用解析器构建参考和弦
    ref_data = parse_chord_name(f"{root}{best_type}")
    ref_notes = ref_data["notes"]
    ref_vals = frozenset((n._pitch - root._pitch) % 24 for n in ref_notes[1:])

    # ── 确定多余音（需要 modifier/extender 表达） ────────────────────────────
    extra_vals = input_vals - ref_vals
    missing_vals = ref_vals - input_vals

    ext = []
    mod = []
    block_omit_vals = set()
    unresolved = []

    for val in sorted(extra_vals):
        # 尝试 extender
        found = False
        for ext_name, ext_itv in _extender.items():
            if ext_itv.value == val:
                ext.append(ext_name)
                found = True
                break
        if found:
            continue
        # 尝试 modifier
        for mod_name, (src, dst) in _modifier.items():
            if dst.value == val:
                mod.append(mod_name)
                block_omit_vals.add(src.value)
                found = True
                break
        if not found:
            unresolved.append(root + _by_value(val))

    # ── 确定缺失音（需要 omit 表达） ─────────────────────────────────────────
    omit_strs = []
    omit_cost = 0
    for val in missing_vals:
        if val in block_omit_vals:
            continue
        for omit_name, omit_itvs in _omit.items():
            if any(i.value == val for i in omit_itvs):
                if not (omit_name == "no3" and "sus" in best_type):
                    omit_strs.append(omit_name)
                    omit_cost += 1
                break

    modify_str = "".join(mod) + "".join(ext)
    omit_str = "".join(omit_strs)
    if omit_str:
        omit_str = f"({omit_str})"

    typename = f"{best_type}{modify_str}{omit_str}"
    cost = (1.0 - best_score) + 0.5 * omit_cost ** 2 + len(ext) ** 2 + len(mod) ** 2
    if unresolved:
        cost += 5.0

    return root, typename, unresolved, cost


def Reoctvate(notes: list[Note]) -> list[Note]:
    """调整八度使音列严格递增。"""
    notes = list(notes)
    for i in range(1, len(notes)):
        while notes[i] <= notes[i - 1]:
            notes[i] = notes[i] + Oct
    return notes


def Standardize(notes: list[Note]) -> list[Note]:
    """将音列规范化到两个八度内，去除八度重复音。"""
    notes = Reoctvate(list(notes))

    for i, n in enumerate(notes):
        if i != 0:
            while (notes[i]._pitch - notes[0]._pitch) > DuoOct.value and (notes[i] - Oct) not in notes:
                notes[i] = notes[i] - Oct

    for i, n in enumerate(notes):
        if i != 0:
            diff = (notes[i]._pitch - notes[0]._pitch)
            while diff in (Min10.value, Maj10.value, Aug11.value, Per12.value, Min14.value + 1):
                candidate = notes[i] - Oct
                if candidate not in notes:
                    notes[i] = candidate
                    diff = (notes[i]._pitch - notes[0]._pitch)
                else:
                    break

    notes.sort()
    # 去除八度重复
    for i in range(len(notes) - 1, -1, -1):
        candidate = Note(notes[i]._pitch - Oct.value)
        if candidate in notes:
            notes.pop(i)
    return notes


def Names(notes: list[Note], force_root=None) -> list[str]:
    notes = Standardize(notes)
    if force_root is not None:
        notes.insert(0, force_root)
        notes = Reoctvate(notes)

    results = []
    root = notes[0]

    # 原位和转位
    for start in range(len(notes)):
        cycle = Reoctvate([notes[(i + start) % len(notes)] for i in range(len(notes))])
        root_note, typename, unresolved, cost = Name(cycle)
        if not unresolved:
            over = "" if start == 0 else f"/{root}"
            cost += 0 if start == 0 else 1
            results.append((f"{root_note}{typename}{over}", cost))

    # 和弦外低音
    upper = notes[1:]
    for start in range(len(upper)):
        cycle = Reoctvate([upper[(i + start) % len(upper)] for i in range(len(upper))])
        root_note, typename, unresolved, cost = Name(cycle)
        if not unresolved:
            extra = 1.5 if force_root is None else 0
            cost += extra
            results.append((f"{root_note}{typename}/{root}", cost))

    results.sort(key=lambda x: x[1])
    return [n for n, _ in results]
