<!-- N-SURVEY-RELATED | layer: 2 | status: draft -->
# 相关工作与差异定位

**上游**：`N-PROPOSAL §6`
**材料状态**：外部事实均标注核实程度；标"未复核"者不得作为论文依据。

---

## 0 一句话定位

> POP 不是又一个 kernel DSL，也不是又一个自动调优器；它是**给已有分层栈补一层可求值契约**，并**用契约做下沉决策**。

已有工作可按"它们在分层什么"分成三类：

| 类别 | 代表 | 层的是什么 | 缺什么 |
|---|---|---|---|
| **语义分层** | MLIR | 变换（pass） | 无代价概念、无"谁何时下沉" |
| **空间搜索** | TVM/Ansor/MetaSchedule | 同一定义域内的配置点 | 不更换变量集合、融合分组非一阶变量 |
| **表达分层** | Triton、TileLang、AscTile、CANNBot-DSL | 编程接口/IR 层级 | 层间契约是散文或隐式，不可求值 |

**POP 落在第三类之上**：接受其分层，补上"可执行契约 + 下沉判据"。

---

## 1 语义分层：MLIR

- MLIR 提供多级 dialect 与 progressive lowering：高层语义逐步降低到硬件，合法性由 dialect conversion 判定，pass 顺序由作者固定。
- **差异**：MLIR 的 lowering 是**语义保持的确定性重写**，层间没有"代价"概念，也没有"何时该停"的问题。POP 的每层是**带代价界的决策问题**，下沉由 gap/headroom 触发而非合法性触发。
- 可借用：dialect 设计、region 嵌套（用于混合层次程序）。

## 2 空间搜索：TVM / Ansor / MetaSchedule

- 在预定义的 schedule 空间内搜索，靠真机反馈或代价模型，按 op/子图优化；Ansor 用 sketch → annotation 的两段式。
- **差异**：它们搜索的是**同一变量集合内的点**；POP 逐层**更换变量集合**，且把"融合分组"本身作为一阶决策变量。
- 可借用：代价模型、采样策略、测量协议。

## 3 表达分层：Triton / TileLang

- Triton 提供 tile 级抽象，编译器负责寄存器与 shared memory；TileLang 提供 tile 原语与更显式的调度。
- **差异**：只给一层 tile 抽象，无分层契约、无观测面；下沉不可显式表达、不可审计。

## 4 最近的工业栈：AscTile（最直接的对照）

据调研（`docs/_inbox/survey-stack.md`，待复核）：

- PyAsc 是 CANN 的 Python 算子语言，接口与 Ascend C 对应；
- `asctile` 是其**实验性**层，以预发布 wheel 分发；
- AscTile = `asctile → ascendc → ascvf` 三个 dialect + 60+ pass，做自动同步、自动分配与复用（图着色）、自动双缓冲、VF 融合与 CV 混合；主平台 950PR。

**结论（对课题至关重要）**："Tile–Buffer–Register 三层 IR + 编译栈自动化"**已是工业实现**，不能作为新颖性主张。

**差异**：
- AscTile 的自动化是**不可协商**的：没有对象让 Agent 声明"这一层我允许劣化 $\epsilon$"；
- 没有代价界、没有层间契约、没有"何时下沉"的判据；
- 没有面向 Agent 的观测面（分组、代价、回退原因）。

## 5 最直接的竞品：CANNBot-DSL + cannbot-skills

据调研：CANNBot 是 CANN 的智能体层；`cannbot-dsl` 是面向 Agent 的显式 Python DSL（存储层级、搬运、tile 手写，同步/VF 由后端插）；`cannbot-skills` 用 prose skill + Stage 门禁承担事实上的契约（Buffer 硬限、同步选型强制记录、R1–R4 设计轮）。

**差异（本文最锋利的论据）**：

| 维度 | CANNBot 的门禁 | POP 的契约 |
|---|---|---|
| 形式 | 自然语言描述 + LLM 判断 | 可执行表达式 |
| 可判定 | 否（依赖"读懂"） | 是（返回通过/违反+原因） |
| 可用于剪枝 | 否 | 是（$\kappa$ 为下界） |
| 可复现 | 弱（判断随模型波动） | 强（同一输入同一结果） |

**证据**：官方材料对硬件参数口径冲突（L0C 128KB vs 256KB；UB 物理 256KB 而 API 返回 248KB，均待复核）。**同一参数两处不一致，prose 契约就无法仲裁**——这正是"契约必须可求值"的实证理由。

## 6 谱系：PTO-ISA、VISC、Nested BSP

### 6.1 PTO-ISA / 虚拟指令集

- 据调研：昇腾 CANN 有 PTO-ISA（Parallel Tile Operation），tile 级虚拟 ISA；另有专利（CN122072555A）给出虚拟指令集算子编译的分层构造（地址空间 GM/L1/L0/UB，pipe 指令抽象为内存屏障，中端做多级缓存管理、双缓冲、预取、同步插入）。
- **用途**：这是"同步/双缓冲下沉给编译栈"的**工程先例**，用来支撑 A6a 的可行性论证，而**不是**本课题的新颖性来源。
- VISC 谱系（Adve/Lattner 等）提供"虚拟指令集保留高层信息以支持持续优化"的通识背景。

### 6.2 Nested BSP（已核实）

`[R-LIAO-NESTED-BSP]` = Heng Liao, *Many Processors, Still One Computer: The Nested Parallel von Neumann Architecture and Nested BSP*, arXiv:2609.16787。

- 内容：以 $(p,g,l)$（处理器数、互联吞吐、屏障延迟）刻画每层机器；superstep 代价 = 最慢本地计算 + 通信/吞吐 + 同步；层为 package→board→rack→zone。
- 可借用：分层代价模型的形式、按 phase 论证正确性的模板、"层位置应是参数而非重写"的论点。
- **不可借用**：其"层"是**并行层级**，不是抽象层级；无 contract/refinement 形式化。原文对 MPI+OpenMP 的批评（"mapping is frozen into the source… a rewrite rather than a parameter change"）恰好支持 POP"层位置可参数化"的主张。

### 6.3 廖恒：VISA 2026 报告（已核实）

**"VISA" 不是虚拟指令集，而是 MICRO 2026 的 workshop 名**（1st Workshop on Virtual ISA for Rapidly Evolving Architectures）。廖恒（Huawei Fellow & Chief Scientist，Da Vinci AI Core / Ascend 系列首席架构师）作了开幕邀请报告：

> *The Contract for Nested Parallel Computers — Taking Another Look at Instruction Set Architecture*
> VISA 2026 @ MICRO 2026, Athens, 2026-10-31 13:00–13:40 EET

其核心主张（据 workshop 主题表述）：**虚拟 ISA 是"机器程序员"与"硅"之间的契约面**——自描述、可验证、可版本化。

- **PPT/视频/逐字稿未公开**：workshop 站点只挂 6 篇 accepted papers，邀请报告无 slides；因此**只能引标题与场合，不能引内容细节**。
- 书面近邻：`[R-LIAO-NESTED-BSP]`（arXiv:2609.16787，14 页，架构论述）。该文不含 "contract" 字样，说明"契约"很可能是报告的**新框架**。
- 引用方式：*"受廖恒在 VISA 2026 的报告《The Contract for Nested Parallel Computers》启发，本文把契约理解为层间接口，并将其从并行层级迁移到算子程序的抽象层级。"*

## 7 算法/调度分离与 LLM 方向

- **Halide**：algorithm/schedule 二分，是"表达分层"的思想源头之一；但其 schedule 是空间变换，不含代价界，也无 Agent 参与。
- **LLM/Agent 生成 kernel**（2024–2025，`[R-LLM-KERNEL]` 待核实具体条目）：以最终正确性/加速比为唯一信号、直接搜索源码。
- **差异**：POP 在中间层给**可验证观测**，使错误在下沉前暴露，而不是等最终 benchmark 失败。

---

## 8 差异汇总表

| 对象 | 层 | 契约 | 代价界 | 下沉判据 | Agent 观测面 |
|---|---|---|---|---|---|
| MLIR | 变换 | conversion 合法性 | 无 | 无 | 无 |
| TVM/Ansor | schedule 空间 | 无 | 有（模型/实测） | 固定空间内 | 弱 |
| Triton/TileLang | 一层 tile | 隐式 | 无 | 无 | 无 |
| AscTile | 三层 IR | 隐式、不可协商 | 无显式 | 无（全自动） | 无 |
| CANNBot-DSL | DSL + Stage | prose 门禁 | 无 | 流程驱动 | 弱 |
| **POP** | 三层（复用 AscTile） | **可执行五元组** | **有（下界）** | **gap/headroom** | **有** |

---

## 9 空白在哪（三选一）

1. **可执行契约 + 下沉决策** ← 本文选择（范围最小、最可证伪）
2. 融合 grouping 的搜索空间与代价界（AscTile/CANNBot 均无法表达）
3. 混合层次程序的交接协议

> 建议：1 为主线，2 作为关键验证实验，3 作为演示。

---

## 10 待办

- [ ] T-5.1 逐条复核 `survey-stack` 的 13 条链接，把 `unverified` 升级为 `verified` 或删除
- [ ] T-5.2 读 AscTile 的 pass 清单，确认"契约层旁路"是否可行（能否在 IR 层插入检查）
- [ ] T-5.3 读 CANNBot skills 的 R1–R4，确认哪些约束是"可求值但没求值"
- [ ] T-5.4 补 `R-LLM-KERNEL` 的 3–5 篇具体文献（KernelBench 等）
- [ ] T-5.5 与 AscTile/CANNBot 团队沟通，确认无撞车
