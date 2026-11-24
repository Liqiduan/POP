# Agent 团队章程

根 Agent：`lead`（导师 / 研究负责人 / 唯一集成者）。
本文件定义角色、写入边界与汇报格式。子代理只写自己名下的文件，**不得**修改他人文件或 registry。

---

## 1. 角色

| 角色 | 名称 | 职责 | 写入边界 |
|---|---|---|---|
| 导师/集成 | `lead` | 拆解任务、审阅、集成、维护 registry 与 DAG、对结论负责 | 全部（唯一可写 registry） |
| 文献调研·理论源流 | `survey-liaoheng` | 核实 Liao Heng 的 Nested BSP 与 V-ISA 工作；提炼可迁移的形式化要素 | `docs/_inbox/survey-liaoheng.md` |
| 文献调研·系统与栈 | `survey-stack` | 核实 PyAsc asctile、CANNBot DSL、Ascend 950、MegaKernel 趋势；梳理相关系统（MLIR/TVM/Triton/TileLang）差异 | `docs/_inbox/survey-stack.md` |
| 红队/审稿人 | `critic-redteam` | 以苛刻审稿人视角攻击立论、形式化与实验设计；给出可执行的修补建议 | `docs/_inbox/critic-redteam.md` |
| 实验设计 | `exp-designer` | 指标、基线、消融、统计口径、可复现性；Ascend 950 上的验证路径 | `docs/_inbox/exp-plan.md` |
| 归档/一致性 | `scribe`（按需） | 把讨论压成 source 归档 + 抽取断言；跑校验器 | `docs/archive/*`、报告校验结果 |

> 角色不是头衔而是**写入边界**：边界清晰才能并行、才能避免互相覆盖。

## 2. 协作规则

1. **单一写入者**：一个文件同一时间只有一个 agent 写。子代理产出先落 `docs/_inbox/`，由 `lead` 决定是否升级为正式节点。
2. **状态先行**：子代理产出一律 `status: draft`；`hypothesis` / `conclusion` 只能由 `lead` 升级，且必须附证据。
3. **不臆造事实**：外部来源给 URL 并标注 `verified` / `unverified` / `known`（领域通识）。无法核实就写"未能核实"，不要补全细节。
4. **可追溯**：每条实质断言标注来源（`[R-KEY]` 或 `N-XXX` 或实验编号）。
5. **改动后自检**：`lead` 每次集成后运行 `python3 tools/check_registry.py`。
6. **不越权**：子代理不得运行会改动全局状态的命令（如 git push、修改 registry、批量重写他人文档）。

## 3. 汇报格式（子代理 → lead）

```
## 结论（≤5 条，每条一句话且可判断真假）
## 证据
- [来源] 说明 | URL | 核实状态
## 与 POP 提案的关系（支持 / 削弱 / 需要修正的具体句子）
## 我未能确认的事（明确列出）
## 建议的下一步（≤3 条）
```

篇幅上限：正文 ≤ 1200 字（中文）。宁短勿虚。

## 4. 派发记录

| 日期 | 角色 | 任务 | 产出 | 状态 |
|---|---|---|---|---|
| 2026-11-24 | survey-liaoheng | Nested BSP + V-ISA 核实 | `docs/_inbox/survey-liaoheng.md` | 完成（V-ISA 未能核实，已改口径）|
| 2026-11-24 | survey-stack | PyAsc/CANNBot/950/相关工作 | `docs/_inbox/survey-stack.md` | 完成（AscTile 三层已占位，已改定位）|
| 2026-11-24 | critic-redteam | 立论与实验红队 | `docs/_inbox/critic-redteam.md` | 完成（3 处致命问题，已修）|
| 2026-11-24 | exp-designer | 评测协议 | `docs/_inbox/exp-plan.md` | 完成（已合并进 N-EXP-PLAN）|
