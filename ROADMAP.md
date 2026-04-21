# 开发路线图与设计决策

> 更新日期: 2026-04-21

---

## 层面一：乐理功能性缺失

### F1 — Note 音名语义重设计（等音异名）

**问题**：`C#` 和 `Db` 在内部完全等价，导致调式分析、和声分析失真。

**设计决策：双轨制而非替换**

不将 `pitch (int)` 换成 `(letter, accidental)` 作为主存储，而是两者共存：

```
Note
├── _pitch: int           ← 主存储，永远存在（向后兼容，算术基础）
└── _spelling: Optional[tuple[int, int]]
    ├── [0]: letter_idx   ← 0=C, 1=D, 2=E, 3=F, 4=G, 5=A, 6=B
    └── [1]: accidental   ← -2=bb, -1=b, 0=natural, 1=#, 2=x
```

- `_spelling = None` 时退化为现有行为（`__signal__` 决定显示）
- Sound→Note 一对多的问题：`Note(48)` 没有 spelling，是"只有音高的声音"；`Note("Db4")` 有 spelling，是"有意义的乐理音符"
- 等音异名规则收敛到：`note.respell(target_letter: int) -> Note`，在有 Key 上下文时调用

**引入节点**：P0，与消除全局状态同批

| 受影响模块 | 影响程度 | 处理方式 |
|-----------|---------|---------|
| `Note.__init__` | 中 | 字符串解析路径直接填充 `_spelling`；int 路径 `_spelling=None` |
| `Note.__str__/__repr__` | 低 | spelling 存在时优先用 spelling 显示，否则用现有逻辑 |
| `Note.__eq__` | 无 | 保持按 `_pitch` 比较（等音 = 相等），满足乐理运算需求 |
| `Chord._notes` | 无 | 和弦内的音保留 spelling，运算产生的音 spelling=None |
| `Scale`（未来） | 依赖此特性 | Scale 构建时必须填充 spelling，是 Scale 的前置依赖 |

---

### F2 — Interval 区分策略：最小化改动方案

**问题**：`Aug4 = Dim5 = 6`，Python Enum 同值别名导致等音程语义丢失；只需区分，无需完整标签化质量属性。

**方案：放弃 Enum，改用类常量**

```python
class Interval:
    __slots__ = ('value', 'name')
    _registry: dict[str, 'Interval'] = {}

    def __init__(self, semitones: int, name: str):
        self.value = semitones
        self.name = name
        Interval._registry[name] = self

    def __eq__(self, other):
        if isinstance(other, Interval):
            return self is other        # 身份相等，Aug4 ≠ Dim5
        return NotImplemented

    def __hash__(self):
        return id(self)

    def enharmonic_eq(self, other: 'Interval') -> bool:
        return self.value == other.value  # 等音程比较

Per1 = Unison = Interval(0, "Per1")
Aug4 = Tritone = Interval(6, "Aug4")   # Tritone 作为显式别名
Dim5 = Interval(6, "Dim5")
# ...
```

**引入节点**：P0，与 F1 同批

| 受影响位置 | 变化 |
|-----------|------|
| `Chord._type` 字典 | 行为不变，但 `Aug4 != Dim5` 成立 |
| `Chord.Structure()` 中的 `in` 检查 | 需改为 `.value` 比较或 `enharmonic_eq` |
| `Note.__sub__` 返回 Interval | 无 spelling 时返回默认（如 `Dim5`），有 spelling 时推导 |
| `Chord.Name()` 内的 if-elif | 当前已是值比较，改动最小 |

---

### F3 — 音阶系统：等音工程化决策

**设计决策**：Scale 必须持有 spelling 信息，强依赖 F1。

**音级 spelling 推导算法**：每个音级必须用不同的字母名，accidental 由 `实际 pitch - 该字母的自然 pitch` 决定。

```
Scale("F", "major")
  根音 letter=3(F), accidental=0
  推导: F G A Bb C D E（不是 A#）
```

**等音选择的工程化边界**：
- Scale 内部统一用规范 spelling
- Scale 之外的 Note 运算结果 `_spelling=None`，由调用方决定是否规范化
- `Note.in_key(scale)` 提供按调规范化的接口

**引入节点**：P1，F1 完成后

---

### F4 — 面向爵士和声的 Key 系统

**爵士 vs 斯波索宾的核心差异**：

| 斯波索宾 | 爵士 |
|---------|------|
| T / SD / D 三功能 | 关注**导音关系**和 tritone |
| 自然调式为主 | 大量使用**和弦音阶理论（chord-scale theory）** |
| 和弦连接看进行倾向 | 关注 available tensions 和 avoid notes |
| 转调有明确界定 | 调性中心模糊，modal interchange 频繁 |

**建议的 JazzKey 模型**：

```python
class JazzKey:
    tonic: Note
    mode: str                    # "major" / "dorian" / "lydian" 等
    def diatonic_chords(self) -> list[Chord]: ...
    def roman(self, chord: Chord) -> str:        # "ii-7", "V7", "I△7", "bVII△7"
    def available_tensions(self, chord: Chord) -> list[Note]: ...
    def is_tritone_sub(self, c1: Chord, c2: Chord) -> bool: ...
    def is_secondary_dominant(self, chord: Chord, target: Chord) -> bool: ...
    def infer_key(chords: list[Chord]) -> list[tuple['JazzKey', float]]: ...  # 多候选+置信度
```

**爵士专项概念的实现优先级**：

| 概念 | 实现复杂度 | 价值 |
|------|----------|------|
| II-V-I 检测 | 低 | 极高 |
| Tritone substitution 识别 | 低 | 高（规则简单：根音相差 tritone，共享 tritone） |
| 调内和弦识别（Roman numeral） | 中 | 高 |
| Secondary dominant | 中 | 高 |
| Chord-scale mapping | 中 | 高（即兴演奏基础） |
| Available tensions | 中 | 中（需要 F1/F3 前置） |
| Modal interchange 检测 | 高 | 中 |
| Coltrane changes | 高（高度经验性） | 低 |

**引入节点**：P2，依赖 F3 完成

---

### F5 — 不完整和弦识别：评分函数替代 if-else

**方案**：现有 `_type` 字典已是完整声明式数据，`Name()` 的 if-else 本质是手工表查询，用加权音程集合匹配自动化。

```python
_interval_weights = {
    Int.Maj3: 1.8, Int.Min3: 1.8,       # 性质决定音
    Int.Maj2: 1.5, Int.Per4: 1.5,        # sus音
    Int.Dim5: 1.3, Int.Min6: 1.3,        # 特征变化音
    Int.Min7: 1.4, Int.Maj7: 1.4,        # 七度
    Int.Per5: 0.15,                       # 爵士中几乎不标 no5
    Int.Maj9: 0.5, Int.Min9: 0.7,        # 延伸音
    Int.Per11: 0.4, Int.Aug11: 0.6,
    Int.Maj13: 0.4, Int.Min13: 0.6,
}

def _score_type_match(input_itvs: frozenset, type_itvs: list) -> float:
    input_set = {i.value for i in input_itvs}
    type_set_vals = [i.value for i in type_itvs]
    matched  = sum(_interval_weights.get(i, 0.3) for i in type_itvs if i.value in input_set)
    missing  = sum(_interval_weights.get(i, 0.3) for i in type_itvs if i.value not in input_set)
    spurious = sum(0.3 for v in input_set if v not in type_set_vals)
    total = matched + missing + spurious
    return matched / total if total > 0 else 0.0
```

**引入节点**：P1，依赖 F2（Interval 区分）完成；完全替换 `Name()` 内的 if-elif，对外接口不变；`nameCost` 退役，用 `1 - score` 替代。

---

### F6 — 和声进行分析

**定性**：经验性远大于通用性，应数据驱动而非逻辑推导。

**参考资源**：

| 资源 | 说明 |
|------|------|
| **music21** | Roman numeral 分析模块值得参考，整体过重 |
| **jazzparser** | HMM 模型，训练于爵士语料，有论文，适合理解建模思路 |
| **iRealPro 数据** | 3000+ 爵士标准曲和弦谱，社区校对，最佳经验数据源 |

**分层架构**：

```
ProgressionAnalyzer
├── Layer 1: 模式检测引擎（规则，通用，可插拔）
│   ├── ProgressionTemplate: [(chord_constraint, label), ...]
│   ├── 支持模糊匹配：constraint 可以是谓词函数
│   └── 返回匹配位置 + 置信度
│
├── Layer 2: 爵士模式库（经验，可替换注册）
│   ├── ii-V-I (major/minor)
│   ├── tritone substitution pairs
│   ├── secondary dominants chain
│   ├── rhythm changes (A/B section templates)
│   └── ...（可扩展注册）
│
└── Layer 3: Key 推断（依赖 F4，滑动窗口对各候选 key 评分）
```

```python
@progression_library.register("ii-V-I/major")
def _is_iivi_major(chords: list[Chord], key: JazzKey) -> float:
    if len(chords) < 3: return 0.0
    score = 0.0
    if key.roman(chords[0]) == "ii-7": score += 0.4
    if key.roman(chords[1]) == "V7":   score += 0.4
    if chords[2].Root() == key.tonic:  score += 0.2
    return score
```

**引入节点**：P3，强依赖 F4（JazzKey）完成；F4 之前可实现基于纯音程关系的弱版本（如 tritone sub 只看根音距离）。

---

## 层面二：工程性缺陷

### E1 — 消除全局可变状态 `__global_signal__`

**引入节点**：P0

删除全局变量，字符串构造路径直接写入 `_spelling`，int 构造路径 `_spelling=None`，`SetGlobalSignal()` 废弃。

---

### E2 — Chord.py 拆分

**引入节点**：P1

```
Engine/
  interval.py       ← Interval 类常量（原 Note.py 中）
  note.py           ← Note 类
  chord_types.py    ← _type / _extender / _modifier / _omit / _suspend 数据
  chord_parser.py   ← _match() / _split() / _parse_omit() + 字符串→Chord 逻辑
  chord_analyzer.py ← Structure() / Get3rd..13th() / Name() / Names() / 评分函数
  chord.py          ← Chord 类（持有状态，调用 parser 和 analyzer）
  scale.py          ← Scale 类
```

---

### E3 — Name() 自动化（与 F5 合并处理）

与 F5 的评分函数方案同步实现，消除 `_type` 字典与 if-elif 树的双维护问题。

---

### E4 — 消除 module load 副作用

**引入节点**：P2（随 E2 拆分时顺带处理）

`Chord.py` 顶层的 sus 和弦生成循环改为 `_build_sus_types()` 函数，在 `chord_types.py` 导入时显式调用一次，或改为懒加载。

---

### E5 — 补全 `__hash__`

**引入节点**：P1

`Note.__hash__ = lambda self: self._pitch`；F2 方案中 Interval 已通过 `id()` 实现 `__hash__`。

---

### E6 — 统一音程模运算

**引入节点**：P0（随 F2 一起处理）

F2 改为类常量后，运算结果通过 `_registry` 查找，`% 24` 问题自然消失。pitch class 运算（`% 12`）与带八度运算（绝对值）明确分离。

---

### E7 — 解析器单元测试

**引入节点**：P1 完成后

重点覆盖：
- 和弦名 → 音列的 round-trip 一致性（构造后重新 `GetNames()` 应包含原始名称）
- 边界输入：`"C##"`、`"Dbb"`、单音、仅根音
- 不完整音列命名的 top-1 结果稳定性

---

## 综合路线图

```
P0（模型根基，同批重构）
├── E1  消除 __global_signal__
├── F1  Note 双轨制（_pitch + _spelling）
├── F2  Interval 放弃 Enum 改类常量
└── E6  统一音程模运算

P1（结构重组 + 核心补完）
├── E2  Chord.py 拆分为 6 模块
├── E3/F5  Name() 改评分函数（消除 if-elif + 不完整和弦支持）
├── F3  Scale 实现（依赖 F1）
├── E5  补全 __hash__
└── E7  解析器单元测试

P2（爵士分析核心）
├── F4  JazzKey（Roman numeral、chord-scale、tritone sub、secondary dominant）
└── E4  消除 module load 副作用

P3（进行分析）
└── F6  ProgressionAnalyzer（规则引擎 + 爵士模式库，依赖 F4）
```
