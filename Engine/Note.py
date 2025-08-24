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

    def Normalized(self):
        return [i for i in Interval.__members__.values() if i.value == self.value % 12][0]

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
            # input can be like "C" "C4" "C#" "#C" "bC" "Cb" "Cb4"
            # ie. # and b may not be at [0] and octave may miss.
            # extract text and number, then fill correct info to __note__ and __signal__
            # if no octave specified, default is 4.
            # octave is not a variable, it is used to multiply 12 and add to the note
            # __note__ = 0 - .... from C0 to ....

            # find # and b or skip and remove it.
            modify = 0
            if '#' in note:
                self.__signal__ = '#'
                note = note.replace('#', '')
                modify = 1
            elif 'b' in note:
                self.__signal__ = 'b'
                note = note.replace('b', '')
                modify = -1

            # find note name and remove it.
            note_name = note.strip().upper()
            if note_name.startswith('C'):
                self.__note__ = 0 + modify
            elif note_name.startswith('D'):
                self.__note__ = 2 + modify
            elif note_name.startswith('E'):
                self.__note__ = 4 + modify
            elif note_name.startswith('F'):
                self.__note__ = 5 + modify
            elif note_name.startswith('G'):
                self.__note__ = 7 + modify
            elif note_name.startswith('A'):
                self.__note__ = 9 + modify
            elif note_name.startswith('B'):
                self.__note__ = 11 + modify
            else:
                raise ValueError(f"Invalid note name: {note}")
            # find octave number and multiply 12 to the note.
            if len(note) > 1 and note[1:].isdigit():
                octave = int(note[1:])
                self.__note__ += octave * 12
            else:
                self.__note__ += 4 * 12
        else:
            self.__note__ = 48

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
        """
        Convert the note to a string representation.
        __note__ -> % 12 to get name, / 12 to get octave
        __signal__ -> if note is not in CDEFGAB, use __signal__ specified signal to mark.
        """
        if self.__signal__ == '#':
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        elif self.__signal__ == 'b':
            note_names = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
        else:
            raise ValueError("Invalid signal, must be '#' or 'b'")

        octave = self.__note__ // 12
        note_index = self.__note__ % 12
        note_name = note_names[note_index]

        return f"{note_name}{octave}"

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



