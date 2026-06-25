from __future__ import annotations
from typing import TYPE_CHECKING

from .Note import Note
from .interval import Per5, Aug4, Min7, Maj7, Min9, Maj9, Per11, Aug11, Min13, Maj13
from .Scale import Scale

if TYPE_CHECKING:
    from .Chord import Chord

# Roman numeral labels (uppercase)
_ROMAN_UPPER = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']

# Chord type -> jazz quality marker
_JAZZ_QUALITY = {
    'maj7':  '△7',
    'M7':    '△7',
    'm7':    '-7',
    'mM7':   '-△7',
    'dim7':  '°7',
    'aug7':  '+7',
    '':      '',
    'm':     '-',
    'aug':   '+',
    'dim':   '°',
    '6':     '6',
    'm6':    '-6',
    '9':     '9',
    'maj9':  '△9',
    'm9':    '-9',
    '11':    '11',
    'm11':   '-11',
    '13':    '13',
    'm13':   '-13',
    'maj13': '△13',
}

# Diatonic chord types per mode (7 degrees)
_DIATONIC_TYPES = {
    'major':      ['maj7','m7','m7','maj7','7','m7','m7'],
    'ionian':     ['maj7','m7','m7','maj7','7','m7','m7'],
    'minor':      ['mM7','m7','maj7','m7','7','maj7','7'],
    'aeolian':    ['m7','m7','maj7','m7','m7','maj7','7'],
    'dorian':     ['m7','m7','maj7','7','m7','m7','maj7'],
    'lydian':     ['maj7','7','m7','m7','maj7','m7','m7'],
    'mixolydian': ['7','m7','m7','maj7','m7','m7','maj7'],
    'phrygian':   ['m7','maj7','7','m7','m7','maj7','m7'],
    'locrian':    ['m7','maj7','m7','m7','maj7','7','m7'],
}

# Available tensions per diatonic degree (major mode)
_MAJOR_TENSIONS = [
    [Maj9, Aug11, Maj13],
    [Maj9, Per11, Maj13],
    [Min9, Per11, Min13],
    [Maj9, Aug11, Maj13],
    [Min9, Maj9, Aug11, Maj13],
    [Maj9, Per11, Maj13],
    [Min9, Per11, Min13],
]


class JazzKey:
    # Jazz harmonic analysis centered on a tonic and mode (ROADMAP P2 F4).
    #
    # Key features:
    #   diatonic_chords()              -> list[Chord]
    #   roman(chord)                   -> str  ('ii-7', 'V7', 'I△7')
    #   available_tensions(chord)      -> list[Note]
    #   is_tritone_sub(c1, c2)         -> bool
    #   is_secondary_dominant(c, tgt)  -> bool
    #   infer_key(chords)              -> list[(JazzKey, float)]

    def __init__(self, tonic, mode='major'):
        if isinstance(tonic, str):
            tonic = Note(tonic)
        if not isinstance(tonic, Note):
            raise TypeError(f'tonic must be str or Note, got {type(tonic)}')
        self.tonic = tonic
        self.mode = mode.lower()
        self.scale = Scale(tonic, self.mode)

    # -- diatonic chords --------------------------------------------------

    def diatonic_chords(self):
        from .Chord import Chord
        types = _DIATONIC_TYPES.get(self.mode, _DIATONIC_TYPES['major'])
        result = []
        for i, note in enumerate(self.scale):
            t = types[i] if i < len(types) else 'm7'
            if self.mode in ('major', 'ionian') and i == 6:
                try:
                    c = Chord(f'{note}m7b5')
                except Exception:
                    c = Chord(f'{note}m7')
            else:
                c = Chord(f'{note}{t}')
            result.append(c)
        return result

    # -- degree analysis --------------------------------------------------

    def _degree_of(self, root):
        root_pc = root._pitch % 12
        for i, n in enumerate(self.scale):
            if n._pitch % 12 == root_pc:
                return i, 0
        best_i, best_dist = 0, 12
        for i, n in enumerate(self.scale):
            dist = (root_pc - n._pitch % 12 + 12) % 12
            if dist > 6:
                dist -= 12
            if abs(dist) < abs(best_dist):
                best_i, best_dist = i, dist
        return best_i, best_dist

    # -- roman numeral ----------------------------------------------------

    def roman(self, chord):
        root = chord._root
        degree, alteration = self._degree_of(root)
        numeral = _ROMAN_UPPER[degree]
        prefix = '#' * alteration if alteration > 0 else 'b' * (-alteration)
        chord_type = chord._type
        quality = _JAZZ_QUALITY.get(chord_type, chord_type)
        is_minor = chord_type.startswith('m') and not chord_type.startswith('maj')
        is_dim = 'dim' in chord_type
        if is_minor or is_dim:
            numeral = numeral.lower()
        return f'{prefix}{numeral}{quality}'

    # -- available tensions -----------------------------------------------

    def available_tensions(self, chord):
        if self.mode not in ('major', 'ionian'):
            return []
        degree, alteration = self._degree_of(chord._root)
        if alteration != 0:
            return []
        return [chord._root + itv for itv in _MAJOR_TENSIONS[degree]
                if chord._root + itv in self.scale]

    # -- tritone substitution ---------------------------------------------

    def is_tritone_sub(self, c1, c2):
        if c1._type != '7' or c2._type != '7':
            return False
        return abs(c1._root._pitch - c2._root._pitch) % 12 == 6

    # -- secondary dominant -----------------------------------------------

    def is_secondary_dominant(self, chord, target):
        if chord._type != '7':
            return False
        expected = (target._root._pitch + Per5.value) % 12
        return chord._root._pitch % 12 == expected

    # -- key inference ----------------------------------------------------

    @staticmethod
    def infer_key(chords):
        candidates = []
        for root_pc in range(12):
            root_note = Note(48 + root_pc)
            for mode in ('major', 'minor'):
                key = JazzKey(root_note, mode)
                score = _score_key(key, chords)
                candidates.append((key, score))
        candidates.sort(key=lambda x: -x[1])
        max_score = candidates[0][1] if candidates and candidates[0][1] > 0 else 1.0
        return [(k, round(s / max_score, 3)) for k, s in candidates[:5]]

    # -- display ----------------------------------------------------------

    def __str__(self):
        return f'JazzKey({self.tonic} {self.mode})'

    def __repr__(self):
        return f'JazzKey({self.tonic!r}, {self.mode!r})'


def _score_key(key, chords):
    score = 0.0
    for chord in chords:
        if any(chord._root.pitch_class_eq(n) for n in key.scale):
            score += 1.0
        for n in chord.Notes():
            if any(n.pitch_class_eq(sn) for sn in key.scale):
                score += 0.2
    return score
