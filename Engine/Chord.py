from Engine.Note import *
import re

Int = Interval

_type: dict[str, list[Int]] = {
    "5": [Int.Per5],

    "": [Int.Maj3, Int.Per5],
    "m": [Int.Min3, Int.Per5],
    "aug": [Int.Maj3, Int.Min6],
    "dim": [Int.Min3, Int.Dim5],

    "maj7": [Int.Maj3, Int.Per5, Int.Maj7],
    "m7": [Int.Min3, Int.Per5, Int.Min7],
    "7": [Int.Maj3, Int.Per5, Int.Min7],
    "mM7": [Int.Min3, Int.Per5, Int.Maj7],
    "dim7": [Int.Min3, Int.Dim5, Int.Maj6],
    "aug7": [Int.Maj3, Int.Min6, Int.Min7],
    "augM7": [Int.Maj3, Int.Min6, Int.Maj7],

    "6": [Int.Maj3, Int.Per5, Int.Maj6],
    "m6": [Int.Min3, Int.Per5, Int.Maj6],
    "aug6": [Int.Maj3, Int.Min6, Int.Maj6],
    "dim6": [Int.Min3, Int.Dim5, Int.Maj6],
    "6/9": [Int.Maj3, Int.Per5, Int.Maj6, Int.Maj9],
    "aug6/9": [Int.Maj3, Int.Min6, Int.Maj6, Int.Maj9],
    "dim6/9": [Int.Min3, Int.Dim5, Int.Maj6, Int.Maj9],

    "maj9": [Int.Maj3, Int.Per5, Int.Maj7, Int.Maj9],
    "m9": [Int.Min3, Int.Per5, Int.Min7, Int.Maj9],
    "9": [Int.Maj3, Int.Per5, Int.Min7, Int.Maj9],
    "aug9": [Int.Maj3, Int.Min6, Int.Min7, Int.Maj9],
    "dim9": [Int.Min3, Int.Dim5, Int.Maj6, Int.Maj9],

    "maj11": [Int.Maj3, Int.Per5, Int.Maj7, Int.Maj9, Int.Per11],
    "m11": [Int.Min3, Int.Per5, Int.Min7, Int.Maj9, Int.Per11],
    "11": [Int.Maj3, Int.Per5, Int.Min7, Int.Maj9, Int.Per11],
    "aug11": [Int.Maj3, Int.Min6, Int.Min7, Int.Maj9, Int.Per11],
    "dim11": [Int.Min3, Int.Dim5, Int.Maj6, Int.Maj9, Int.Per11],

    "maj13": [Int.Maj3, Int.Per5, Int.Maj7, Int.Maj9, Int.Per11, Int.Maj13],
    "m13": [Int.Min3, Int.Per5, Int.Min7, Int.Maj9, Int.Per11, Int.Maj13],
    "13": [Int.Maj3, Int.Per5, Int.Min7, Int.Maj9, Int.Per11, Int.Maj13],
    "aug13": [Int.Maj3, Int.Min6, Int.Min7, Int.Maj9, Int.Per11, Int.Maj13],
    "dim13": [Int.Min3, Int.Dim5, Int.Maj6, Int.Maj9, Int.Per11, Int.Maj13],
}
# suspend works like modifiers, but should place before extenders.
_suspend: dict[str, tuple[list[Int], Int]] = {
    "sus": ([Int.Min3, Int.Maj3], Int.Maj2),
    "sus2": ([Int.Min3, Int.Maj3], Int.Maj2),
    "sus4": ([Int.Min3, Int.Maj3], Int.Per4),
}
# let's just try to add sus chords into chord types
# known that, if a chord is a sus chord, we simply consider it as a Maj one,
# and search the specified chord name, and add a "sus" behind it.
# we do this to every chord, add only insert if not presented before.
container = {}
for (t, itvs) in _type.items():
    if not any([itv in [Int.Maj3, Int.Min3] for itv in itvs]):
        continue
    if Int.Per5 not in itvs:
        continue
    correspond_maj_itvs = [itv if itv != Int.Min3 else Int.Maj3 for itv in itvs]
    correspond_type = ""
    for (t1, itvs1) in _type.items():
        if itvs1 == correspond_maj_itvs:
            correspond_type = t1
            break

    # try insert sus
    for sus, mod in _suspend.items():
        sus_itvs = [itv if itv != Int.Maj3 else mod[1] for itv in correspond_maj_itvs]
        sus_name = f"{correspond_type}{sus}"
        container[sus_name] = sus_itvs

for (t, itvs) in container.items():
    _type[t] = itvs

_extender: dict[str, Int] = {
    "add2": Int.Maj2,
    "add4": Int.Per4,
    "add6": Int.Maj6,
    "add9": Int.Maj9,
    "add11": Int.Per11,
    "add13": Int.Maj13
}

# modifier modify a note in chord to another specified note
# if the note does not exist, modifier works like an extender.
_modifier: dict[str, tuple[Int, Int]] = {
    "b5": (Int.Per5, Int.Dim5), "-5": (Int.Per5, Int.Dim5),
    "#5": (Int.Per5, Int.Min6),

    "b9": (Int.Maj9, Int.Min9), "-9": (Int.Maj9, Int.Min9),
    "#9": (Int.Maj9, Int.Min10),

    "b11": (Int.Per11, Int.Maj10), "-11": (Int.Per11, Int.Maj10),
    "#11": (Int.Per11, Int.Aug11),

    "b13": (Int.Maj13, Int.Min13), "-13": (Int.Maj13, Int.Min13),
    "#13": (Int.Maj13, Int.Min14),
}

# omit removes specified note from chord.
_omit: dict[str, list[Int]] = {
    "no3": [Int.Maj3],
    "no5": [Int.Per5],
    "no7": [Int.Maj7, Int.Min7],
    "no9": [Int.Maj9],
    "no11": [Int.Per11],
}


def _match(_s: str, patterns: list[str]):
    # 遍历列表l中的模式串
    sorted_patterns = sorted(patterns, key=len, reverse=True)
    for pattern in sorted_patterns:
        if _s.startswith(pattern):
            p = pattern
            rest_part = _s[len(p):]
            return p, rest_part
    return "", _s


def _split(_s: str, patterns: list[str]):
    # 按长度排序模式串列表，优先匹配较长的模式串
    sorted_patterns = sorted(patterns, key=len, reverse=True)
    result = []
    remaining_s = _s

    while True:
        matched = False
        for pattern in sorted_patterns:
            if remaining_s.startswith(pattern):
                if pattern not in result:
                    result.append(pattern)
                remaining_s = remaining_s[len(pattern):]
                matched = True
                break
        if not matched:
            return result, remaining_s


def _parse_omit(_s: str):
    if _s[0] != "(" and _s[-1] != ")":
        return []
    else:
        _s = _s[1:-1]
        _s = _s.replace(",", "")
        _s = _s.replace(" ", "")

        res, _ = _split(_s, list(_omit.keys()))

        return res


class Chord:
    def __init__(self, param=None, param2=''):
        self._notes = []
        self._type = ""
        self._extenders = []
        self._modifiers = []
        self._omits = []
        self._root = None
        self._over = None
        # init by Chord obj.
        if isinstance(param, Chord):
            self._notes = param._notes
            self._type = param._type
            self._extenders = param._extenders
            self._modifiers = param._modifiers
            self._omits = param._omits
            self._root = param._root
            self._over = param._over
        # init by analyze:
        elif isinstance(param, Note) or isinstance(param, str):
            # init like Chord(Note("C"), "M7")
            if isinstance(param, Note):
                self._root = param
                _name = param2
            # init like Chord(CM7)
            else:
                signal = "#"
                if param[0] in ['b', '#']:
                    typeIndex = 2
                    signal = param[0]
                else:
                    typeIndex = 1
                self._root = Note(param[:typeIndex], signal)
                _name = param[typeIndex:]

            # analyze name to get type, extenders, modifiers, omits.
            # 使用正则表达式匹配括号及其内容
            match = re.search(r'\(.*?\)', _name)
            _omits = []
            if match:
                parentheses_content = match.group(0)
                _name = _name[:match.start()] + _name[match.end():]
                _omits = _parse_omit(parentheses_content)
            self._type, _name = _match(_name, list(_type.keys()))
            _mods, _name = _split(_name, list(_modifier.keys()))
            _exts, _name = _split(_name, list(_extender.keys()))

            composites = [d for d in _type[self._type]]

            for ext in _exts:
                if _extender[ext] not in composites:
                    self._extenders.append(ext)
                    composites.append(_extender[ext])
            composites.sort(key=lambda x: x.value)

            for mod in _mods:
                if _modifier[mod][1] in composites:
                    continue

                if _modifier[mod][0] in composites:
                    if _modifier[mod][0] != composites[-1] or _modifier[mod][0] <= Int.Per5:  # 不允许修饰五度以上冠音（不含）
                        self._modifiers.append(mod)
                        composites[composites.index(_modifier[mod][0])] = _modifier[mod][1]
                # 五度modifier只允许修饰存在的纯五度，不能在不存在时进行插入。
                elif _modifier[mod][0] != Int.Per5:
                    self._modifiers.append(mod)
                    composites.append(_modifier[mod][1])

            for omit in _omits:
                for itv in _omit[omit]:
                    if itv in composites:
                        composites.remove(itv)
                        self._omits.append(omit)
                        break

            self._notes = [self._root]
            for n in composites:
                self._notes.append(self._root + n)
            self._notes.sort()

            # analyze slash chord overs.
            slash = _name.find("/")
            if slash != -1:
                base = Note(_name[slash + 1:])
                self._over = base
        else:
            self._notes = [Note("C")]
            for d in _type[""]:
                self._notes.append(self._notes[0] + d)
            self._type = ""
            self._root = Note("C")

    def Inv(self, ord: int):
        self._over = self._notes[ord % len(self._notes)]

    def Notes(self) -> list[Note]:
        return [n for n in self._notes]

    def Root(self) -> Note:
        if self._over is not None:
            return self._over
        else:
            return self._root

    def __getitem__(self, item):
        return self._notes[item % len(self._notes)]

    def __setitem__(self, key, value):
        self._notes[key % len(self._notes)] = value

    def __str__(self):
        _root = self._root.__str__()
        _name = _root + self._type
        for ext in self._extenders:
            _name += ext
        for mod in self._modifiers:
            _name += mod
        if self._over is not None:
            _name += "/" + self._over.__str__()
        _omits = ""
        for omit in self._omits:
            _omits += f"{omit}"
        if len(_omits) != 0:
            _name += f"({_omits})"

        return _name

    @staticmethod
    def Get3rd(notes: list[Note]):
        for n in notes:
            if n in notes[0] + [Int.Min3, Int.Maj3]:
                return n
        # 找不到三度音，寻找挂留音
        for n in notes:
            if n - notes[0] in [Int.Maj2, Int.Per4]:
                return n
        return None

    @staticmethod
    def Get5th(notes: list[Note]):
        for n in notes:
            if n - notes[0] in [Int.Dim5, Int.Per5, Int.Min6]:
                return n
        for n in notes:
            if n - notes[0] == Int.Per12:
                return n

        return None

    @staticmethod
    def Get7th(notes: list[Note]):
        for n in notes:
            if n - notes[0] in [Int.Maj7, Int.Min7]:
                return n
        # 如果找不到，若五度音是减五度，则找大六度
        if Chord.Get5th(notes) - notes[0] == Int.Dim5:
            for n in notes:
                if n - notes[0] == Int.Maj6:
                    return n
        return None

    @staticmethod
    def Get6th(notes: list[Note]):
        # 若七音不是bb7
        if Chord.Get7th(notes) - notes[0] != Int.Maj6:
            for n in notes:
                if n - notes[0] in [Int.Maj6]:
                    return n
        return None

    @staticmethod
    def Get9th(notes: list[Note]):
        for n in notes:
            if n - notes[0] in [Int.Maj9, Int.Min9, Int.Min10]:
                return n
        return None

    @staticmethod
    def Get11th(notes: list[Note]):
        for n in notes:
            if n - notes[0] in [Int.Per11, Int.Maj10, Int.Aug11]:
                return n
        return None

    @staticmethod
    def Get13th(notes: list[Note]):
        for n in notes:
            if n - notes[0] in [Int.Maj13, Int.Min13, Int.Min14]:
                return n
        return None

    @staticmethod
    def Structure(notes: list[Note]):
        structure = {
            "3": Chord.Get3rd(notes),
            "5": Chord.Get5th(notes),
            "6": Chord.Get6th(notes),
            "7": Chord.Get7th(notes),
            "9": Chord.Get9th(notes),
            "11": Chord.Get11th(notes),
            "13": Chord.Get13th(notes),
        }
        other = [n for n in notes[1:] if n not in structure.values()]
        return structure, other

    @staticmethod
    def Name(notes: list[Note]):
        _root = notes[0]
        structureNotes, other = Chord.Structure(notes)
        structureItvs = [i - _root for i in structureNotes.values()]
        structure = dict([(k, v) for (k, v) in zip(list(structureNotes.keys()), structureItvs)])

        typename = ""
        nameCost = 0
        # 5
        if structure["3"] is None and structure["5"] == Int.Per5:
            typename = "5"
        # maj3, aug3
        elif structure["3"] == Int.Maj3 or structure["3"] is None:
            # maj and allow no5:
            if structure["5"] == Int.Per5 or structure["5"] is None:
                # majs
                if structure["7"] == Int.Maj7:
                    if structure["13"] == Int.Maj13:
                        typename = "maj13"
                    elif structure["11"] == Int.Per11:
                        typename = "maj11"
                    elif structure["9"] == Int.Maj9:
                        typename = "maj9"
                    else:
                        typename = "maj7"
                # doms
                elif structure["7"] == Int.Min7:
                    if structure["13"] == Int.Maj13:
                        typename = "13"
                    elif structure["11"] == Int.Per11:
                        typename = "11"
                    elif structure["9"] == Int.Maj9:
                        typename = "9"
                    else:
                        typename = "7"
                # M6
                elif structure["7"] is None and structure["6"] == Int.Maj6:
                    if structure["9"] == Int.Maj9:
                        typename = "6/9"
                    else:
                        typename = "6"
                # maj
                else:
                    typename = ""
            # augs and maj#5s:
            elif structure["5"] == Int.Min6:
                # maj#5s
                if structure["7"] == Int.Maj7:
                    nameCost += 1
                    if structure["13"] == Int.Maj13:
                        typename = "maj13#5"
                    elif structure["11"] == Int.Per11:
                        typename = "maj11#5"
                    elif structure["9"] == Int.Maj9:
                        typename = "maj9#5"
                    else:
                        typename = "maj7#5"
                # aug7 and above
                elif structure["7"] == Int.Min7:
                    if structure["13"] == Int.Maj13:
                        typename = "aug13"
                    elif structure["11"] == Int.Per11:
                        typename = "aug11"
                    elif structure["9"] == Int.Maj9:
                        typename = "aug9"
                    else:
                        typename = "aug7"
                # aug6
                elif structure["7"] is None and structure["6"] == Int.Maj6:
                    if structure["9"] == Int.Maj9:
                        typename = "aug6/9"
                    else:
                        typename = "aug6"
                # aug3
                else:
                    typename = "aug"
            # b5s
            elif structure["5"] == Int.Dim5:
                nameCost += 1
                # majb5s
                if structure["7"] == Int.Maj7:
                    if structure["13"] == Int.Maj13:
                        typename = "maj13b5"
                    elif structure["11"] == Int.Per11:
                        typename = "maj11b5"
                    elif structure["9"] == Int.Maj9:
                        typename = "maj9b5"
                    else:
                        typename = "maj7"
                # domb5s
                elif structure["7"] == Int.Min7:
                    if structure["13"] == Int.Maj13:
                        typename = "13b5"
                    elif structure["11"] == Int.Per11:
                        typename = "11b5"
                    elif structure["9"] == Int.Maj9:
                        typename = "9b5"
                    else:
                        typename = "7b5"
                # M6b5
                elif structure["7"] is None and structure["6"] == Int.Maj6:
                    if structure["9"] == Int.Maj9:
                        typename = "6/9b5"
                    else:
                        typename = "6b5"
                # maj
                else:
                    typename = "b5"
        # min3 dim3
        elif structure["3"] == Int.Min3:
            # mins
            if structure["5"] == Int.Per5:
                # mM7
                if structure["7"] == Int.Maj7:
                    typename = "mM7"
                # m7 and above
                elif structure["7"] == Int.Min7:
                    if structure["13"] == Int.Maj13:
                        typename = "m13"
                    elif structure["11"] == Int.Per11:
                        typename = "m11"
                    elif structure["9"] == Int.Maj9:
                        typename = "m9"
                    else:
                        typename = "m7"
                # m6
                elif structure["6"] == Int.Maj6:
                    typename = "m6"
                # min
                else:
                    typename = "m"
            # m#5s:
            elif structure["5"] == Int.Min6:
                nameCost += 1
                # m#5s
                if structure["7"] == Int.Min7:
                    if structure["13"] == Int.Maj13:
                        typename = "m13#5"
                    elif structure["11"] == Int.Per11:
                        typename = "m11#5"
                    elif structure["9"] == Int.Maj9:
                        typename = "m9#5"
                    elif structure["6"] == Int.Maj6:
                        typename = "m6#5"
                    else:
                        typename = "m7#5"
                # m#5
                else:
                    typename = "m#5"
            # dims and b5s
            elif structure["5"] == Int.Dim5:
                # m7-5
                if structure["7"] == Int.Min7:
                    typename = "m7"
                # dim7 and above
                elif structure["7"] == Int.Maj6:
                    if structure["13"] == Int.Maj13:
                        typename = "dim13"
                    elif structure["11"] == Int.Per11:
                        typename = "dim11"
                    elif structure["9"] == Int.Maj9:
                        typename = "dim9"
                    else:
                        typename = "dim7"
                # dim3
                else:
                    typename = "dim"
        # sus2 & sus4
        elif structure["3"] in [Int.Maj2, Int.Per4]:
            # maj7sus2 and above
            if structure["7"] == Int.Maj7:
                if structure["13"] == Int.Maj13:
                    typename = "maj13sus2"
                elif structure["11"] == Int.Per11:
                    typename = "maj11sus2"
                elif structure["9"] == Int.Maj9:
                    typename = "maj9sus2"
                else:
                    typename = "maj7sus2"
            # 7sus2 and above
            elif structure["7"] == Int.Min7:
                if structure["13"] == Int.Maj13:
                    typename = "13sus2"
                elif structure["11"] == Int.Per11:
                    typename = "11sus2"
                elif structure["9"] == Int.Maj9:
                    typename = "9sus2"
                else:
                    typename = "7sus2"
            # 6sus2
            elif structure["7"] is None and structure["6"] == Int.Maj6:
                if structure["9"] == Int.Maj9:
                    typename = "6/9sus2"
                else:
                    typename = "6sus2"
            # sus2
            else:
                typename = "sus2"
            if structure["5"] == Int.Min6:
                nameCost += 1
                typename += "#5"
            elif structure["5"] == Int.Dim5:
                nameCost += 1
                typename += "b5"

            if structure["3"] == Int.Per4:
                typename = typename.replace("sus2", "sus4")
        # maj3
        else:
            typename = ""

        refChord = Chord(_root, typename)
        modItvs = [n - notes[0] for n in notes[1:] if n not in refChord.Notes()]
        omitItvs = [i - refChord[0] for i in refChord.Notes()[1:] if i - refChord[0] not in structureItvs]
        ext = []
        mod = []
        blockOmitItv = []
        modifyStr = ""
        omitStr = ""
        unresolved = []
        for mo in modItvs:
            if mo in _extender.values():
                for extName, e_itv in _extender.items():
                    if e_itv == mo:
                        ext.append(extName)
                        break
            elif mo in [mod_rule[1] for mod_rule in _modifier.values()]:
                for modName, m_rule in _modifier.items():
                    if m_rule[1] == mo:
                        mod.append(modName)
                        blockOmitItv.append(m_rule[0])
                        break
            else:
                unresolved.append(_root + mo)
        for tdkr in mod:
            modifyStr += tdkr
        for tdkr in ext:
            modifyStr += tdkr
        omitCost = 0
        for omi in omitItvs:
            if any([omi in omit_rule for omit_rule in _omit.values()]):
                for omitName, omit_rule in _omit.items():
                    # 排除挂留和弦的no3, 排除所有有mod的omit
                    if (omi in omit_rule and
                            not (omitName == "no3" and typename.find("sus") != -1) and
                            omi not in blockOmitItv):
                        omitStr += omitName
                        omitCost += 1
        nameCost += 0.5 * omitCost ** 2
        if len(omitStr) != 0:
            omitStr = f"({omitStr})"
        typename = f"{typename}{modifyStr}{omitStr}"
        nameCost += len(ext) ** 2 + len(mod) ** 2
        return _root, typename, unresolved, nameCost

    @staticmethod
    # 音的出现顺序不变，调整后续音的八度，使其满足递增排列。
    def Reoctvate(notes: list[Note]):
        # 不改变音列顺序，整理音列为递增序列（）
        for i in range(1, len(notes)):
            while notes[i] <= notes[i - 1]:
                notes[i] = notes[i] + Int.Oct
        return notes

    @staticmethod
    def Standardize(notes: list[Note]):
        notes = Chord.Reoctvate(notes)
        # 将音列规范化到两个八度内，即，若低八度不低于低音，且不在原始音列中，则改变为低八度。
        for i, n in enumerate(notes):
            if i != 0:
                while notes[i] - notes[0] > Int.DuoOct and notes[i] - Int.Oct not in notes:
                    notes[i] -= Int.Oct
        # 进一步规范，潜在的三度音、五度音、大七度音到一个八度内
        for i, n in enumerate(notes):
            if i != 0:
                while notes[i] - notes[0] in [Int.Min10, Int.Maj10, Int.Aug11, Int.Per12, Int.Maj14] and notes[i] - Int.Oct not in notes:
                    notes[i] -= Int.Oct

        # 按绝对音高升序排列
        notes.sort()
        # 由高到低去除八度音（以免产生unresolvable的多余音）
        for i in range(len(notes) - 1, -1, -1):
            if notes[i] - Int.Oct in notes:
                notes.remove(notes[i])
        return notes

    @staticmethod
    def Names(notes: list[Note], force_root=None):
        notes = Chord.Standardize(notes)
        if force_root is not None:
            notes.insert(0, force_root)
            notes = Chord.Reoctvate(notes)
        names = []
        root = notes[0]
        # 原位和转位
        for start, n in enumerate(notes):
            cycle = Chord.Reoctvate([notes[(id + start) % len(notes)] for id in range(len(notes))])
            rootNote, typename, unresolved, cost = Chord.Name(cycle)
            if len(unresolved) == 0:
                over = "" if start == 0 else f"/{root.__str__()}"
                cost += 0 if start == 0 else 1
                names.append([f"{rootNote.__str__()}{typename}{over}", cost])
        # 和弦外低音斜线和弦
        notes = notes[1:]
        for start, n in enumerate(notes):
            cycle = Chord.Reoctvate([notes[(id + start) % len(notes)] for id in range(len(notes))])
            rootNote, typename, unresolved, cost = Chord.Name(cycle)
            if len(unresolved) == 0:
                cost += 1.5 if force_root is None else 0
                names.append([f"{rootNote.__str__()}{typename}/{root.__str__()}", cost])
        names.sort(key=lambda x: x[-1])
        names = [n[0] for n in names]
        return names

    def GetNames(self):
        return Chord.Names(self.Notes(), self._over)

    def Debug(self, detailed=False):
        contains = [n.__str__() for n in self.Notes()]
        _extends = [f"{ext}: {(self._root + _extender[ext]).__str__()}" for ext in self._extenders]
        _modifies = [f"{mod}: {(self._root + _modifier[mod][1]).__str__()}" for mod in self._modifiers]
        _omits = [omit for omit in self._omits]

        log_info = f"{self} = {contains} on: {self.Root()}"
        if detailed:
            if len(_extends) != 0:
                log_info += f"\nextends: {_extends}"
            if len(_modifies) != 0:
                log_info += f"\nmodifies: {_modifies}"
            if len(_omits) != 0:
                log_info += f"\nomits: {_omits}"

        print(f"{log_info}")


if __name__ == "__main__":
    import random

    random.seed(114514)
    for i in range(100):
        root = Note("C")
        types = list(_type.keys())
        modifiers = list(_modifier.keys())
        extends = list(_extender.keys())
        omits = list(_omit.keys())
        type = types[random.randint(0, 100) % (len(types))]
        adds = ""
        for j in range(0, random.randint(0, 2)):
            adds += extends[random.randint(0, 100) % (len(extends))]
        mods = ""
        for j in range(0, random.randint(0, 1)):
            mods += modifiers[random.randint(0, 100) % (len(modifiers))]
        name = root.__str__() + type + adds + mods
        omits_s = ""
        for o in omits[:max(0, random.randint(0, 13) - 10)]:
            omits_s += o
        if len(omits_s) != 0:
            name += f"({omits_s})"
        # print(f"test: {name}")
        c = Chord(name)
        c.Debug()
        names = Chord.Names(c.Notes())
        print(names)
