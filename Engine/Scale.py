"""
Scale.py -- Scale class (P1 F3)

Design (ROADMAP F3):
- Scale holds full spelling for every degree.
- Each degree uses a distinct letter name (no duplicate letters).
- Supports __contains__ at pitch-class level (Note in scale).
- Supports spelling_contains() for strict spelling membership.
- Note.in_key(scale) interface delegated here via respell().
"""

from __future__ import annotations
from .Note import Note, _LETTER_PITCH, _LETTER_NAME

_MODES: dict[str, list[int]] = {
    "major":      [0, 2, 4, 5, 7, 9, 11],
    "ionian":     [0, 2, 4, 5, 7, 9, 11],
    "minor":      [0, 2, 3, 5, 7, 8, 10],
    "aeolian":    [0, 2, 3, 5, 7, 8, 10],
    "dorian":     [0, 2, 3, 5, 7, 9, 10],
    "phrygian":   [0, 1, 3, 5, 7, 8, 10],
    "lydian":     [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "locrian":    [0, 1, 3, 5, 6, 8, 10],
    # pentatonic
    "major_pentatonic": [0, 2, 4, 7, 9],
    "minor_pentatonic": [0, 3, 5, 7, 10],
    # blues
    "blues": [0, 3, 5, 6, 7, 10],
    # melodic / harmonic minor
    "melodic_minor":   [0, 2, 3, 5, 7, 9, 11],
    "harmonic_minor":  [0, 2, 3, 5, 7, 8, 11],
}


def _build_notes(tonic: Note, mode: str) -> list[Note]:
    """
    Derive scale notes with correct spelling.

    Each degree advances the letter index by 1, and the accidental is
    computed so that (natural_pitch + accidental) % 12 == actual_pitch_class.
    """
    intervals = _MODES[mode]
    tonic_pc = tonic._pitch % 12
    tonic_octave = tonic._pitch // 12

    if tonic._spelling is not None:
        tonic_letter = tonic._spelling[0]
    else:
        # Infer letter from sharp name (use the natural letter of the pitch class)
        from .Note import _SHARP_NAMES
        name_str = _SHARP_NAMES[tonic_pc]
        letter_char = name_str[0]
        tonic_letter = _LETTER_NAME.index(letter_char)

    notes: list[Note] = []
    for i, semitones in enumerate(intervals):
        letter_idx = (tonic_letter + i) % 7
        actual_pc = (tonic_pc + semitones) % 12
        natural_pc = _LETTER_PITCH[letter_idx]
        # acc in range [-2, +2]
        acc = (actual_pc - natural_pc + 6) % 12 - 6
        pitch = tonic_octave * 12 + tonic_pc + semitones
        note = Note.__new__(Note)
        object.__setattr__(note, "_pitch", pitch)
        object.__setattr__(note, "_spelling", (letter_idx, acc))
        notes.append(note)
    return notes


class Scale:
    """
    Diatonic (or other) scale with full spelling information.

    Construction:
        Scale("C", "major")   -> C D E F G A B
        Scale("F", "major")   -> F G A Bb C D E  (not A#)
        Scale("D", "dorian")  -> D E F G A B C
        Scale(Note("Bb4"), "major") -> also works
    """

    def __init__(self, tonic, mode: str = "major"):
        if isinstance(tonic, str):
            tonic = Note(tonic)
        if not isinstance(tonic, Note):
            raise TypeError(f"tonic must be str or Note, got {type(tonic)}")
        mode = mode.lower()
        if mode not in _MODES:
            raise ValueError(
                f"Unknown mode {mode!r}. Available: {sorted(_MODES)}"
            )
        self.tonic = tonic
        self.mode = mode
        self._notes: list[Note] = _build_notes(tonic, mode)

    # -- collection interface -------------------------------------------------

    def __len__(self) -> int:
        return len(self._notes)

    def __iter__(self):
        return iter(self._notes)

    def __getitem__(self, idx):
        return self._notes[idx]

    def __contains__(self, note: object) -> bool:
        """Pitch-class membership (enharmonic: C# == Db)."""
        if isinstance(note, Note):
            return any(note.pitch_class_eq(n) for n in self._notes)
        return False

    def spelling_contains(self, note: Note) -> bool:
        """Strict membership: pitch class AND spelling both match."""
        return any(note.spelling_eq(n) for n in self._notes)

    # -- note spelling normalization ------------------------------------------

    def respell(self, note: Note) -> Note | None:
        """
        Return the scale-canonical spelling of *note*, or None if the note
        is not in the scale (by pitch class).
        """
        for n in self._notes:
            if note.pitch_class_eq(n):
                return n.respell(n._spelling[0]) if n._spelling else n
        return None

    # -- properties -----------------------------------------------------------

    @property
    def notes(self) -> list[Note]:
        return list(self._notes)

    # -- display --------------------------------------------------------------

    def __str__(self) -> str:
        notes_str = " ".join(str(n) for n in self._notes)
        return f"{self.tonic} {self.mode}: {notes_str}"

    def __repr__(self) -> str:
        return f"Scale({self.tonic!r}, {self.mode!r})"


# -- available modes ----------------------------------------------------------

MODES = sorted(_MODES.keys())


if __name__ == "__main__":
    for mode in ("major", "minor", "dorian", "lydian"):
        s = Scale("C", mode)
        print(s)
    print(Scale("F", "major"))
    print(Scale("Bb", "major"))
    print(Scale("F#", "major"))
    print(Scale("Ab", "minor"))
    print("Bb in F major:", Note("Bb") in Scale("F", "major"))
    print("A# in F major:", Note("A#") in Scale("F", "major"))   # True (same pc)
    print("A# spelling in F major:", Scale("F", "major").spelling_contains(Note("A#")))  # False
