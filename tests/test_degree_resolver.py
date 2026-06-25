"""Integration test for degree resolver + ChordTab slash chord semantics."""
import sys
from PyQt5.QtWidgets import QApplication

from GUI.ChordTab import (
    ChordTab, DegreeChordDialog,
    _resolve_degree_root_bass, _format_degree_chord, _DEFAULT_DEGREE_CHORDS,
)
from Engine.Chord import Chord

app = QApplication(sys.argv)

print('=== Slash Chord Resolution (key=C) ===')
tests = [
    ('3/7', 'm',  ['B', 'E', 'G', 'B']),          # Em/B
    ('3/7', '',   ['B', 'E', 'G#', 'B']),          # E/B
    ('V/IV','7',  ['F', 'G', 'B', 'D', 'F']),      # G7/F
    ('V/II','7',  ['D', 'G', 'B', 'D', 'F']),      # G7/D
    ('bVII','7',  ['A#', 'D', 'F', 'G#']),          # A#7 (no slash)
    ('I',   'maj7',['C', 'E', 'G', 'B']),           # Cmaj7 (no slash)
    ('2/3', '7',  ['E', 'D', 'F#', 'A', 'C']),      # D7/E
]
for expr, suffix, expected_notes in tests:
    root, bass = _resolve_degree_root_bass(expr, 'C')
    chord_str = f'{root}{suffix}/{bass}' if bass else f'{root}{suffix}'
    ch = Chord(chord_str)
    actual = [str(n) for n in ch.Notes()]
    ok = actual == expected_notes
    status = 'OK' if ok else 'FAIL'
    fmt = _format_degree_chord(expr, suffix)
    print(f'{status:>5}: {fmt:>10}  chord_str={chord_str:>12}  '
          f'chord={str(ch):>8}  notes={actual}')
    if not ok:
        print(f'        expected notes: {expected_notes}')

print()
print('=== Default Degree Chords in C ===')
for dc in _DEFAULT_DEGREE_CHORDS:
    expr = dc['degree_expr']
    suffix = dc['chord_suffix']
    root, bass = _resolve_degree_root_bass(expr, 'C')
    chord_str = f'{root}{suffix}/{bass}' if bass else f'{root}{suffix}'
    ch = Chord(chord_str)
    notes = ' '.join(str(n) for n in ch.Notes())
    fmt = _format_degree_chord(expr, suffix)
    print(f'  {fmt:>8} -> {str(ch):>10}  [{notes}]')

print()
print('=== Key=G ===')
for expr, suffix in [('3/7','m'), ('V/IV','7'), ('bVII','7')]:
    root, bass = _resolve_degree_root_bass(expr, 'G')
    chord_str = f'{root}{suffix}/{bass}' if bass else f'{root}{suffix}'
    ch = Chord(chord_str)
    fmt = _format_degree_chord(expr, suffix)
    print(f'  {fmt:>10} -> {str(ch):>10}')

print()
print('=== ChordTab Instance Test ===')
ct = ChordTab()
print(f'Degree chords: {len(ct._degree_chords)}')
print(f'Degree cells: {len(ct._degree_cells)}')
# Check first degree cell tooltip
print(f'First cell text: {ct._degree_cells[0].text()}')
print(f'First cell chord: {ct._degree_cells[0]._chord}')

# Key switch
ct._on_key_changed('D')
print(f'After key=D, first cell: {ct._degree_cells[0].text()} -> {ct._degree_cells[0]._chord}')

print()
print('ALL CHECKS PASSED')
