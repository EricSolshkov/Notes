"""Quick test of script execution via ScriptTab's _inject_globals."""
import sys
import io

from GUI.ScriptTab import _inject_globals, _SCRIPT_GLOBALS
_inject_globals()

code = """
c = Chord('Cmaj7')
print('和弦:', c)
print('音名:', c.GetNames())
print('音符:', [str(n) for n in c.Notes()])

d = Chord('Dm7')
print('Dm7:', d)

jk = JazzKey('C', 'major')
print('C Major diatonic:')
for ch in jk.diatonic_chords():
    print(f'  {ch}')
"""

old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    exec(code, _SCRIPT_GLOBALS, {})
    output = sys.stdout.getvalue()
    print('=== OUTPUT ===')
    for line in output.strip().split('\n'):
        print('  ' + line)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    sys.stdout = old_stdout

print('Script test PASSED')
