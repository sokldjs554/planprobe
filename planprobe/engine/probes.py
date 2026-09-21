from __future__ import annotations

import ast
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from planprobe.models import EvidenceRef, ProbeResult, ProbeSpec


def run_probe(workspace: Path, spec: ProbeSpec) -> ProbeResult:
    started = time.perf_counter()
    if spec.kind == "mapping_all_equal":
        verdict, observed, expected, evidence = _mapping_all_equal(workspace, spec)
    elif spec.kind == "field_shape":
        verdict, observed, expected, evidence = _field_shape(workspace, spec)
    elif spec.kind == "pytest_node":
        verdict, observed, expected, evidence = _pytest_node(workspace, spec)
    elif spec.kind == "ast_order":
        verdict, observed, expected, evidence = _ast_order(workspace, spec)
    elif spec.kind == "function_signature":
        verdict, observed, expected, evidence = _function_signature(workspace, spec)
    else:
        verdict, observed, expected, evidence = "unknown", "unsupported probe", "supported probe", []
    return ProbeResult(
        probe_id=spec.id,
        assumption_id=spec.assumption_id,
        verdict=verdict,
        observed=observed,
        expected=expected,
        evidence=evidence,
        duration_ms=round((time.perf_counter() - started) * 1000, 3),
    )


def _source(workspace: Path, rel: str) -> tuple[Path, str, list[str]]:
    path = (workspace / rel).resolve()
    if workspace.resolve() not in path.parents:
        raise ValueError("probe path escaped workspace")
    text = path.read_text(encoding="utf-8")
    return path, text, text.splitlines()


def _mapping_all_equal(workspace: Path, spec: ProbeSpec) -> tuple[str, str, str, list[EvidenceRef]]:
    _, text, lines = _source(workspace, spec.target_path)
    tree = ast.parse(text)
    symbol = str(spec.params["symbol"])
    expected_value = str(spec.params["expected_value"])
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == symbol:
            if isinstance(node.value, ast.Dict):
                values: list[Any] = []
                for value in node.value.values:
                    values.append(ast.literal_eval(value))
                line = node.lineno
                snippet = "\n".join(lines[line - 1 : min(len(lines), getattr(node, "end_lineno", line))])
                verdict = "verified" if values and all(str(v) == expected_value for v in values) else "contradicted"
                return (
                    verdict,
                    f"{symbol} values={values}",
                    f"all values == {expected_value}",
                    [EvidenceRef(id=f"EV-{spec.id}", path=spec.target_path, line_start=line, line_end=getattr(node, "end_lineno", line), snippet=snippet)],
                )
    return "unknown", f"symbol {symbol} not found", f"all values == {expected_value}", []


def _field_shape(workspace: Path, spec: ProbeSpec) -> tuple[str, str, str, list[EvidenceRef]]:
    _, text, lines = _source(workspace, spec.target_path)
    tree = ast.parse(text)
    class_name = str(spec.params["class"])
    field_name = str(spec.params["field"])
    expected_shape = str(spec.params["expected_shape"])
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == field_name:
                    annotation = ast.unparse(item.annotation)
                    shape = "list" if annotation.startswith("list[") else "scalar"
                    verdict = "verified" if shape == expected_shape else "contradicted"
                    line = item.lineno
                    return (
                        verdict,
                        f"{field_name}: {annotation} ({shape})",
                        expected_shape,
                        [EvidenceRef(id=f"EV-{spec.id}", path=spec.target_path, line_start=line, line_end=getattr(item, "end_lineno", line), snippet=lines[line - 1])],
                    )
    return "unknown", f"field {class_name}.{field_name} not found", expected_shape, []


def _pytest_node(workspace: Path, spec: ProbeSpec) -> tuple[str, str, str, list[EvidenceRef]]:
    node = str(spec.params["node"])
    target = node.split("::", 1)[0]
    _, text, lines = _source(workspace, target)
    test_name = node.split("::")[-1]
    tree = ast.parse(text)
    if not any(isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == test_name for item in tree.body):
        return "unknown", f"pytest node {test_name} not found", "pytest node exists and passes", []
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", node],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(workspace)},
    )
    verdict = "verified" if completed.returncode == 0 else "contradicted"
    match_line = next((i + 1 for i, line in enumerate(lines) if test_name in line), 1)
    return (
        verdict,
        (completed.stdout + completed.stderr).strip()[-600:],
        "pytest node passes",
        [EvidenceRef(id=f"EV-{spec.id}", path=target, line_start=match_line, line_end=match_line, snippet=lines[match_line - 1])],
    )


def _ast_order(workspace: Path, spec: ProbeSpec) -> tuple[str, str, str, list[EvidenceRef]]:
    _, text, lines = _source(workspace, spec.target_path)
    tree = ast.parse(text)
    function_name = str(spec.params["function"])
    before_name = str(spec.params["before"])
    after_name = str(spec.params["after"])
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            before_lines: list[int] = []
            after_lines: list[int] = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    name = _call_name(child.func)
                    if name == before_name:
                        before_lines.append(child.lineno)
                    if name == after_name:
                        after_lines.append(child.lineno)
            if before_lines and after_lines:
                before_line = min(before_lines)
                after_line = min(after_lines)
                verdict = "verified" if before_line < after_line else "contradicted"
                return (
                    verdict,
                    f"{before_name}@{before_line}, {after_name}@{after_line}",
                    f"{before_name} occurs before {after_name}",
                    [
                        EvidenceRef(id=f"EV-{spec.id}-A", path=spec.target_path, line_start=before_line, line_end=before_line, snippet=lines[before_line - 1]),
                        EvidenceRef(id=f"EV-{spec.id}-B", path=spec.target_path, line_start=after_line, line_end=after_line, snippet=lines[after_line - 1]),
                    ],
                )
    return "unknown", "call order could not be established", f"{before_name} before {after_name}", []


def _function_signature(workspace: Path, spec: ProbeSpec) -> tuple[str, str, str, list[EvidenceRef]]:
    _, text, lines = _source(workspace, spec.target_path)
    tree = ast.parse(text)
    function_name = str(spec.params["function"])
    expected_params = [str(item) for item in spec.params.get("expected_params", [])]
    mode = str(spec.params.get("mode", "subset"))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            actual = [arg.arg for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]]
            if node.args.vararg is not None:
                actual.append("*" + node.args.vararg.arg)
            if node.args.kwarg is not None:
                actual.append("**" + node.args.kwarg.arg)
            if mode == "exact":
                ok = actual == expected_params
                expected = f"exact params={expected_params}"
            else:
                ok = all(param in actual for param in expected_params)
                expected = f"contains params={expected_params}"
            line = node.lineno
            end = getattr(node, "end_lineno", line)
            header = lines[line - 1] if lines else ""
            return (
                "verified" if ok else "contradicted",
                f"{function_name} params={actual}",
                expected,
                [EvidenceRef(id=f"EV-{spec.id}", path=spec.target_path, line_start=line, line_end=line, snippet=header)],
            )
    return "unknown", f"function {function_name} not found", f"function with params {expected_params}", []


def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
