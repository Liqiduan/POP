<!-- N-DESIGN-LAYERED-IR | layer: 4 | status: draft -->
# 契约层与混合程序的落地方式（旁路于 AscTile）

**上游**：`N-THEORY-VISA`、`N-PROPOSAL §7`
**下游**：`N-EXP-PLAN`、`N-PLAN-ROADMAP`

---

## 1 三种介入点（按侵入性从低到高）

| 方式 | 做法 | 侵入性 | 何时可用 |
|---|---|---|---|
| **S1 源码注解** | 在 asctile/CANNBot 程序里用装饰器声明契约 | 0（不改编译器） | 立即可用 |
| **S2 产物检查** | 编译后用 trace/调度产物验证 $\Phi,\kappa$ | 0 | 立即可用 |
| **S3 IR 注解** | 在 dialect 上加 `pop.contract` attribute | 中（需编译器配合） | 若 AscTile 开放 dialect 扩展 |

**MVP 走 S1+S2**：先证明"可执行契约 + 下沉"有收益，再谈 S3。

---

## 2 契约的书写形式

```python
from pop import contract, Bound

@contract.tile(
    vars     = ["fusion_groups", "algo"],
    observes = ["graph", "traffic", "ub_capacity_bound", "min_pipe_depth"],
    phi      = ["dep_order_ok()", "footprint() <= ub_capacity"],
    kappa    = Bound.rel("asctile_default", eps=0.15, kind="lower"),
    mu       = "cost_model.v3",
)
def attention(q, k, v):
    with group("qk_softmax") as g:
        s = matmul(q, k.T)
        p = softmax(s * scale)
    contract(g).algo = "flash"
    return matmul(p, v)
```

要点：
- `kappa` 的 `kind="lower"` 强制它是**下界**（剪枝可靠性，见 `N-THEORY-REFINE §3`）；
- `observes` 是白名单：不在列表里的量，Agent 拿不到；
- 契约是**数据**（可序列化），因此可存档、可 diff、可回放。

---

## 3 契约描述（机器可读，落盘为 artifact）

```yaml
contract_tile:
  vars: [fusion_groups, algo, tile_class]
  observes: [graph, per_group_traffic, ub_capacity_bound, min_pipe_depth]
  phi:
    - dep_order_ok()
    - footprint_le(ub_capacity)
    - aligned(k_dim, 32)
  kappa: {ref: asctile_default, eps: 0.15, kind: lower}
  mu: {model: cost_model_v3, ci: 0.15}
  locked: []          # 人锁定的决策，Agent 不可改
```

---

## 4 Checker 的实现

| 检查 | 方法 | 失败输出 |
|---|---|---|
| $\Phi$ 静态部分 | 符号执行 + 区间运算 | `violated(phi_id, reason, witness)` |
| $\Phi$ 动态部分 | 读 trace / 调度产物 | `violated(phi_id, trace_slice)` |
| $\kappa$ 下界 | 解析模型（理想带宽/峰值算力） | `bound(value)` |
| $\mu$ 预测 | 校准后的代价模型 | `estimate(value, ci)` |

**关键设计**：失败必须给出 **witness**（哪个组、哪个变量、超了多少）。没有 witness 的失败对 Agent 无用，也无法用于回跳。

---

## 5 混合层次程序：在既有栈上怎么表达

AscTile 的三层是**编译流程**（同一程序逐层 lower），而 POP 要的是**局部替换**（同一 kernel 内，整体走 asctile、某段走 ascendc/ascvf）。

据调研 AscTile 是单一编译管道，**是否支持"局部嵌入低层片段"未知**。因此 MVP 采取保守路线：

**方案 A（推荐，MVP）**：**不嵌入**。整体仍用 asctile 生成，POP 只通过**参数化**（显式指定某组的 buffer 策略/VF 边界）实现"局部下沉"，由 AscTile 负责生成。
- 优点：零侵入，立刻可做；
- 缺点：下沉粒度受 AscTile 参数面限制（这本身是测量对象：AscTile 暴露了哪些旋钮？）。

**方案 B（P2 之后）**：真正的混合程序——高层 IR 的某个 region 替换为低层实现，需要编译器支持 region 级替换。
- 若 AscTile 不支持，则本课题的"混合编程"主张降级为"参数化局部下沉"，并在论文中诚实声明。

> **影响**：混合层次编程依赖 AscTile 支持 region 级替换。若不支持，C5（混合交接协议）降为 future work，需在设计与论文中相应收缩（T-3.1）。

---

## 6 编译栈接口

```yaml
pop_to_compile:
  program: asctile_source
  contract: contract_tile.yaml
  overrides:            # 下沉时显式指定的旋钮
    - {group: qk_softmax, knob: buffer_depth, value: 3}
    - {group: qk_softmax, knob: vf_boundary, value: after_mul}
  required: [schedule, buffer_plan, sync_plan, compile_log]
  on_violation: {action: reject, report: witness}
```

---

## 7 决策日志（artifact，不是日志文本）

每条记录：

```json
{"step": 7, "layer": "buffer", "action": "set", "target": "qk_softmax.buffer_depth",
 "from": 2, "to": 3, "reason": "gap=0.22 > headroom=0.11",
 "before": {"lat_ms": 1.93}, "after": {"lat_ms": 1.71},
 "phi": "ok", "kappa": "ok", "witness": null}
```

用途：回放、审阅、论文证据、Agent 的上下文（只给相关片段，不给全量）。

---

## 8 风险

| 风险 | 影响 | 应对 |
|---|---|---|
| asctile 是实验特性，API 会变 | 契约注解失效 | 锁定 wheel 版本；契约层与 API 解耦（只依赖语义，不依赖符号名） |
| AscTile 不支持 region 替换 | C5 降级 | 走方案 A（参数化下沉），论文改口径 |
| 契约无法访问调度产物 | 动态 $\Phi$ 做不了 | 退化为静态 $\Phi$ + 实测 $\mu$ |
| 参数面太窄，下沉无空间 | 收益消失 | 这本身是重要发现：可写成"现有栈的旋钮不足"的批评性结论 |

---

## 9 待办

- [ ] T-3.1 确认 AscTile 是否支持 region 级替换（决定 C5 命运）
- [ ] T-3.2 列出 asctile 暴露的全部旋钮（决定下沉空间）
- [ ] T-3.3 实现 S1+S2 的最小 checker（静态 $\Phi$）
- [ ] T-3.4 跑通 1 个算子的契约注解 → 编译 → 检查闭环
