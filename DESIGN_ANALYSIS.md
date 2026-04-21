# Notes 乐理库架构分析

> 分析日期: 2026-04-21

## 整体结构

```
Engine/           ← 核心乐理引擎（主体）
  Note.py         ← Interval 枚举 + Note 类 + 全局升降号设置
  Chord.py        ← 和弦解析/构建/命名（~760行，占全部代码量 80%+）
  Scale.py        ← 音阶类（仅骨架）
GUI/              ← PyQt5 前端（几乎空白）
main.py           ← 临时测试脚本
```

## 核心亮点（应用价值）

1. **和弦符号解析器设计精巧**：`_type` / `_suspend` / `_extender` / `_modifier` / `_omit` 五层字典 + 正则组合，能解析 `Dm7b5(no3)add9`、`F/G`、`bEmaj7` 等复杂记法
2. **双向转换能力**：和弦名 → 音列 + 音列 → 和弦名，反向命名引入 `nameCost` 权重系统
3. **运算符重载直觉化**：`Note + Interval`、`Note - Note → Interval`、`Note + [Interval]` 等
4. **和弦分析工具链**：`Structure()`、`Get3rd/5th/7th`、`Standardize()`、`Reoctvate()`

## 设计问题

1. **全局可变状态** — `__global_signal__` 影响所有后续构造的 Note，并发/库调用场景致命
2. **Interval 枚举多值映射** — `Aug4=6`/`Tritone=6`/`Dim5=6` 同值别名，等音异名语义丢失
3. **Note 丢失音名语义** — 仅存绝对半音编号，C#/Db 区别靠全局开关而非音本身属性
4. **Chord.py 职责过重** — 类型定义+解析+构建+分析+命名+转位+标准化全在一文件
5. **Name() 反向命名脆弱** — ~260行硬编码 if-elif，新增类型需手动维护两处
6. **__str__/__repr__ 重复** — Note 两个方法逻辑几乎完全相同
7. **Scale 几乎未实现** — 仅构造函数和 __repr__
8. **缺少 __hash__** — Note/Interval 重写了 __eq__ 但未定义 __hash__
9. **命名风格不一致** — PascalCase/snake_case 混用，双下划线 name mangling 非必要

## 下一步开发计划

### 方案 A：完善为通用 Python 乐理库

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| P0: 核心模型重构 | Note 改为 pitch-class + spelling 双轨表示（letter + accidental + octave） | 高 |
| P0: 消除全局状态 | 删除 `__global_signal__`，升降号决策改为 context/key 参数 | 高 |
| P1: 拆分 Chord.py | 分离为 chord_types/chord_parser/chord_analyzer/chord 四模块 | 高 |
| P1: 补全 Scale | 自然大小调、和声/旋律小调、教会调式、五声音阶等 | 中 |
| P2: 反向命名重构 | 用 _type 字典自动生成反向匹配规则替代手写 if-elif | 中 |
| P2: Key/Tonality | 调性上下文、顺阶和弦生成、级数分析 | 中 |
| P3: 序列化/MIDI | 导出 MIDI 事件，与 mido/music21 互操作 | 低 |
| P3: 单元测试 | 和弦解析/命名双向 round-trip 测试 | 中 |

### 方案 B：迁移到 Unity C# 包

- `Interval` enum → C# enum + extension method
- `Note` 类 → struct 值类型，运算符重载原生支持
- `Chord` 解析器 → static readonly Dictionary，解析逻辑 1:1 移植
- 全局状态 → ScriptableObject 配置或注入式 context
- 应用场景：音游音符生成、实时和弦可视化、MIDI 输入分析、乐理教学

建议 Unity 包结构：
```
com.yourname.musictheory/
  Runtime/
    Core/         ← Note, Interval, Chord, Scale (纯数据，无 Unity 依赖)
    Unity/        ← MonoBehaviour 桥接、ScriptableObject 配置
    MIDI/         ← MIDI 输入/输出适配
  Editor/         ← 自定义 Inspector、和弦输入面板
  Tests/
```

## 总结

和弦解析/命名双向系统是最大价值点。主要短板：Note 音名语义缺失 + 全局状态污染。通用库方向优先修 Note 表示；Unity 迁移方向当前架构足够支撑 MVP。
