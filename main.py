"""
main.py — Notes 库入口

用法：
  python main.py              → 启动 GUI
  python main.py --cli        → 命令行模式（运行示例代码）

也可在其他脚本中：
  from GUI.Window import run
  run()
"""

import sys
from PyQt5.QtWidgets import QApplication

from Engine.Chord import Chord
from Engine.Note import Note
from Engine.Scale import Scale
from Engine.interval import Int, Per5
from Engine.jazz_key import JazzKey


def run_gui():
    """启动图形界面"""
    from GUI.Window import run
    run()


def run_cli():
    """命令行模式 — 运行示例"""

    def Temp251To(c1: Chord):
        root = c1.Root()
        n5 = root + Per5
        n2 = n5 + Per5
        c2 = Chord(n2, 'm')
        c5 = Chord(n5, "7")
        return [c2, c5, c1]

    progression = [
        Chord("Dm7"),
        Chord("Em"),
        Chord("Fm"),
        Chord("bB7"),
        Chord("bEmaj7"),
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


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()
