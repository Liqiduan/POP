#!/usr/bin/env python3
"""校验研究仓库的注册表一致性、依赖 DAG、引用完整性。

用法:
    python3 tools/check_registry.py
    python3 tools/check_registry.py --graph
    python3 tools/check_registry.py --strict   # 警告也视为失败

校验项:
  1. 节点 id 唯一；status 合法；layer 为非负整数
  2. path 存在；两个节点不得指向同一文件
  3. refines 指向的节点存在，且 layer 严格更小（由粗到细）
  4. 依赖图无环
  5. refs 中的 key 存在于 refs.yaml
  6. 文档首行注释（若存在）与 registry 一致
  7. 文档中出现的 [R-KEY] / N-XXX 必须已注册（悬空引用 = 错误）
  8. 未被注册的 docs/*.md 文件（孤儿文件 = 警告）
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "registry" / "nodes.yaml"
REFS = ROOT / "registry" / "refs.yaml"

VALID_STATUS = {"source", "draft", "hypothesis", "conclusion", "decision", "superseded"}
LAYER_NAME = {0: "L0 原始素材", 1: "L1 框架", 2: "L2 概念", 3: "L3 理论", 4: "L4 设计/实验", 5: "L5 执行"}
HEADER_RE = re.compile(r"<!--\s*(N-[A-Z0-9-]+)\s*\|\s*layer:\s*(\d+)\s*\|\s*status:\s*([a-z]+)\s*-->")
REF_RE = re.compile(r"\[(R-[A-Z0-9-]+)\]")
NODE_RE = re.compile(r"\b(N-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*)\b")
SKIP_SCAN = {"README.md", "AGENTS.md"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def load() -> tuple[list[dict], dict[str, dict]]:
    nodes = (yaml.safe_load(NODES.read_text()) or {}).get("nodes") or []
    refs = {r["key"]: r for r in ((yaml.safe_load(REFS.read_text()) or {}).get("refs") or [])}
    return nodes, refs


def check_schema(nodes: list[dict]) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    by_path: dict[str, str] = {}
    for n in nodes:
        nid = n.get("id", "<missing>")
        if nid in by_id:
            err(f"重复节点 id: {nid}")
        by_id[nid] = n

        status = n.get("status")
        if status not in VALID_STATUS:
            err(f"{nid}: 非法 status={status!r}（允许 {sorted(VALID_STATUS)}）")

        layer = n.get("layer")
        if not isinstance(layer, int) or layer < 0:
            err(f"{nid}: layer 必须是非负整数，got {layer!r}")

        path = n.get("path")
        if not path:
            err(f"{nid}: 缺少 path")
            continue
        if path in by_path:
            err(f"{nid}: 与 {by_path[path]} 指向同一文件 {path}")
        by_path[path] = nid
        if not (ROOT / path).exists():
            err(f"{nid}: 文件不存在 {path}")

    return by_id


def check_edges(by_id: dict[str, dict]) -> None:
    for nid, n in by_id.items():
        for parent in n.get("refines") or []:
            if parent not in by_id:
                err(f"{nid}: refines 指向未注册节点 {parent}")
                continue
            pl, cl = by_id[parent].get("layer"), n.get("layer")
            if isinstance(pl, int) and isinstance(cl, int) and not pl < cl:
                err(
                    f"{nid}(L{cl}) refines {parent}(L{pl}) —— 依赖必须由粗到细（parent.layer < child.layer）"
                )
            if parent == nid:
                err(f"{nid}: 自引用")


def check_cycles(by_id: dict[str, dict]) -> None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {k: WHITE for k in by_id}
    stack: list[str] = []

    def dfs(u: str) -> None:
        color[u] = GRAY
        stack.append(u)
        for v in by_id[u].get("refines") or []:
            if v not in by_id:
                continue
            if color[v] == GRAY:
                cyc = " -> ".join(stack[stack.index(v):] + [v])
                err(f"依赖成环: {cyc}")
            elif color[v] == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for k in by_id:
        if color[k] == WHITE:
            dfs(k)


def check_refs(by_id: dict[str, dict], refs: dict[str, dict]) -> None:
    for nid, n in by_id.items():
        for key in n.get("refs") or []:
            if key not in refs:
                err(f"{nid}: refs 指向未注册文献 {key}")
    for key, r in refs.items():
        if r.get("status") == "verified" and not r.get("url"):
            warn(f"{key}: status=verified 但没有 url")


def check_docs(by_id: dict[str, dict], refs: dict[str, dict]) -> None:
    registered = {n["path"] for n in by_id.values() if n.get("path")}
    for nid, n in by_id.items():
        path = ROOT / n.get("path", "")
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:10])

        if n.get("header", True):
            m = HEADER_RE.search(head)
            if not m:
                err(f"{nid}: 缺少首行契约注释 `<!-- {nid} | layer: X | status: Y -->`")
            else:
                hid, hlayer, hstatus = m.group(1), int(m.group(2)), m.group(3)
                if hid != nid:
                    err(f"{nid}: 首行注释 id 不匹配（{hid}）")
                if hlayer != n.get("layer"):
                    err(f"{nid}: 首行 layer={hlayer} 与 registry layer={n.get('layer')} 不一致")
                if hstatus != n.get("status"):
                    err(f"{nid}: 首行 status={hstatus} 与 registry status={n.get('status')} 不一致")

        for key in REF_RE.findall(text):
            if key not in refs:
                err(f"{nid}: 正文引用 [{key}] 未在 refs.yaml 注册")
        for nref in NODE_RE.findall(text):
            if nref not in by_id:
                err(f"{nid}: 正文引用 {nref} 未在 nodes.yaml 注册")

    for p in (ROOT / "docs").rglob("*.md"):
        rel = p.relative_to(ROOT).as_posix()
        if rel in registered or p.name in {"INDEX.md", "README.md"}:
            continue
        warn(f"孤儿文档（未注册）: {rel}")


def print_graph(by_id: dict[str, dict]) -> None:
    children: dict[str, list[str]] = {k: [] for k in by_id}
    roots: list[str] = []
    for nid, n in by_id.items():
        parents = [p for p in (n.get("refines") or []) if p in by_id]
        if not parents:
            roots.append(nid)
        for p in parents:
            children[p].append(nid)

    def walk(nid: str, depth: int = 0) -> None:
        n = by_id[nid]
        print(f"{'  ' * depth}├─ {nid}  [{n.get('status')}]  {n.get('title', '')}")
        for c in sorted(children[nid]):
            walk(c, depth + 1)

    print("\n依赖树（粗 → 细）")
    for r in sorted(roots):
        walk(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", action="store_true")
    ap.add_argument("--strict", action="store_true", help="把警告也当作失败")
    args = ap.parse_args()

    nodes, refs = load()
    by_id = check_schema(nodes)
    check_edges(by_id)
    check_cycles(by_id)
    check_refs(by_id, refs)
    check_docs(by_id, refs)

    print(f"节点 {len(by_id)} 个 ｜ 文献 {len(refs)} 条 ｜ 层级 {sorted({n.get('layer') for n in nodes})}")
    if args.graph:
        print_graph(by_id)

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    print()
    if errors:
        print(f"✗ 失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    if args.strict and warnings:
        print(f"✗ 严格模式失败：{len(warnings)} 个警告")
        return 1
    print(f"✓ 通过：0 个错误，{len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
