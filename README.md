# POP · Progressive Operator Programming（渐进式算子编程）

> **一句话**：当 MegaKernel 把"融合什么、怎么切、怎么复用片上缓存"的决策空间推到不可枚举，
> Agent 就不该"一次看全图"，而应沿 **Tile → Buffer → Register** 逐层下沉：
> 每一层只决策该层能决策的事，只观测该层该观测的证据。
>
> **定位**：分层 IR 已由工业栈 AscTile（`asctile→ascendc→ascvf`）占位，不作为新颖性主张。
> 本课题的落点是 **把层间契约从"散文"变成"可执行"**，并用它做下沉决策。
> 详见 [`docs/00-proposal/proposal.md`](docs/00-proposal/proposal.md)。修订理由记于 [`CHANGELOG.md`](CHANGELOG.md)，正式文档只描述当前结论。

**当前阶段**：开题（Proposal）。本仓库同时是研究记录、决策账本和可执行校验器。

---

## 1. 这个仓库解决什么问题

研究工作最容易死在三件事上：

1. **思想活在聊天里** —— 讨论完就散，两周后同一句话要想半天，且"当时为什么这么想"永久丢失；
2. **结论与猜测混在一起** —— 草稿被当成结论引用，假设被当成事实写进论文；
3. **依赖关系失控** —— 文档互相引用成环，或者细粒度文档偷偷定义了粗粒度概念，改一处全崩。

因此本仓库有两条铁律：

- **每一条内容都有状态**：`source / draft / hypothesis / conclusion / decision / superseded`，不允许"无状态"的文字。
- **依赖只能单向、无环、由粗到细**：`refines` 边只能指向 `layer` 更小的节点，禁止同层或反向。细文档可以"前向链接"粗文档，粗文档不回指细节（细节变化不应反向污染框架）。

校验命令（每次改完文档都跑）：

```bash
python3 tools/check_registry.py          # 校验 ID/状态/层级/引用/DAG/文件一致性
python3 tools/check_registry.py --graph  # 额外打印依赖树
```

---

## 2. 目录结构

```
.
├── README.md                     # 本文件：导航 + 规则
├── AGENTS.md                     # Agent 团队章程：角色、边界、汇报格式
├── docs/
│   ├── 00-proposal/
│   │   └── proposal.md           # ★ 开题报告（主文档，L1）
│   ├── 01-framing/
│   │   └── problem-statement.md  # 问题定义与形式化（L2）
│   ├── 02-survey/
│   │   └── related-work.md       # 相关工作与差异定位（L2）
│   ├── 03-theory/
│   │   ├── nested-visa-contract.md   # Nested VISA：contract / 观测 / 影响（L2）
│   │   └── refinement-order.md       # 单向精化与完备性论证（L2）
│   ├── 04-design/
│   │   ├── layered-ir.md         # Tile/Buffer/Register 分层 API 与 IR（L3）
│   │   └── observability.md      # 观测与交互：grouping / trace / cost model（L3）
│   ├── 05-experiments/
│   │   └── plan.md               # 实验方案、基线、指标、消融（L3）
│   ├── 06-roadmap/
│   │   └── milestones.md         # 里程碑、任务分解、风险（L4）
│   ├── _inbox/                   # Agent 产出暂存区（status: draft，待 lead 集成）
│   └── archive/
│       ├── INDEX.md              # 归档索引（时间序）
│       └── 2026-11-24-initial-thesis.md  # ★ 原始构想，逐字保真（L0，只增不改）
├── registry/
│   ├── nodes.yaml                # 节点注册表：id / layer / status / refines / refs
│   └── refs.yaml                 # 参考文献注册表：key / 出处 / 核实状态
├── templates/                    # 讨论、断言、文献笔记模板
└── tools/check_registry.py       # 校验器
```

---

## 3. 状态词表（唯一合法取值）

| 状态 | 含义 | 允许的操作 | 进入论文？ |
|---|---|---|---|
| `source` | 原始素材：对话、邮件、白板照、会议纪要 | **只增不改**；纠错另开节点 | 可引用为"设计来源"，不作论据 |
| `draft` | 草稿，可能就是错的 | 自由改 | 否 |
| `hypothesis` | 可检验的假设；必须写"如何验证/谁负责" | 改需保留历史 | 只能作"待验证命题" |
| `conclusion` | 已论证或已验证 | **需有证据链接**（实验/证明/文献） | 是 |
| `decision` | 已做出的研究或工程选择 | 需记录备选方案与否决理由 | 可写入设计章节 |
| `superseded` | 被取代，保留追溯 | 只能指向替代节点 | 否（仅历史） |

**升级规则**：`draft → hypothesis → conclusion` 不可跳级；任何 `conclusion` 必须能回答"证据在哪"。

---

## 4. 工作流（讨论如何变成资产）

```
讨论/实验
   │  ① 当场记录（可用 templates/discussion-note.md）
   ▼
docs/archive/<日期>-<主题>.md      status: source，只增不改
   │  ② 抽取断言：每条一句话、可判断真假
   ▼
registry/nodes.yaml 中登记 claim 节点  status: draft → hypothesis
   │  ③ 指派验证（实验 / 形式化 / 文献）
   ▼
evidence（docs/05-experiments 结果 / 证明 / refs）
   │  ④ 升级
   ▼
status: conclusion  →  被 proposal / 章节文档引用
```

**引用规范**：
- 文献用 `[R-KEY]`，必须在 `registry/refs.yaml` 中存在；
- 内部节点用 `N-XXX`，必须在 `registry/nodes.yaml` 中存在；
- 未核实的外部来源必须标 `unverified`，正文写"待核实"，**禁止**写成既成事实。

---

## 5. 从哪读起

1. 想快速理解课题 → [`docs/00-proposal/proposal.md`](docs/00-proposal/proposal.md)
2. 想知道原始想法、避免被二手转述带偏 → [`docs/archive/2026-11-24-initial-thesis.md`](docs/archive/2026-11-24-initial-thesis.md)
3. 想知道"这个说法凭什么成立" → [`docs/03-theory/refinement-order.md`](docs/03-theory/refinement-order.md)
4. 想知道下一步做什么 → [`docs/06-roadmap/milestones.md`](docs/06-roadmap/milestones.md)
5. 想知道谁在干什么 → `AGENTS.md` + `python3 tools/check_registry.py --graph`

---

## 6. 名词约定（避免后续歧义）

| 术语 | 本仓库的定义 |
|---|---|
| MegaKernel | 单 kernel 内融合大量算子（≥10 且典型 100+ 计算步骤）、以片上缓存复用与流水隐藏为主导优化手段的程序形态 |
| 层（Layer） | 抽象层级：Tile / Buffer / Register；可扩展（如 Cluster / Slice 层） |
| 精化（Refinement） | 在保留上层决策的前提下，为下层变量赋值；`refines` 边方向：细 → 粗 |
| 决策（Decision） | 对某一层自由变量的取值，是"解"的分量 |
| 观测（Observation） | 该层对外暴露的结构化视图；未被观测的量不允许被该层决策依赖 |
| 契约（Contract） | 每层必须满足的约束集合 + 该层可见视图 + 该层代价界 |
| 下沉（Descend） | Agent 在当前解空间收缩后，切换到更低层的 API/IR 继续搜索 |
