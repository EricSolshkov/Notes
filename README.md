# Notes — 爵士乐理分析库

Python 乐理分析库，面向爵士和声研究。提供音符、音程、和弦、音阶的完整建模，以及爵士调性分析功能。

## 功能概览

| 模块 | 功能 |
|------|------|
| `Note` | 音符双轨制（音高 + 拼写），不可变，支持等音比较 |
| `Interval` | 音程类常量，身份等价（`Aug4 ≠ Dim5`） |
| `Chord` | 和弦构造、命名、转位、评分识别 |
| `Scale` | 音阶构造，带完整拼写信息（F大调有 Bb 不是 A#） |
| `JazzKey` | 爵士调性分析：级数标记、可用张力音、tritone substitution |

---

## 快速开始

```python
from Engine import Note, Interval, Chord, Scale, JazzKey
from Engine import Maj3, Min7, Per5, Aug4, Dim5
```

### Note — 音符

```python
# 字符串构造（带拼写信息）
c4  = Note("C4")
cs4 = Note("C#4")
db4 = Note("Db4")

# 整数构造（无拼写，只有音高）
n   = Note(48)   # C4，但 _spelling=None

# 等价层级（三层）
cs4 == db4                      # True  — 音高相等（等音算相等）
cs4.pitch_class_eq(Note("C#5")) # True  — 忽略八度
cs4.spelling_eq(db4)            # False — 严格拼写不同

# 算术
Note("C4") + Maj3               # E4
Note("E4") - Note("C4")         # → Interval(Maj3, 4)
Note("C4").respell(1)           # Db4（保持 pitch，换成 D 字母）
```

### Interval — 音程

音程是类常量，身份相等（不同名称的等音程是不同对象）：

```python
Aug4 == Aug4          # True
Aug4 == Dim5          # False  ← 身份不同
Aug4.enharmonic_eq(Dim5)   # True   ← 半音数相同（都是 6）
Maj9.simple_eq(Maj2)       # True   ← mod 12 相等

# 可用常量（部分）
Per1  Min2  Maj2  Min3  Maj3  Per4
Aug4  Dim5  Per5  Min6  Maj6  Min7  Maj7
Oct   Min9  Maj9  Per11 Aug11 Maj13 Min13  DuoOct
```

### Chord — 和弦

```python
# 字符串构造
Chord("Cmaj7")       # C△7
Chord("Dm7")         # D-7
Chord("G7b9")        # G7♭9
Chord("Fm7b5")       # Fø7（半减七）
Chord("F/G")         # F大三和弦，低音 G

# Note + 类型字符串
Chord(Note("D"), "m7")   # Dm7

# 访问
c = Chord("Cmaj7")
c.Notes()            # [C4, E4, G4, B4]
c.Root()             # C4
str(c)               # "Cmaj7"

# 转位
c.Inv(1)             # 第一转位（E4 在底）

# 从音列识别最可能的和弦名（多候选，按代价排序）
notes = [Note("C4"), Note("E4"), Note("G4"), Note("Bb4")]
Chord.Names(notes)   # ["C7", ...]

# 指定根音
Chord.Names(notes, force_root=Note("G4"))
```

**支持的和弦语法**

| 类别 | 示例 |
|------|------|
| 三和弦 | `C` `Cm` `Caug` `Cdim` |
| 七和弦 | `Cmaj7` `Cm7` `C7` `CmM7` `Cdim7` `Caug7` `Cm7b5` |
| 六和弦 | `C6` `Cm6` `C6/9` |
| 九、十一、十三 | `C9` `Cmaj9` `C11` `C13` `Cmaj13` |
| 挂留 | `Csus2` `Csus4` `C7sus4` |
| 省略 | `C(no5)` `Cmaj7(no3)` |
| 修饰 | `C7b9` `C7#11` `C7b13` |
| 附加 | `Cadd9` `Cadd11` |
| 斜线 | `F/G` `Cmaj7/E` |
| 五度和弦 | `C5` |

### Scale — 音阶

```python
Scale("C", "major")     # C D E F G A B
Scale("F", "major")     # F G A Bb C D E  （Bb，不是 A#）
Scale("Bb", "major")    # Bb C D Eb F G A
Scale("D", "dorian")    # D E F G A B C
Scale("C", "minor")     # C D Eb F G Ab Bb

# 集合操作
s = Scale("F", "major")
Note("Bb") in s                   # True  — 音高类成员
Note("A#") in s                   # True  — 等音也算在内
s.spelling_contains(Note("Bb"))   # True
s.spelling_contains(Note("A#"))   # False — 拼写不匹配
s.respell(Note("A#4"))            # Bb4   — 返回调内规范拼写

# 支持的调式
from Engine import MODES
# ['aeolian', 'blues', 'dorian', 'harmonic_minor', 'ionian',
#  'locrian', 'lydian', 'major', 'major_pentatonic', 'melodic_minor',
#  'minor', 'minor_pentatonic', 'mixolydian', 'phrygian']
```

### JazzKey — 爵士调性分析

```python
key = JazzKey("C", "major")

# 调内和弦（七和弦）
key.diatonic_chords()
# [Cmaj7, Dm7, Em7, Fmaj7, G7, Am7, Bm7b5]

# 级数标记（爵士记谱）
key.roman(Chord("Dm7"))    # "ii-7"
key.roman(Chord("G7"))     # "V7"
key.roman(Chord("Cmaj7"))  # "I△7"
key.roman(Chord("Bb7"))    # "bVII7"

# 可用张力音（大调模式）
key.available_tensions(Chord("G7"))   # [A, D, E]（Maj9, Aug11, Maj13）

# Tritone substitution（共享 tritone，根音相差 6 半音）
key.is_tritone_sub(Chord("G7"), Chord("bD7"))     # True
key.is_tritone_sub(Chord("G7"), Chord("Db7"))     # True

# Secondary dominant（V7/x：和弦根音是目标根音的纯五度上方）
key.is_secondary_dominant(Chord("G7"),  Chord("Cmaj7"))  # True  (G = V of C)
key.is_secondary_dominant(Chord("A7"),  Chord("Dm7"))    # True  (A = V of D)

# 调性推断（从和弦进行推断最可能的调，返回 top-5 带置信度）
JazzKey.infer_key([Chord("Dm7"), Chord("G7"), Chord("Cmaj7")])
# [(JazzKey(C major), 1.0), (JazzKey(A minor), 1.0), ...]
```

---

## 项目结构

```
Notes/
├── Engine/
│   ├── interval.py       — Interval 类常量（所有音程对象）
│   ├── Note.py           — Note 类（双轨制：_pitch + _spelling）
│   ├── chord_types.py    — 和弦类型数据（_type / _extender / _modifier / _omit）
│   ├── chord_parser.py   — 字符串 → 和弦结构解析
│   ├── chord_analyzer.py — Structure / Name / Names / 评分函数
│   ├── Chord.py          — Chord 类（薄包装，委托上两个模块）
│   ├── Scale.py          — Scale 类（调式音阶，带拼写推导）
│   ├── jazz_key.py       — JazzKey 类（爵士调性分析）
│   └── __init__.py       — 公共 API 导出
├── GUI/
│   ├── Parser.py
│   └── Window.py
├── tests/
│   └── test_chord.py     — 52 个单元测试（pytest）
├── main.py
├── ROADMAP.md            — 设计决策与开发路线图
└── README.md             — 本文件
```

---

## 设计要点

### Note 等价三层

```python
# 层级 1：__eq__  — 音高相等（等音算相等）
Note("C#4") == Note("Db4")                        # True

# 层级 2：pitch_class_eq  — 忽略八度
Note("C4").pitch_class_eq(Note("C5"))             # True

# 层级 3：spelling_eq  — 严格相等（音高 + 拼写）
Note("C#4").spelling_eq(Note("Db4"))              # False
```

### Interval 等价三层

```python
# 层级 1：__eq__  — 身份相等（同一对象）
Aug4 == Dim5                    # False（不同对象，即使半音数相同）

# 层级 2：enharmonic_eq  — 半音数相等
Aug4.enharmonic_eq(Dim5)        # True（都是 6 半音）

# 层级 3：simple_eq  — mod 12 相等（复合音程折叠）
Maj9.simple_eq(Maj2)            # True（14 % 12 == 2 % 12）
```

### 和弦识别：评分函数

`Chord.Names()` 使用加权音程集合匹配而非 if-else 树。每种和弦类型被评分：

$$\text{score} = \frac{\sum_{\text{matched}} w_i}{\sum_{\text{matched}} w_i + \sum_{\text{missing}} w_i + \sum_{\text{spurious}} 0.3}$$

权重体现乐理重要性：三度音（1.8）> 七度音（1.4）> 五度音（0.15）。支持不完整音列识别。

---

## 运行测试

```bash
pip install pytest
python -m pytest tests/test_chord.py -v
```

预期输出：`52 passed`。

---

## 依赖

- Python 3.10+
- `PyQt5`（GUI，可选）
- `pytest`（测试）
