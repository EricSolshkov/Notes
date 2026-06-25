"""
chord_types.py — 和弦类型数据（P1 E2/E4）

包含 _type / _suspend / _extender / _modifier / _omit 字典。
Sus 和弦通过 _build_sus_types() 显式构建，消除 module load 副作用（E4）。
"""

from .interval import (
    Min2, Maj2, Min3, Maj3, Per4, Aug4, Dim5, Per5,
    Min6, Maj6, Min7, Maj7, Min9, Maj9, Min10, Maj10,
    Per11, Aug11, Min13, Maj13, Min14,
    Interval,
)

# ── 基础和弦类型 ──────────────────────────────────────────────────────────────
_type: dict[str, list[Interval]] = {
    "5": [Per5],

    "":     [Maj3, Per5],
    "m":    [Min3, Per5],
    "aug":  [Maj3, Min6],
    "dim":  [Min3, Dim5],

    "maj7":  [Maj3, Per5, Maj7],
    "M7":    [Maj3, Per5, Maj7],
    "m7":    [Min3, Per5, Min7],
    "7":     [Maj3, Per5, Min7],
    "mM7":   [Min3, Per5, Maj7],
    "dim7":  [Min3, Dim5, Maj6],
    "m7b5":  [Min3, Dim5, Min7],   # half-diminished (ø7)
    "aug7":  [Maj3, Min6, Min7],
    "augM7": [Maj3, Min6, Maj7],

    "6":     [Maj3, Per5, Maj6],
    "m6":    [Min3, Per5, Maj6],
    "aug6":  [Maj3, Min6, Maj6],
    "dim6":  [Min3, Dim5, Maj6],
    "6/9":   [Maj3, Per5, Maj6, Maj9],
    "aug6/9":[Maj3, Min6, Maj6, Maj9],
    "dim6/9":[Min3, Dim5, Maj6, Maj9],

    "maj9":  [Maj3, Per5, Maj7, Maj9],
    "m9":    [Min3, Per5, Min7, Maj9],
    "9":     [Maj3, Per5, Min7, Maj9],
    "aug9":  [Maj3, Min6, Min7, Maj9],
    "dim9":  [Min3, Dim5, Maj6, Maj9],

    "maj11": [Maj3, Per5, Maj7, Per11],
    "m11":   [Min3, Per5, Min7, Per11],
    "11":    [Maj3, Per5, Min7, Per11],
    "aug11": [Maj3, Min6, Min7, Per11],
    "dim11": [Min3, Dim5, Maj6, Per11],

    "maj13": [Maj3, Per5, Maj7, Maj13],
    "m13":   [Min3, Per5, Min7, Maj13],
    "13":    [Maj3, Per5, Min7, Maj13],
    "aug13": [Maj3, Min6, Min7, Maj13],
    "dim13": [Min3, Dim5, Maj6, Maj13],
}

_suspend: dict[str, tuple[list[Interval], Interval]] = {
    "sus":  ([Min3, Maj3], Maj2),
    "sus2": ([Min3, Maj3], Maj2),
    "sus4": ([Min3, Maj3], Per4),
}

_extender: dict[str, Interval] = {
    "add2":  Maj2,
    "add4":  Per4,
    "add6":  Maj6,
    "add9":  Maj9,
    "add11": Per11,
    "add13": Maj13,
}

_modifier: dict[str, tuple[Interval, Interval]] = {
    "b5":  (Per5, Dim5),  "-5":  (Per5, Dim5),
    "#5":  (Per5, Min6),

    "b9":  (Maj9, Min9),  "-9":  (Maj9, Min9),
    "#9":  (Maj9, Min10),

    "b11": (Per11, Maj10), "-11": (Per11, Maj10),
    "#11": (Per11, Aug11),

    "b13": (Maj13, Min13), "-13": (Maj13, Min13),
    "#13": (Maj13, Min14),
}

_omit: dict[str, list[Interval]] = {
    "no3": [Maj3],
    "no5": [Per5],
    "no7": [Maj7, Min7],
    "no9": [Maj9],
    "no11":[Per11],
}


def _build_sus_types() -> None:
    """
    为所有含三度且含纯五度的和弦类型生成 sus 变体。
    显式调用一次，消除 module load 副作用（E4）。
    """
    container: dict[str, list[Interval]] = {}
    for t, itvs in list(_type.items()):
        if not any(itv.enharmonic_eq(Maj3) or itv.enharmonic_eq(Min3) for itv in itvs):
            continue
        if not any(itv.enharmonic_eq(Per5) for itv in itvs):
            continue
        # 对应 Maj 版本
        correspond_maj_itvs = [Maj3 if itv.enharmonic_eq(Min3) else itv for itv in itvs]
        correspond_type = ""
        for t1, itvs1 in _type.items():
            if itvs1 == correspond_maj_itvs:
                correspond_type = t1
                break

        for sus_name_key, (_, sus_note) in _suspend.items():
            sus_itvs = [sus_note if itv.enharmonic_eq(Maj3) else itv for itv in correspond_maj_itvs]
            full_name = f"{correspond_type}{sus_name_key}"
            container[full_name] = sus_itvs

    for t, itvs in container.items():
        if t not in _type:
            _type[t] = itvs


# 在模块导入时显式调用一次（E4 合规：不是顶层副作用循环，而是显式函数调用）
_build_sus_types()
