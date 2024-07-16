from enum import Enum


class Interval(Enum):
    Unison = 0
    Per1 = 0
    Min2 = 1
    Maj2 = 2
    Min3 = 3
    Maj3 = 4
    Per4 = 5
    Aug4 = 6
    Tritone = 6
    Dim5 = 6
    Per5 = 7
    Fifth = 7
    Min6 = 8
    Maj6 = 9
    Min7 = 10
    Maj7 = 11
    Oct = 12
    Octave = 12
    Min9 = 13
    Maj9 = 14
    Min10 = 15
    Maj10 = 16
    Per11 = 17
    Aug11 = 18
    Dim12 = 18
    Per12 = 19
    Twelfth = 19
    Min13 = 20
    Maj13 = 21
    Min14 = 22
    Maj14 = 23
    DuoOct = 24

    def __add__(self, other):
        if isinstance(other, Interval):
            return [e for e in Interval.__members__.values() if e == (self.value + other.value) % 24][0]
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Interval):
            return [e for e in Interval.__members__.values() if e.value == (self.value - other.value) % 24][0]
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Interval):
            return self.value == other.value
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Interval):
            return self.value >= other.value
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, Interval):
            return self.value <= other.value
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Interval):
            return self.value > other.value
        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Interval):
            return self.value < other.value
        else:
            return NotImplemented

    def __str__(self):
        return self.name


Int = Interval


__global_signal__ = None


def SetGlobalSignal(s: str):
    if s in ['#', 'b']:
        global __global_signal__
        __global_signal__ = s
    else:
        print("Invalid Signal!")


class Note:
    def __init__(self, note, signal='#'):
        self.__signal__ = signal
        if note is not None and isinstance(note, Note):
            self.__note__ = note.__note__
        elif note is not None and isinstance(note, int):
            self.__note__ = note
        elif note is not None and isinstance(note, str):
            map = {
                "C": 24,
                "D": 26,
                "E": 28,
                "F": 29,
                "G": 31,
                "A": 33,
                "B": 35,
            }
            if note[0] not in ['b', '#']:
                self.__note__ = map[note[0]]
                if len(note) >= 2:
                    self.__note__ += int(note[1:]) * 12
            else:
                self.__note__ = map[note[1]]
                if len(note) >= 3:
                    self.__note__ += int(note[2:]) * 12
                if note[0] == 'b':
                    self.__note__ -= 1
                    self.__signal__ = 'b'
                else:
                    self.__note__ += 1
                    self.__signal__ = '#'

        else:
            self.__note__ = 24

        if __global_signal__ is not None:
            self.__signal__ = __global_signal__

    def __add__(self, other):
        if other is None:
            return None
        elif isinstance(other, Interval):
            return Note(self.__note__ + other.value, self.__signal__)
        elif isinstance(other, list) and len(other) > 0 and isinstance(other[0], Interval):
            return [Note(self.__note__ + o.value, self.__signal__) for o in other]
        elif type(other) is int:
            return Note(self.__note__ + other, self.__signal__)
        else:
            return NotImplemented

    def __radd__(self, other):
        if other is None:
            return None
        elif isinstance(other, list) and len(other) > 0 and isinstance(other[0], Interval):
            return [Note(self.__note__ + o.value, self.__signal__) for o in other]
        else:
            return NotImplemented

    def __sub__(self, other):
        if other is None:
            return None
        elif isinstance(other, Interval):
            return Note(self.__note__ - other.value, self.__signal__)
        elif isinstance(other, list) and len(other) > 0 and isinstance(other[0], Interval):
            return [Note(self.__note__ - o.value, self.__signal__) for o in other]
        elif isinstance(other, Note):
            return [e for e in Interval.__members__.values() if e.value == (self.__note__ - other.__note__) % 24][0]
        elif isinstance(other, list) and len(other) > 0 and isinstance(other[0], Note):
            return [[e for e in Interval.__members__.values() if e.value == (self.__note__ - o.__note__) % 24][0] for o in other]
        elif type(other) is int:
            return Note(self.__note__ - other, self.__signal__)
        else:
            return NotImplemented

    def __rsub__(self, other):
        if other is None:
            return None
        elif isinstance(other, list) and len(other) > 0 and isinstance(other[0], Interval):
            return [o - self for o in other]
        elif isinstance(other, list) and len(other) > 0 and isinstance(other[0], Note):
            return [o - self for o in other]
        else:
            return NotImplemented

    def __str__(self):
        names1 = [
            'C', '#C', 'D', '#D',
            'E', 'F', '#F', 'G',
            '#G', 'A', '#A', 'B'
        ]
        names2 = [
            'C', 'bD', 'D', 'bE',
            'E', 'F', 'bG', 'G',
            'bA', 'A', 'bB', 'B'
        ]
        return (names1 if self.__signal__ == '#' else names2)[self.__note__ % 12]

    def __eq__(self, other):
        if other is None:
            return False
        return self.__note__ == other.__note__

    def __ge__(self, other):
        return self.__note__ >= other.__note__

    def __le__(self, other):
        return self.__note__ <= other.__note__

    def __gt__(self, other):
        return self.__note__ > other.__note__

    def __lt__(self, other):
        return self.__note__ < other.__note__

if __name__ == "__main__":
    print([n.__str__() for n in Note("C")+[n for n in [Note("C"), Note("G")] - Note("C")]])



