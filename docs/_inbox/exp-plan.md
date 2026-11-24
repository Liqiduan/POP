<!-- status: draft | author: exp-designer | date: 2026-11-24 -->

# POP 实验协议

全文数字（含种子数、重复数、阈值）均为**建议值†/待定**，无一实测。**主张映射**：a←P2/P3；b←E2 vs E5 的 token/轮数；c←A2/A6；d←A5。目标机 Ascend 950DT（144GB/4TB/s 为厂商口径，unverified，[来源](https://www.techpowerup.com/344062/huawei-ascend-950-ai-accelerator-pictured)）；锁定 CANN/PyAsc 版本、机器 SN 并随产物归档。

## 1. Benchmark（8 项）

| ID | 形态 | 考察决策 | 规模† | 来源 |
|---|---|---|---|---|
| B1 | FlashAttention prefill+decode | 融合边界、softmax 数值、VF/CV 流水、UB 复用 | prefill B8·H32·S4096·D128；decode B64·S8192 | 公开形状，自建驱动 |
| B2 | MoE GroupGEMM | token 分组、专家 tile 调度、权重驻留 | E64·top8·T8192·H4096·I14336 | DeepSeek-V3 形状 |
| B3 | GEMM+epilogue | epilogue 融合、tile、Register 级 vector | 4096³ bf16，bias+GELU+int8 | 公开 samples |
| B4 | Conv-BN-ReLU | 空间 tile、double buffer、CV 流水 | N32·C64·112²·k3 | ResNet-50 |
| B5 | decode GEMV/MLA | 带宽界、KV 布局、归约 | B64·S8192·kv512·rope64 | DeepSeek-V2 形状 |
| B6 | 长序列 KV（chunked prefill） | 切块、HBM↔UB、跨块流水 | B1·S131072·D128 | 自建 |
| B7 | 单 block MegaKernel（100+ 步） | grouping 融合边界、三层耦合 | B8·S2048·H4096 | B1+B3 组装 |
| B8 | AllGather+GEMM 重叠 | 跨卡边界、通信/计算流水 | 8 卡·4096² | 自建 |

## 2. 基线（5+1）

| ID | 基线 | 控制变量 | 公平性陷阱 |
|---|---|---|---|
| E0 | 专家手写 Ascend C | 性能上限参照 | 专家工时、调优轮次单列，不折算成成本 |
| E1 | PyAsc asctile 直出 | 编译栈/DSL 表达力 | 默认 tile 未调优，需给同等调优预算 |
| E2 | 纯 LLM 一次性生成（无分层） | 同模型、同 token/$ 上限 | prompt 信息量须与 POP 首层对齐 |
| E3 | 自动调度器/代价模型搜索 | 同编译-运行预算 | 搜索预算口径（次数 vs 时间）易被放大 |
| E4 | TVM/TileLang | 可移植性待定 | 后端差异≠方法差异，只作同后端对比 |
| E5 | POP-flat（有结构化观测、单层） | 分离“观测”与“分层” | 与 E2 的差异仅在观测 |

公平性：同机器/CANN、同 warmup 与重复、同 token 与编译-运行上限、同数值容差（bf16 相对误差≤2e-2†）；专家工时与 LLM 成本**分表报告**，禁止合并为单一“成本”。

## 3. 指标

| 维度 | 指标 | 测量方法 | 记录格式 |
|---|---|---|---|
| 性能 | 峰值算力 % | 以微基准 GEMM 实测峰值为分母（标称不可靠）；profiler op summary | `tflops, pct_peak` |
| | 端到端时延 | 20 次 warmup + 100 iter 取中位数 | `lat_ms[]` |
| | 有效带宽 | profiler HBM 字节 / 时延 | `gbps` |
| 搜索 | token / 美元 | API usage × 固定价目表版本 | `tok_in, tok_out, usd` |
| | wall-clock / 轮数 / 编译时间 | 日志时间戳，含重试 | `wall_s, iters, compile_s` |
| 质量 | 相对专家差距 | `(T_E0−T)/T_E0` 与 speedup 双报 | `gap_pct` |
| | 跨 seed 分位 | 5 seeds 的 median / P90 | `med, p90` |
| 复现 | 环境指纹 | git sha、CANN、env、随机种子、SN | `env_hash` |
| 人机 | 介入次数/分钟、首可用解时间 | 操作者日志 | `hits, t_first_s` |

每 run 一行 JSONL（`run_id, bench, baseline, seed, env_hash, status, metrics…`），失败也写；聚合 CSV 与原始 trace 一并存档。

## 4. 消融（7 组）

| ID | 去掉什么 | 预期 | 若无变化说明 |
|---|---|---|---|
| A1 | 某层 contract（如 Buffer 层约束隐式化） | 空间爆炸、违规/编译失败升 | contract 非瓶颈或编译器已代偿 |
| A2 | 结构化观测，退回读代码 | token、轮数升，质量降 | 任务过小，观测非必需 |
| A3 | cost model + replay | 试错轮数与编译时间升 | 空间窄，廉价代理足够 |
| A4 | 层数降为 2/1（对照 3 层） | 性能先升后平/降 | 层间解耦收益弱 |
| A5 | 关闭回溯（仅单向贪心） | 若无损则支持主张(d) | 退化则单向精化不成立 |
| A6 | 拆掉 grouping 图，只留 trace | 融合边界决策变差 | 图结构信息冗余 |
| A7 | 换模型/换留出形状 | 收益随模型能力变化但不消失 | 收益来自模型而非方法 |

## 5. 统计口径

每 (bench, baseline) 跑 5 个 LLM seed；时延另做 3 次编译-运行，取中位数的中位数。报 median[IQR] 与 P90（时延 P90 为差尾）。以 bench 为配对单位做 Wilcoxon signed-rank（n=8，最小双侧 p=0.0078†，α=0.05 可行），Holm 校正；加速比给 bootstrap 95% CI 与效应量。失败按 ITT 全报：超时 30 min† 计删失，分类为编译错/数值超容差/性能回退/预算耗尽，附失败率与案例表，不静默剔除。

## 6. 阶段与 go/no-go

| 阶段 | 内容 | 周期† | 通过标准（go） |
|---|---|---|---|
| P0 可行性 | B1/B5，E1/E2 跑通 | 2–3 周 | 编译→profiler 链路可复现、数值达标、schema 完整；否则转模拟器/910B |
| P1 单点收益 | B1/B3/B5×5 seeds，E2 vs POP-3 | 3–4 周 | ≥2/3 中位加速≥1.15×、token≤70%、CI 排除 1 |
| P2 全量对比 | 8 bench×6 基线×5 seeds | 4–6 周 | ≥6/8 优于 E2、中位加速≥1.2×、token 降≥40%、失败率不劣 |
| P3 归因/泛化 | 消融+留出未见 shape（B2/B6 变体）+换模型 | 3–4 周 | 消融方向与预期一致、留出差距≤10%；否则收窄主张 |

## 7. 风险与退路

| 风险 | 应对 | 论文如何仍成立 |
|---|---|---|
| 950 不可得/早期硅不稳 | 降级 910B，协议不变并报硬件差异；CANN 模拟器仅验正确性与编译 | (b)(c)(d) 是搜索/上下文效率主张，与后端无关；真机数据补 910B |
| 无任何昇腾 | GPU 后端（Triton/TileLang）复现方法级对比；950 性能用解析 cost model 投影并标注 | (a) 降级为“可得硬件上接近专家”，预注册 contingency |
| 峰值/带宽未知 | 微基准自测分母；所有 % 相对实测峰值 | 结论不依赖厂商标称 |
| benchmark 污染 | 自建留出形状、去名化 prompt | 泛化实验兜底 |
| API 漂移/专家不可比 | 固定模型快照日期；专家工时单列 | 成本结论限定在快照内 |

**预注册**：上述 bench、基线、指标、go/no-go 在 P0 前冻结；任何偏离记入变更日志并说明理由。
