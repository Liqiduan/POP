<!-- status: draft | author: survey-liaoheng | date: 2026-11-24 -->

# Liao Heng：Nested BSP 与 V-ISA 核实

## 结论

1. **Nested BSP 真实存在**：Heng Liao（华为）《Many Processors, Still One Computer: The Nested Parallel von Neumann Architecture and Nested BSP》，arXiv:2609.16787v2，v1 2026-09-15 / v2 2026-09-30，14 页。
2. **"廖恒的 V-ISA / Nested VISA"未能核实**。该论文全文检索无 `V-ISA`、`virtual instruction`、`contract` 命中；未检索到廖恒署名的 V-ISA 论文、专利或报告。公开文献中 V-ISA 主要指 VISC（虚拟指令集计算机）谱系（Adve/Lattner 等，UIUC），与廖恒无署名关系。
3. **但"昇腾 tile 级虚拟 ISA"确实存在**：PTO-ISA（Parallel Tile Operation），由 Ascend CANN 定义，124 条 tile 指令——这才是提案所指"V-ISA"的实体，归属 CANN 团队而非廖恒。
4. **华为+中科大专利 CN122072555A** 给出了算子编译用虚拟指令集的分层构造（地址空间/内存屏障/通用计算/特殊寄存器），发明人不含廖恒。
5. 廖恒确有**早期虚拟体系结构**工作：1995 年与李三立《新型体系结构概念——虚拟寄存器与并行的指令处理部件》，但属"虚拟寄存器"，非 V-ISA。

## 证据

- **Nested BSP 定义与层次模型**：经典 BSP 递归嵌套；每个 superstep = 并行本地计算 + 交换/聚合 + barrier；每层有自己的 throughput、barrier latency、同步域（§4.1）| <https://arxiv.org/abs/2609.16787> | verified
- **同步语义**：barrier 保证通信完成且可见后才进入下一 superstep；正确性按 phase 论证而非任意交错（§3.1）| 同上 | verified
- **代价模型**：机器由 (处理器数 p, 互联吞吐 g, barrier 延迟 l) 刻画；superstep 代价 = 最慢本地计算 + 通信量/吞吐 + 同步代价；嵌套后逐层叠加，τ scaling law 逐层折算时间 | 同上 | verified
- **层次边界**：package → board → rack → data hall → autonomous zone；SuperNode >8000 节点、6.7 PB/s、400 Tbps、全阵 barrier <10 μs | 同上 | verified
- **关键原句（支持 POP 立论）**："The mapping is frozen into the source, so moving a coarse-grid solve one layer inward is a rewrite rather than a parameter change."（§5.6 批评 MPI+OpenMP）| 同上 | verified
- **嵌套判据**：在任一 scope 上，问题能否分解为少数同类更小问题，且交换/聚合代价相对本地工作很小 | 同上 §5.3–5.4 | verified
- **PTO-ISA**：Ascend CANN 定义的 tile 编程虚拟 ISA，124 条 tile 指令 + 片间通信扩展指令 | <https://www.hiascend.com/en-sg/document/detail/en/CANNCommunityEdition/latest/compiler/ptoisa/docs/PTO-ISA-Header-and-Library-Description.md>、<https://atomgit.com/pengcheng1024/pto-isa> | verified
- **虚拟指令集算子编译专利**：地址空间 0 Generic/1 GM/2 InternalUse/3 L1/4 L0/5 UB；pipe 指令抽象为内存屏障虚拟指令；标量/向量/张量→通用计算虚拟指令；编译链 Triton IR → TritonNPU IR → 虚拟指令 → 按硬件版本号映射；中端做多级缓存管理、double buffer、预取、同步插入 | <https://patents.google.com/patent/CN122072555A/en> | verified（发明人：苏景波、白有辉、王盛南、王森、张弓等，非廖恒）
- **1995 虚拟寄存器论文**：李三立、廖恒，《小型微型计算机系统》16(6):6-11 | 仅见二次引用（<https://ieeexplore.ieee.org/document/794471/references>）| unverified
- **VISC/V-ISA 谱系**：V-ISA 为软硬件解耦的虚拟指令集，低层且语言无关、保留高层信息以支持持续优化 | <https://ieeexplore.ieee.org/document/1303226> | unverified（仅摘要片段）

## 对 POP 的可迁移要素

1. **每层自带 (p, g, l) 的 contract**：把 POP 每层"代价界"直接写成该层 BSP 三元组（或 UB/L1/L0 的带宽-延迟-同步代价），沿用已有术语，不另造。
2. **peer 平等、无中心主控**：正好对应"pipeline/同步交给编译栈自动完成"，而非 host 逐步指挥——这是权威出处。
3. **嵌套判据可判定**：用"能否分解为同类子问题且聚合代价占比小"来判定融合边界是否成立，比经验规则更硬。
4. **"改层 ≠ 重写"**：论文对 MPI+OpenMP 的批评原句，直接支持"层位置应是参数"这一 POP 主张。
5. **地址空间虚拟化 + pipe→屏障虚拟指令**：是 Buffer 层"buffer 复用与同步下沉给编译栈"的现成工程先例（且已在昇腾落地）。
6. **单向精化的论证模板**：BSP 的"按 superstep/phase 论证正确性"可借为 A→B→C→B'→C' 的逐层论证骨架。

## 未能确认

- 廖恒本人任何 V-ISA / Nested VISA 论文、报告、专利：**未找到**。提案"借鉴廖恒 Nested VISA"疑为三源合并（Nested BSP + VISC 通识 + Ascend PTO-ISA）。
- Nested BSP 是否有形式化语义与定理：该文为架构论述性长文，未见 contract、代价界定理、精化关系的形式化。
- 1995 年论文原文未取得，仅二次引用。
- "Nested VISA"是否出自华为内部文档或 CNCC2026 报告 PPT：公开渠道未见。

## 建议下一步

1. **更正引用口径**：把"廖恒的 V-ISA"改写为"廖恒的 Nested BSP（arXiv:2609.16787）+ Ascend CANN 的 PTO-ISA + VISC 谱系"。现有表述一经审稿人核查即失分。
2. V-ISA 的形式化先例改读 VISC 谱系与 PTO-ISA 头文件/库文档，不再在廖恒名下检索。
3. 若确信存在内部 Nested VISA 材料，向海思/CANN 团队索要；中文检索词："嵌套虚拟指令集""分层虚拟 ISA""廖恒 CNCC2026""τ scaling"。
