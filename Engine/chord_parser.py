"""
chord_parser.py — 和弦字符串解析（P1 E2）

包含 _match / _split / _parse_omit 以及字符串 → 和弦音列的解析逻辑。
"""

import re
from .Note import Note
from .interval import Interval, Per5
from .chord_types import _type, _extender, _modifier, _omit, _suspend


def _match(s: str, patterns: list[str]):
    sorted_patterns = sorted(patterns, key=len, reverse=True)
    for pattern in sorted_patterns:
        if s.startswith(pattern):
            return pattern, s[len(pattern):]
    return "", s


def _split(s: str, patterns: list[str]):
    sorted_patterns = sorted(patterns, key=len, reverse=True)
    result = []
    remaining = s
    while True:
        matched = False
        for pattern in sorted_patterns:
            if remaining.startswith(pattern):
                if pattern not in result:
                    result.append(pattern)
                remaining = remaining[len(pattern):]
                matched = True
                break
        if not matched:
            return result, remaining


def _parse_omit(s: str) -> list[str]:
    if not (s.startswith("(") and s.endswith(")")):
        return []
    inner = s[1:-1].replace(",", "").replace(" ", "")
    res, _ = _split(inner, list(_omit.keys()))
    return res


def parse_chord_name(name: str) -> dict:
    """
    解析和弦名字符串，返回结构化字典：
    {
        root: Note,
        type: str,
        extenders: list[str],
        modifiers: list[str],
        omits: list[str],
        notes: list[Note],
        over: Note | None,
    }
    """
    original = name
    # 提取根音：先取首字母，再扫描所有连续变音符号（支持 C##, Dbb, Fx 等）
    if len(name) == 1:
        type_index = 1
        signal = '#'
    elif name[0] in ('b', '#'):
        # 前缀变音：# 或 b 在字母前（旧式写法）
        type_index = 2
        signal = name[0]
    elif len(name) > 1 and name[1] in ('b', '#', 'x'):
        # 字母后跟变音符：扫描所有连续变音字符
        i = 1
        while i < len(name) and name[i] in ('#', 'b', 'x'):
            i += 1
        type_index = i
        signal = name[1]
    else:
        type_index = 1
        signal = '#'
    root = Note(name[:type_index], signal)
    name = name[type_index:]

    # 提取括号内容（omit）
    match = re.search(r'\(.*?\)', name)
    omits = []
    if match:
        omits = _parse_omit(match.group(0))
        name = name[:match.start()] + name[match.end():]

    chord_type, name = _match(name, list(_type.keys()))
    mods, name = _split(name, list(_modifier.keys()))
    exts, name = _split(name, list(_extender.keys()))

    composites = list(_type[chord_type])

    final_exts = []
    for ext in exts:
        if not any(i.enharmonic_eq(_extender[ext]) for i in composites):
            final_exts.append(ext)
            composites.append(_extender[ext])
    composites.sort(key=lambda x: x.value)

    final_mods = []
    for mod in mods:
        src, dst = _modifier[mod]
        if any(i.enharmonic_eq(dst) for i in composites):
            continue
        if any(i.enharmonic_eq(src) for i in composites):
            if src.value <= Per5.value or not src.enharmonic_eq(composites[-1]):
                final_mods.append(mod)
                composites = [dst if i.enharmonic_eq(src) else i for i in composites]
        elif src.value != Per5.value:
            # 五度 modifier 只允许修饰已存在的五度，其他 modifier 可插入
            final_mods.append(mod)
            composites.append(dst)

    final_omits = []
    for omit in omits:
        for itv in _omit[omit]:
            matched = [i for i in composites if i.enharmonic_eq(itv)]
            if matched:
                composites.remove(matched[0])
                final_omits.append(omit)
                break

    notes = [root] + [root + itv for itv in composites]
    notes.sort()

    # 斜线和弦
    over = None
    slash = name.find("/")
    if slash != -1:
        over = Note(name[slash + 1:])

    return {
        "root": root,
        "type": chord_type,
        "extenders": final_exts,
        "modifiers": final_mods,
        "omits": final_omits,
        "notes": notes,
        "over": over,
    }
