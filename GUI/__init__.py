"""
GUI — Notes 库图形界面

模块：
  Window.py      — 主窗口（QMainWindow + QTabWidget）
  ScriptTab.py   — 脚本编辑与执行 Tab
  ChordTab.py    — 和弦按钮矩阵 Tab（12 级数）
  SoundPlayer.py — 音频合成与播放
  Parser.py      — 旧版解析器（保留兼容）
"""

from GUI.Window import MainWindow, run
from GUI.ScriptTab import ScriptTab
from GUI.ChordTab import ChordTab
from GUI.SoundPlayer import play_chord, play_note, play_arpeggio
