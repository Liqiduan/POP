<!-- status: draft | author: survey-stack | date: 2026-11-24 -->

# 系统与栈调研：PyAsc / asctile、CANNBot-DSL、Ascend 950

## 结论

1. **PyAsc 与 asctile 真实存在**：PyAsc 是 CANN 的 Python 算子语言，接口与 Ascend C 一一对应；`asctile` 是其**实验性**层（`asc.experimental.asctile`），仅以 `pyasc-dev` 预发布 wheel 分发。
2. **"三层 IR"已是工业实现**：AscTile 为 `asctile`→`ascendc`→`ascvf` 三个 dialect（tile / ≈Ascend C / 寄存器 VF），60+ pass 做自动同步、自动分配与复用、自动双缓冲、VF 融合与 CV 混合。→ POP 的"Tile–Buffer–Register 三层"**不能作为新颖性主张**，只能作为与 AscTile 对齐的落点。
3. **CANNBot 是最直接的竞品**：CANN 的 Infra 智能体层；`cannbot-dsl` 是面向 Agent 的显式 Python DSL，`cannbot-skills` 用 prose skill + Stage 门禁承担事实上的 contract（Buffer 硬限、同步选型强制记录、R1–R4 设计轮）。
4. **Ascend 950PR 已可得**：2026Q1 随 Atlas 350 上市（28 核/112GB 档），950DT 计划 2026Q4。片上 UB 256KB/AIV、L1 512KB/AIC、L0A/B 各 64KB、L0C 256KB；SIMD+SIMT 混合、VF 融合属后端能力。
5. **空白确实存在但很窄**：上述任何一方都没有"每层 contract（决策变量/观测视图/不变量/代价界）+ 由搜索空间收缩触发的逐层下沉"。POP 的新颖性必须收敛到这一条，否则会被审稿人一句"AscTile 已有"打死。

## 事实核实

| 对象 | 结论 | 链接 | 状态 |
|---|---|---|---|
| PyAsc | CANN 社区 Python 算子语言，2025-11 首上线，接口对应 Ascend C | [cann/pyasc README](https://gitcode.com/cann/pyasc) | verified |
| asctile 发布形态 | 实验性扩展，仅预发布 wheel（2026-10 起 26 个 dev 版）；需另装 CANN | [pyasc-dev (PyPI)](https://pypi.org/project/pyasc-dev/) | verified |
| AscTile 架构 | 3 dialect + 60+ pass；自动同步、图着色 buffer 复用、`vf_fusion` 选项；主平台 950PR，910B 仅部分功能；自述 >90% PyAsc 性能 | [PR #174](https://atomgit.com/cann/pyasc/pull/174) | verified |
| CANNBot | CANN 社区 Infra 智能体层，用 Agent 做 AscendC/PyPTO/TileLang/Triton 算子开发与推理优化 | [cannbot-dsl](https://atomgit.com/cann/cannbot-dsl) | verified |
| CANNBot-DSL | 显式 DSL：存储层级、搬运、tile 手写，同步/VF 由后端插；自述"对 Agent 友好" | [编程模型文档](https://raw.gitcode.com/cann/cannbot-dsl/raw/master/docs/zh/guide/overview.md) | verified |
| CANNBot 设计门禁 | Architect/Developer/Perf-Tune 分 Stage；R1–R4 设计轮 + 门禁：Buffer 预算硬限、同步选型强制入库、depth 默认 2 需论证 | [SKILL.md](https://atomgit.com/cann/cannbot-skills/blob/master/plugins-community/cannbot-dsl/core-skills/cannbotdsl-op-design/SKILL.md) | verified |
| Ascend 950 | 950PR（128GB/112GB，1.6/1.4 TB/s）2026Q1 上市为 Atlas 350；950DT（144/96GB，4TB/s）2026Q4 | [IT之家](https://www.ithome.com/0/931/355.htm)、[新浪](https://finance.sina.cn/2025-09-18/detail-infqxmrf3835477.d.html) | verified |
| 950 片上规格 | UB 256KB/AIV（512KB/AIC）、L1 512KB、L0A/B 64KB、L0C 256KB、BIAS/FBUF 4KB、SSBUF 3KB；`get_mem_size("ub")`=248KB | [硬件模型](https://raw.gitcode.com/cann/cannbot-dsl/raw/master/docs/zh/guide/hardware-model.md) | verified |
| 950 算力 | 950PR 32 核档：BF16 486（仅 Cube 432）、FP8 919 TFLOPS | 同上，社区文档口径 | unverified |
| MegaKernel 现状 | `mega_mla` 样例：单次 mixed AIC/AIV kernel 完成 Q/KV 投影+RMSNorm+RoPE+KV 更新+稀疏 attention | [PR #258](https://atomgit.com/cann/cannbot-dsl/pull/258) | verified |

相关工作（known）：MLIR 多级 dialect 与 progressive lowering（Lattner 2020；mlir.llvm.org）；TVM / Ansor / MetaSchedule 的 schedule 搜索（TVM 2018；Ansor OSDI'20）；Triton（MAPL'19）与 TileLang（[2504.17577](https://arxiv.org/abs/2504.17577)）的 tile DSL；Halide 的 algorithm/schedule 分离（PLDI'13）；KernelBench（[2502.10517](https://arxiv.org/abs/2502.10517)）、LLM 引导循环优化（[2511.00592](https://arxiv.org/abs/2511.00592)）、AlphaEvolve（2025）。

## 差异表

**要点**：MLIR 的 lowering 是**语义保持的确定性重写**，层间无"代价"概念，也无"谁在何时下沉"；POP 每层是**带代价界的决策问题**，下沉=可搜索集合被收缩到阈值以下。TVM 的 schedule 是**固定空间内的点搜索**，POP 是**空间本身的逐层收缩**。

| 对象 | POP 的具体不同点 |
|---|---|
| MLIR progressive lowering | 合法性由 dialect conversion 判定、pass 顺序由作者固定；POP 每层是给 Agent 的接口（决策变量+观测+不变量+代价界），下沉由代价模型而非合法性触发 |
| TVM / Ansor / MetaSchedule | 在预定义 schedule 空间内搜索、靠真机反馈、按 op/子图优化；POP 每层**更换变量集合**、用解析代价界剪枝，且把"融合 grouping"本身当决策变量 |
| Triton / TileLang | 只给一层 tile 抽象，无分层契约、无观测面；POP 的下沉显式、可审计、可回放 |
| AscTile（最近） | 同为三层 IR，但同步/分配/双缓冲全自动且不可协商，无代价界、无 Agent 观测面；POP 要求下层的自由度必须在上层以 contract 显式可见 |
| CANNBot-DSL + skills（最近） | 显式、Agent 亲和、有门禁；但 contract 是自然语言+LLM 判断，不可求值、无代价界、无层间下沉账本 |
| Halide | algorithm/schedule 固定二分，schedule 是空间变换而非"决策+代价界"，无 Agent 参与 |
| LLM kernel 生成 | 以最终正确性/加速比为唯一信号、搜索源码；POP 在中间层给可验证观测，使错误在下沉前暴露 |

## 未能确认

- CANNBot-DSL 是否存在**机器可校验**的 contract 实现（只见 prose 门禁 + translate 断言）；未读到其 IR/编译器内部。
- 950DT 是否已量产发货（仅路线图 2026Q4）。
- asctile 正式版发布计划与版本号；">90% PyAsc 性能"仅见 PR 自述，无第三方复现。
- 官方口径冲突：`cannbot-skills` 写 L0C 128KB，`hardware-model` 写 256KB；UB 物理 256KB 而 API 返回 248KB。**这正说明 prose 级契约不可执行。**

## 建议下一步

1. 把新颖性从"三层 API"改写为"可执行的层间 contract + 由搜索空间收缩触发的下沉"，并在 950PR 上与 AscTile/CANNBot-DSL 做正面对照。
2. 选一个 AscTile 与 CANNBot 都无法表达的决策（融合 grouping 的搜索空间及其代价界）作为最小可证伪实验。
3. 用上述规格冲突做素材：contract 必须能被 checker 求值，而非文档约定。
