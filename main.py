import PyQt5
from Engine import *


def Temp251To(c1: Chord):
    root = c1.Root()
    n5 = root + Int.Per5
    n2 = n5 + Int.Per5
    c2 = Chord(n2, 'm')
    c5 = Chord(n5, "7")
    return [c2, c5, c1]


SetGlobalSignal("b")

progression = [
    Chord("Dm7"),
    Chord("Em"),
    Chord("Fm"),
    Chord("bB7"),
    Chord("bEmaj7")
]

progression = [
    Chord("Am7"),
    Chord("#Cmaj7"),
    Chord("bAmaj7"),
    Chord("#Fm7"),
    Chord("E7"),
    Chord("#Cmaj7"),
]

ToEb = Temp251To(Chord("bE"))

print(Chord("F/G").Notes())
print(Chord("F/G").GetNames())
