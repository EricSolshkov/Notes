import PyQt5
from Engine import *


def Temp251To(c1: Chord):
    root = c1.Root()
    n5 = root + Int.Per5
    n2 = n5 + Int.Per5
    c2 = Chord(n2, 'm')
    c5 = Chord(n5, "7")
    return [c2, c5]

SetGlobalSignal("#")

progression = [
    Chord("Cmaj9"),
    Chord("Bm7"),
    Chord("E7b9"),
    Chord("Am9"),
    Chord("Gm9"),
    Chord("C9"),
    Chord("C7b9"),
    Chord("Fmaj9"),
    Chord("D9"),
    Chord("G9"),
    Chord("Cmaj9"),
    Chord("bAmaj7"),
    Chord("Fm7/G"),
    Chord("Cmaj9"),
    Chord("Bm7"),
    Chord("E7"),
    Chord("Am9"),
    Chord("Gm9"),
    Chord("C9"),
    Chord("C7b9"),
    Chord("Fmaj9"),
    Chord("Gm9"),
    Chord("D9"),
    Chord("G11"),
    Chord("C6"),
    Chord("Fdim7/C"),
    Chord("Cmaj7"),

]
for c in progression:
    c.Debug()
    print(f"alias: {c.GetNames()[:3]}\n")

print(Chord.Names([Note("D"), Note("G"), Note("B")]))



