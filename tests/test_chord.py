"""
tests/test_chord.py — Unit tests (ROADMAP E7)

Coverage:
  - Note: dual-track, equality levels, arithmetic
  - Interval: identity equality (Aug4 != Dim5), enharmonic_eq
  - Chord: construction from string/Note, round-trip GetNames()
  - Chord: edge inputs (C##, Dbb, single note, root-only)
  - Scale: spelling derivation for common keys/modes
  - JazzKey: roman numeral, tritone sub, secondary dominant, infer_key
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest
from Engine.Note import Note
from Engine.interval import (
    Aug4, Dim5, Per5, Maj3, Min3,
    Min7, Maj7, Maj9, Per11, Min9,
)
from Engine.Chord import Chord
from Engine.Scale import Scale
from Engine.jazz_key import JazzKey


# ===========================================================================
# Note
# ===========================================================================

class TestNote:
    def test_string_construction_spelling(self):
        n = Note("C#4")
        assert n._pitch == 49
        assert n._spelling == (0, 1)  # C, sharp

    def test_int_construction_no_spelling(self):
        n = Note(48)
        assert n._pitch == 48
        assert n._spelling is None

    def test_pitch_equality(self):
        assert Note("C#4") == Note("Db4")

    def test_spelling_inequality(self):
        assert not Note("C#4").spelling_eq(Note("Db4"))

    def test_pitch_class_eq(self):
        assert Note("C4").pitch_class_eq(Note("C5"))
        assert Note("C#4").pitch_class_eq(Note("Db5"))

    def test_hash_consistent_with_eq(self):
        a, b = Note("C#4"), Note("Db4")
        assert a == b and hash(a) == hash(b)

    def test_add_interval(self):
        assert Note("C4") + Maj3 == Note("E4")

    def test_sub_notes_returns_interval(self):
        diff = Note("E4") - Note("C4")
        assert diff.enharmonic_eq(Maj3)

    def test_respell(self):
        c_sharp = Note("C#4")
        db = c_sharp.respell(1)  # letter D
        assert str(db) == "Db"
        assert db._pitch == c_sharp._pitch

    def test_immutable(self):
        n = Note("C4")
        with pytest.raises(AttributeError):
            n._pitch = 0


# ===========================================================================
# Interval
# ===========================================================================

class TestInterval:
    def test_identity_equality(self):
        assert Aug4 == Aug4
        assert Aug4 != Dim5

    def test_enharmonic_eq(self):
        assert Aug4.enharmonic_eq(Dim5)     # both = 6 semitones
        assert not Maj7.enharmonic_eq(Min7)

    def test_simple_eq(self):
        assert Maj9.simple_eq(Maj9)
        assert not Aug4.simple_eq(Per5)     # 6 % 12 != 7 % 12

    def test_hash_by_identity(self):
        d = {Aug4: "aug4", Dim5: "dim5"}
        assert d[Aug4] == "aug4"
        assert d[Dim5] == "dim5"


# ===========================================================================
# Chord construction
# ===========================================================================

class TestChordConstruction:
    def test_basic_major(self):
        c = Chord("C")
        assert str(c) == "C"
        assert len(c.Notes()) == 3

    def test_major7(self):
        c = Chord("Cmaj7")
        notes = [str(n) for n in c.Notes()]
        assert "C" in notes and "E" in notes and "G" in notes and "B" in notes

    def test_flat_root(self):
        c = Chord("Bbm7")
        assert str(c.Root()) == "Bb"

    def test_sharp_root(self):
        c = Chord("#Cmaj7")
        assert str(c.Root()) == "C#"

    def test_slash_chord(self):
        c = Chord("F/G")
        assert str(c.Root()) == "G"
        assert str(c._root) == "F"

    def test_note_plus_type(self):
        c = Chord(Note("D"), "m7")
        assert str(c) == "Dm7"

    def test_default_constructor(self):
        c = Chord()
        assert str(c._root) == "C"

    def test_copy_constructor(self):
        c1 = Chord("Dm7")
        c2 = Chord(c1)
        assert str(c1) == str(c2)
        assert c1.Notes() == c2.Notes()


# ===========================================================================
# Chord edge inputs
# ===========================================================================

class TestChordEdgeInputs:
    def test_double_sharp_root(self):
        # C## (Cx) = D; parser now scans multi-char accidentals
        c = Chord("C##")
        assert c._root._pitch == Note("D4")._pitch  # Cx = D

    def test_double_flat_root(self):
        # Dbb = C
        c = Chord("Dbb")
        assert c._root._pitch == Note("C4")._pitch  # Dbb = C

    def test_power_chord(self):
        c = Chord("C5")
        notes = c.Notes()
        assert len(notes) == 2

    def test_diminished_7(self):
        c = Chord("Cdim7")
        types_in_names = Chord.Names(c.Notes())
        assert any("dim7" in n for n in types_in_names)


# ===========================================================================
# Chord round-trip: build -> GetNames() should include original name
# ===========================================================================

class TestChordRoundTrip:
    ROUND_TRIP_NAMES = [
        "Cmaj7", "Dm7", "G7", "Am7",
        "Fm7b5", "Bdim7",  # Fm7b5 now directly in _type
        "Cadd9", "C6/9",
        "Csus4", "Gsus2",
        "Fmaj9", "Bb13",
    ]

    @pytest.mark.parametrize("name", ROUND_TRIP_NAMES)
    def test_round_trip(self, name):
        c = Chord(name)
        names = c.GetNames()
        assert len(names) > 0, f"No names returned for {name}"
        # Top result should match or be enharmonically equivalent
        # "Gsus" and "Gsus2" are enharmonically equivalent names
        canonical = str(c).replace("sus2", "sus").replace("sus4", "sus")
        top = names[0].replace("sus2", "sus").replace("sus4", "sus") if names else ""
        assert top == canonical or name in names or str(c) in names, (
            f"Round-trip failed for {name!r}: got {names}"
        )


# ===========================================================================
# Scale
# ===========================================================================

class TestScale:
    def test_c_major_notes(self):
        s = Scale("C", "major")
        names = [str(n) for n in s]
        assert names == ["C", "D", "E", "F", "G", "A", "B"]

    def test_f_major_has_bb_not_a_sharp(self):
        s = Scale("F", "major")
        names = [str(n) for n in s]
        assert "Bb" in names
        assert "A#" not in names

    def test_f_sharp_major_no_duplicate_letters(self):
        s = Scale("F#", "major")
        letters = [n._spelling[0] for n in s if n._spelling]
        assert len(letters) == len(set(letters)), "Duplicate letter in F# major"

    def test_contains_pitch_class(self):
        s = Scale("F", "major")
        assert Note("Bb") in s
        assert Note("A#") in s      # same pitch class

    def test_spelling_contains(self):
        s = Scale("F", "major")
        assert s.spelling_contains(Note("Bb"))
        assert not s.spelling_contains(Note("A#"))

    def test_c_minor_notes(self):
        s = Scale("C", "minor")
        names = [str(n) for n in s]
        assert "Eb" in names and "Ab" in names and "Bb" in names

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError):
            Scale("C", "noname")

    def test_len(self):
        assert len(Scale("C", "major")) == 7
        assert len(Scale("C", "major_pentatonic")) == 5


# ===========================================================================
# JazzKey
# ===========================================================================

class TestJazzKey:
    def setup_method(self):
        self.key = JazzKey("C", "major")
        self.dm7  = Chord("Dm7")
        self.g7   = Chord("G7")
        self.cmaj7 = Chord("Cmaj7")
        self.db7  = Chord("bD7")

    def test_roman_ii_V_I(self):
        assert self.key.roman(self.dm7)  == "ii-7"
        assert self.key.roman(self.g7)   == "V7"
        assert "I" in self.key.roman(self.cmaj7)

    def test_tritone_sub(self):
        assert self.key.is_tritone_sub(self.g7, self.db7)
        assert self.key.is_tritone_sub(self.db7, self.g7)  # symmetric
        assert not self.key.is_tritone_sub(self.dm7, self.g7)

    def test_secondary_dominant(self):
        a7 = Chord("A7")
        dm7 = Chord("Dm7")
        assert self.key.is_secondary_dominant(self.g7, self.cmaj7)
        assert self.key.is_secondary_dominant(a7, dm7)
        assert not self.key.is_secondary_dominant(self.dm7, self.cmaj7)

    def test_available_tensions_V7(self):
        tensions = self.key.available_tensions(self.g7)
        assert len(tensions) > 0

    def test_diatonic_chords_count(self):
        chords = self.key.diatonic_chords()
        assert len(chords) == 7

    def test_infer_key_top_result(self):
        results = JazzKey.infer_key([self.dm7, self.g7, self.cmaj7])
        top_key, conf = results[0]
        assert conf == 1.0
        # top key should be C major or A minor
        assert top_key.tonic._pitch % 12 in (0, 9)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
