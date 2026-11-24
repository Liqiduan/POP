<!-- N-ARCHIVE-2026-11-24-VISA | layer: 0 | status: source -->
# 归档 #002 · VISA 引用更正（2026-11-24）

> **状态**：`source`（只增不改）
> **来源**：用户澄清 + lead 的公开检索（2026-11-24）
> **作用**：更正归档 #001 中 `A9`/`A11` 对"LiaoHeng V-ISA"的引用口径；**不修改 #001 原文**。

---

## 1 用户澄清（原文）

> liaoheng 的 visa 是指：micro 2026 The contract for nested parallel computers LiaoHeng。找到对应 ppt 和演讲稿作为参考资料，其实是把这个思路引用到算子编程问题的解决中。

---

## 2 核实结果

### 2.1 已核实（公开可查）

| 项 | 内容 | 来源 |
|---|---|---|
| 会议 | MICRO 2026（第 59 届 IEEE/ACM 国际微架构研讨会），Athens | <https://www.microarch.org/micro59/> |
| 场合 | **VISA 2026** = 第 1 届 *Workshop on Virtual ISA for Rapidly Evolving Architectures*，MICRO 2026 的 workshop，2026-10-31 下午 | <https://visaworkshop.github.io/2026/> |
| 报告 | **Invited Talk — LIAO HENG**：*The Contract for Nested Parallel Computers — Taking Another Look at Instruction Set Architecture*，13:00–13:40 EET，Ypsilon III-IV | 同上（Program 节） |
| 讲者身份 | Huawei Fellow & Chief Scientist；Da Vinci AI Core 与 Ascend 系列首席架构师；VISA 2026 组委会成员 | 同上（People 节） |
| workshop 主题 | "The virtual ISA is the contract between them"；agent-facing virtual ISA 为旗舰主题 | 同上（About / CFP） |
| 书面版本（推定） | Heng Liao, *Many Processors, Still One Computer: The Nested Parallel von Neumann Architecture and Nested BSP*, arXiv:2609.16787v2（2026-09-30） | <https://arxiv.org/abs/2609.16787> |

### 2.2 未能获取

- **PPT / 演讲视频 / 逐字稿均未公开**。workshop 站点只提供 6 篇 accepted papers 的 PDF，邀请报告没有挂 slides；未检索到录像。
- 因此 `A9` 中"参考 LiaoHeng 的 V-ISA 研究"目前**只能引到"报告标题 + 会议信息"**，不能引报告内容。
- 推断（`unverified`）：arXiv 论文是同一思想的书面版本；但该文全文不含 "contract" 字样，说明**"契约"是报告的新框架，可能未写进论文**。

### 2.3 更正

- 归档 #001 的 `A9`/`A11` 与调研结论"公开文献无法核实廖恒 V-ISA、疑为三源合并"**部分错误**：错在把 VISA 当成"虚拟指令集（virtual ISA）"，实际是 **workshop 名 + 报告名**。
- 正确表述：*"受廖恒在 VISA 2026（MICRO 2026 workshop）的报告《The Contract for Nested Parallel Computers》启发"*。
- 仍未证实的部分：报告的具体内容（无公开材料），故不得引用其细节。

---

## 3 为什么这个引用很关键（lead 解读，非原文）

报告的标题本身给出了本课题最需要的东西：**"契约"是嵌套并行计算机的层间接口**，而不是文档或约定。

| Liao 的嵌套并行计算机 | POP 的分层算子程序 |
|---|---|
| 层：package → board → rack → data hall → autonomous zone | 层：Tile → Buffer → Register |
| 层间是 **peer-equal**（对等），不是主从 | Agent 与编译栈是**对等层**，不是上下级 |
| 每层都是一个"类计算机"，有自己的 ISA | 每层都有自己的决策变量与观测面 |
| ISA 是**层间的契约**（上层可假设什么、下层保证什么） | 契约五元组 $(\mathcal{V},\Omega,\Phi,\kappa,\mu)$ |
| 代价按层折叠（τ scaling law） | $\kappa_k$ 逐层收紧 |

**这正是"把思路引用到算子编程"的接缝**：算子程序的分层，本质上也是"每一层都是一台小计算机"——Tile 层是一台"融合组计算机"，Buffer 层是一台"搬运计算机"，Register 层是一台"向量计算机"。层与层之间需要一个契约，而这个契约目前是散文。

**必须说清的差异（否则被指生搬硬套）**：

- Liao 的层是**同构的并行层**（每层都是 peer 的机器）；POP 的层是**异构的抽象层**（语义逐级细化，不是同一种东西复制）；
- 因此 POP 借用的是"契约作为层间接口"这一**形式**，不是其并行语义；
- 代价折叠（τ scaling）可借为 $\kappa_k$ 的构造灵感，但不能直接套用（算子层的代价不是时间折叠，而是资源-时延折衷）。

---

## 4 待办

- [ ] T-6.1 向 VISA 2026 组委会（visa.workshop.chairs@gmail.com）或廖恒团队索取 slides
- [ ] T-6.2 若拿到 slides，逐页提取"契约"的定义与形式，回写 `N-THEORY-VISA`
- [ ] T-6.3 检索 MICRO 2026 是否有 session 录像（如 underline.io 类平台）
- [ ] T-6.4 确认 arXiv 论文与报告的关系（是否同一工作的两种表述）

---

## 5 派生节点

- 更正 `N-PROPOSAL` 的参考文献表
- 更正 `N-SURVEY-RELATED §6.3`
- 更正 `N-THEORY-VISA §1`（借用的三件事）
