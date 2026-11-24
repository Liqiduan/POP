<!-- docs/archive/INDEX.md — 归档索引（不参与 nodes 依赖图） -->
# 归档索引

按时间倒序。每条归档都是 `status: source`（只增不改），并注明它派生出了哪些节点。

| 日期 | 文件 | 主题 | 派生节点 |
|---|---|---|---|
| 2026-11-24 | [`2026-11-24-visa-reference-clarification.md`](2026-11-24-visa-reference-clarification.md) | VISA 引用更正：VISA = MICRO 2026 workshop；廖恒报告 *The Contract for Nested Parallel Computers* | `N-PROPOSAL`、`N-THEORY-VISA`、`N-SURVEY-RELATED` |
| 2026-11-24 | [`2026-11-24-initial-thesis.md`](2026-11-24-initial-thesis.md) | 初始研究构想：动机三条、提案六条、参考四项、持久化诉求 | `N-PROPOSAL`、`N-FRAME-PROBLEM`、`N-THEORY-VISA`、`N-THEORY-REFINE` |

---

## 归档规范

1. **只增不改**：纠错不改原文，另开节点并回链。
2. **逐字保真**：用户原话用引用块，不改写；解读放"解读"段，明确区分。
3. **编号**：`A1, A2, …`（断言/原始条目）；`P1, P2, …`（抽取出的可证伪命题）。
4. **状态标注**：每个 P 必须有类型（事实/因果/可行性/效果/理论）与验证方式。
5. **派生关系**：归档末尾必须列出"派生节点"，并在 `registry/nodes.yaml` 中登记。

## 待归档

- [ ] 第一次实验记录（W2 之后）：asctile 跑通数据、平铺基线 token 数
- [ ] 与导师/团队的关键讨论（每次一段，日期命名）
