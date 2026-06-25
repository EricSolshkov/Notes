from .Note import Note
from .interval import (
    Interval, Int,
    Per1, Unison, Min2, Maj2, Min3, Maj3, Per4,
    Aug4, Tritone, Dim5, Per5, Fifth,
    Min6, Maj6, Min7, Maj7, Oct, Octave,
    Min9, Maj9, Min10, Maj10, Per11, Aug11, Dim12,
    Per12, Twelfth, Min13, Maj13, Min14, Maj14, DuoOct,
)
from .chord_types import _type, _extender, _modifier, _omit
from .chord_parser import parse_chord_name
from . import chord_analyzer as _analyzer


class Chord:
    def __init__(self, param=None, param2=""):
        self._notes = []
        self._type = ""
        self._extenders = []
        self._modifiers = []
        self._omits = []
        self._root = None
        self._over = None

        if isinstance(param, Chord):
            self._notes = list(param._notes)
            self._type = param._type
            self._extenders = list(param._extenders)
            self._modifiers = list(param._modifiers)
            self._omits = list(param._omits)
            self._root = param._root
            self._over = param._over

        elif isinstance(param, (Note, str)):
            chord_name = f"{param}{param2}" if isinstance(param, Note) else param
            parsed = parse_chord_name(chord_name)
            self._root = parsed["root"]
            self._type = parsed["type"]
            self._extenders = parsed["extenders"]
            self._modifiers = parsed["modifiers"]
            self._omits = parsed["omits"]
            self._notes = sorted(parsed["notes"])
            self._over = parsed["over"]

        else:
            parsed = parse_chord_name("C")
            self._root = parsed["root"]
            self._type = parsed["type"]
            self._extenders = []
            self._modifiers = []
            self._omits = []
            self._notes = sorted(parsed["notes"])
            self._over = None

    def Inv(self, order):
        if order < 0 or order >= len(self._notes):
            raise ValueError("Inversion order out of range.")
        new_chord = Chord(self)
        new_chord._over = None
        new_chord._root = self._notes[order]
        rotated = self._notes[order:] + self._notes[:order]
        for i in range(1, len(rotated)):
            while rotated[i] < rotated[0]:
                rotated[i] = rotated[i] + Oct
        new_chord._notes = rotated
        return new_chord

    def Notes(self):
        result = list(self._notes)
        if self._over is not None and result:
            bass_pc = self._over._pitch % 12
            # place bass an octave below the lowest chord tone
            target_pitch = result[0]._pitch - ((result[0]._pitch % 12 - bass_pc) % 12)
            if target_pitch >= result[0]._pitch:
                target_pitch -= 12
            # Note is immutable, construct with target pitch directly
            bass = Note(target_pitch)
            result.insert(0, bass)
        return result

    def Root(self):
        return self._over if self._over is not None else self._root

    def __getitem__(self, item):
        return self._notes[item % len(self._notes)]

    def __setitem__(self, key, value):
        self._notes[key % len(self._notes)] = value

    def __str__(self):
        name = str(self._root) + self._type
        for ext in self._extenders:
            name += ext
        for mod in self._modifiers:
            name += mod
        if self._over is not None:
            name += "/" + str(self._over)
        omit_str = "".join(self._omits)
        if omit_str:
            name += f"({omit_str})"
        return name

    def __repr__(self):
        return f"Chord({str(self)!r})"

    @staticmethod
    def Get3rd(notes):
        return _analyzer.Get3rd(notes)

    @staticmethod
    def Get5th(notes):
        return _analyzer.Get5th(notes)

    @staticmethod
    def Get7th(notes):
        return _analyzer.Get7th(notes)

    @staticmethod
    def Get6th(notes):
        return _analyzer.Get6th(notes)

    @staticmethod
    def Get9th(notes):
        return _analyzer.Get9th(notes)

    @staticmethod
    def Get11th(notes):
        return _analyzer.Get11th(notes)

    @staticmethod
    def Get13th(notes):
        return _analyzer.Get13th(notes)

    @staticmethod
    def Structure(notes):
        return _analyzer.Structure(notes)

    @staticmethod
    def Name(notes):
        return _analyzer.Name(notes)

    @staticmethod
    def Reoctvate(notes):
        return _analyzer.Reoctvate(notes)

    @staticmethod
    def Standardize(notes):
        return _analyzer.Standardize(notes)

    @staticmethod
    def MinVoiceLeading(prev_notes, target_notes):
        """
        Global-minimum voice leading via bipartite assignment.

        Solves the minimum-weight assignment between prev_notes and target
        pitch classes so that total semitone movement across all voices is
        globally minimised.  Allows voice exchange and voice crossing.

        For N > M, target pitch classes are duplicated to match voice count.
        For N < M, extra target pitch classes are inserted at mid-range.

        Cost matrix: c[i][j] = min_k |prev[i].pitch - (targetPC[j] + 12*k)| ≤ 6.
        Assignment solved by brute-force (O(n!)) — practical for n ≤ 8.

        Args:
            prev_notes:   previous voicing (list[Note], absolute pitches)
            target_notes: target chord notes (list[Note], any octave)

        Returns:
            list[Note]: target voicing, preserving natural voice mapping
        """
        import itertools

        if not target_notes:
            return []
        if not prev_notes:
            return Chord.Reoctvate(sorted(target_notes))

        n_prev = len(prev_notes)
        target_pcs = [n._pitch % 12 for n in target_notes]
        n_target = len(target_pcs)

        # ── build cost matrix ──
        costs = []
        for prev in prev_notes:
            pp = prev._pitch
            row = []
            for pc in target_pcs:
                d = min((pc - pp % 12) % 12, (pp % 12 - pc) % 12)
                row.append(d)
            costs.append(row)

        # ── N > M: duplicate target columns ──
        if n_prev > n_target:
            repeat = (n_prev + n_target - 1) // n_target
            target_pcs = (target_pcs * repeat)[:n_prev]
            for row in costs:
                row[:] = (row * repeat)[:n_prev]
            n_target = n_prev

        # ── solve assignment ──
        best_perm = None
        best_cost = float('inf')
        for perm in itertools.permutations(range(n_target), n_prev):
            total = sum(costs[i][perm[i]] for i in range(n_prev))
            if total < best_cost:
                best_cost = total
                best_perm = perm

        # ── realise with nearest octave copies ──
        result = []
        for i, j in enumerate(best_perm):
            pp = prev_notes[i]._pitch
            pc = target_pcs[j]
            base = (pp // 12) * 12 + pc
            best = base
            for d in (0, -12, 12, -24, 24):
                if abs(base + d - pp) < abs(best - pp):
                    best = base + d
            result.append(Note(best))

        # ── N < M: insert remaining unassigned target pitch classes ──
        assigned_pcs = {target_pcs[j] for j in best_perm}
        all_pcs = [n._pitch % 12 for n in target_notes]
        remaining = []
        seen = set()
        for i, pc in enumerate(all_pcs):
            key = (pc, i)
            if pc in assigned_pcs:
                assigned_pcs.discard(pc)
            elif key not in seen:
                remaining.append(pc)
                seen.add(key)

        if remaining:
            mid = sum(n._pitch for n in result) // len(result)
            for pc in remaining:
                base = (mid // 12) * 12 + pc
                best = base
                for d in (0, -12, 12):
                    if abs(base + d - mid) < abs(best - mid):
                        best = base + d
                result.append(Note(best))

        return result

    @staticmethod
    def Names(notes, force_root=None):
        return _analyzer.Names(notes, force_root)

    def GetNames(self):
        return Chord.Names(self.Notes(), self._over)

    def Debug(self, detailed=False):
        contains = [str(n) for n in self.Notes()]
        log_info = f"{self} = {contains} on: {self.Root()}"
        if detailed:
            exts = [f"{e}: {self._root + _extender[e]}" for e in self._extenders]
            mods = [f"{m}: {self._root + _modifier[m][1]}" for m in self._modifiers]
            if exts:
                log_info += f"\nextends: {exts}"
            if mods:
                log_info += f"\nmodifies: {mods}"
            if self._omits:
                log_info += f"\nomits: {self._omits}"
        print(log_info)


if __name__ == "__main__":
    import random
    random.seed(114514)
    for i in range(20):
        root = Note("C")
        t = list(_type.keys())[random.randint(0, 100) % len(_type)]
        c = Chord(str(root) + t)
        c.Debug()
        print(Chord.Names(c.Notes()))
