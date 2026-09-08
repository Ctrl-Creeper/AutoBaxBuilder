#!/usr/bin/env python3
"""POST-HOC EXPLORATORY mechanism analysis for Study 4B.

Read-only over the frozen Study-4B artifacts. Does not re-run the model, does not
re-score completions, does not touch stimuli, evaluator, or confirmatory
statistics. Every number here is descriptive; none of it revises the frozen
confirmatory inference.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
STUDY4B = HERE.parent.parent / "preregistration" / "2026-09-08_study4b_execution"
sys.path.insert(0, str(STUDY4B))

import study4b_execute as ex  # noqa: E402

TAXONOMY = HERE / "TAXONOMY_FROZEN.md"
MANIFEST = HERE / "EXPLORATORY_MANIFEST.json"

SANITIZERS = {
    "sub", "replace", "normpath", "realpath", "abspath", "quote", "escape",
    "secure_filename", "strip", "encode", "decode", "normalize",
}
STRING_PREDICATES = {"startswith", "endswith", "isalnum", "isdigit", "isalpha", "isidentifier"}
RE_MATCHERS = {"match", "fullmatch", "search"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_empty_return(node: ast.AST) -> bool:
    if not isinstance(node, ast.Return):
        return False
    value = node.value
    if value is None:
        return True
    if isinstance(value, ast.Constant) and value.value in (None, False, ""):
        return True
    return isinstance(value, (ast.List, ast.Dict, ast.Tuple)) and not getattr(value, "elts", getattr(value, "keys", []))


def classify_code(code: str, function_name: str) -> dict[str, Any]:
    """Frozen taxonomy coder. Sees only the code and the target function name."""
    result = dict.fromkeys(
        (
            "added_validation",
            "restrictive_rejection",
            "sanitization_filtering",
            "extra_exception_handling",
            "refusal_or_noop",
            "unrelated_implementation_divergence",
            "unparseable",
        ),
        0,
    )
    result["n_lines"] = len([line for line in code.splitlines() if line.strip()])
    result["n_chars"] = len(code)
    for key in ("n_if", "n_raise", "n_try", "n_return"):
        result[key] = 0

    try:
        tree = ast.parse(code)
    except SyntaxError:
        result["unparseable"] = 1
        return result

    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    target = next((f for f in functions if f.name == function_name), None)
    if not functions:
        result["refusal_or_noop"] = 1
    elif target is None:
        result["unrelated_implementation_divergence"] = 1
    else:
        body = [n for n in target.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
        trivial = all(isinstance(n, ast.Pass) or (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)) for n in body)
        if not body or trivial:
            result["refusal_or_noop"] = 1

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            result["n_if"] += 1
            for inner in ast.walk(node):
                if isinstance(inner, ast.Raise) or _is_empty_return(inner):
                    result["restrictive_rejection"] = 1
        elif isinstance(node, ast.Raise):
            result["n_raise"] += 1
            exc = node.exc
            name = exc.func.id if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) else None
            if name == "NotImplementedError":
                result["refusal_or_noop"] = 1
        elif isinstance(node, ast.Try):
            result["n_try"] += 1
            result["extra_exception_handling"] = 1
        elif isinstance(node, ast.Return):
            result["n_return"] += 1
        elif isinstance(node, ast.Compare):
            if any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
                result["added_validation"] = 1
        elif isinstance(node, ast.Call):
            func = node.func
            attribute = func.attr if isinstance(func, ast.Attribute) else None
            plain = func.id if isinstance(func, ast.Name) else None
            if plain == "isinstance" or attribute in STRING_PREDICATES:
                result["added_validation"] = 1
            if attribute in RE_MATCHERS and isinstance(func, ast.Attribute):
                root = func.value
                if isinstance(root, ast.Name) and root.id == "re":
                    result["added_validation"] = 1
            if attribute in SANITIZERS or plain == "secure_filename":
                result["sanitization_filtering"] = 1
    return result


def load_rows() -> list[dict[str, Any]]:
    generation = json.loads((STUDY4B / "study4b_generation_completion_FROZEN.json").read_text())
    evaluation = json.loads((STUDY4B / "study4b_evaluation_FROZEN.json").read_text())
    stimuli = json.loads((STUDY4B / "study4b_ds47_stimuli_SEALED.json").read_text())
    scored = {row["request_id"]: row for row in evaluation["rows"]}
    pairs = {pair["ds_task_id"]: pair for pair in stimuli["pairs"]}

    rows = []
    for gen in generation["rows"]:
        score = scored[gen["request_id"]]
        pair = pairs[gen["ds_task_id"]]
        content = json.loads(
            (STUDY4B / "generation_calls" / gen["request_id"] / "response.json").read_text()
        )["response"]["choices"][0]["message"]["content"]
        code = ex.extract_code(content)
        taxonomy = classify_code(code, pair["execution"]["function_name"])
        rows.append(
            {
                "request_id": gen["request_id"],
                "ds_task_id": gen["ds_task_id"],
                "condition": gen["condition"],
                "repeat": gen["repeat"],
                "completion_tokens": gen["usage"]["completion_tokens"],
                "prompt_tokens": gen["usage"]["prompt_tokens"],
                "truncated": int(gen["finish_reason"] == "length"),
                "runnable": int(score["runner_status"] == "OK"),
                "security_pass": score["security_pass"],
                "capability_pass": score["capability_pass"],
                "joint_pass": score["joint_pass"],
                "response_chars": len(content),
                **taxonomy,
            }
        )
    return rows


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else float("nan")


def by_condition(rows: list[dict], key: str) -> dict[str, float]:
    return {c: mean([r[key] for r in rows if r["condition"] == c]) for c in ("S", "Sprime")}


def describe(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    q = statistics.quantiles(ordered, n=4) if len(ordered) > 3 else [float("nan")] * 3
    return {
        "n": len(ordered),
        "mean": mean(ordered),
        "median": statistics.median(ordered),
        "q1": q[0],
        "q3": q[2],
        "min": ordered[0],
        "max": ordered[-1],
    }


def task_rates(rows: list[dict], key: str) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for row in rows:
        out.setdefault(row["ds_task_id"], {}).setdefault(row["condition"], [])
        out[row["ds_task_id"]][row["condition"]].append(row[key])
    return {task: {c: mean(v) for c, v in cond.items()} for task, cond in out.items()}


def analysis_1_length_executability(rows: list[dict]) -> dict[str, Any]:
    runnable = [r for r in rows if r["runnable"]]
    cap_all = task_rates(rows, "capability_pass")
    cap_runnable = task_rates(runnable, "capability_pass")
    delta_all = mean([v["S"] - v["Sprime"] for v in cap_all.values()])
    complete_tasks = {t: v for t, v in cap_runnable.items() if len(v) == 2}
    delta_runnable = mean([v["S"] - v["Sprime"] for v in complete_tasks.values()])
    return {
        "completion_tokens": {
            c: describe([r["completion_tokens"] for r in rows if r["condition"] == c])
            for c in ("S", "Sprime")
        },
        "response_chars": by_condition(rows, "response_chars"),
        "extracted_code_lines": by_condition(rows, "n_lines"),
        "truncations": {c: sum(r["truncated"] for r in rows if r["condition"] == c) for c in ("S", "Sprime")},
        "non_runnable": {
            c: sum(1 - r["runnable"] for r in rows if r["condition"] == c) for c in ("S", "Sprime")
        },
        "non_runnable_rate": {
            c: 1 - mean([r["runnable"] for r in rows if r["condition"] == c]) for c in ("S", "Sprime")
        },
        "capability_delta_all_ITT": delta_all,
        "capability_delta_runnable_only_DESCRIPTIVE": delta_runnable,
        "n_tasks_with_both_conditions_runnable": len(complete_tasks),
        "max_gap_attributable_to_non_runnable": mean(
            [1 - r["runnable"] for r in rows if r["condition"] == "S"]
        ),
    }


def analysis_2_specification_complexity(rows: list[dict]) -> dict[str, Any]:
    stimuli = json.loads((STUDY4B / "study4b_ds47_stimuli_SEALED.json").read_text())
    spec = {"S": [], "Sprime": []}
    fields = {"S": [], "Sprime": []}
    for pair in stimuli["pairs"]:
        for condition, key in (("S", "s"), ("Sprime", "sprime")):
            text = pair[key]
            spec[condition].append(len(text))
            fields[condition].append(len(re.findall(r"^\s*[-*]\s|^\w[\w ]{0,40}:", text, re.M)))
    quartile_rates = {}
    for condition in ("S", "Sprime"):
        subset = sorted(
            (r for r in rows if r["condition"] == condition), key=lambda r: r["completion_tokens"]
        )
        chunk = max(1, len(subset) // 4)
        quartile_rates[condition] = [
            {
                "median_completion_tokens": statistics.median(
                    [r["completion_tokens"] for r in subset[i : i + chunk]]
                ),
                "security": mean([r["security_pass"] for r in subset[i : i + chunk]]),
                "capability": mean([r["capability_pass"] for r in subset[i : i + chunk]]),
            }
            for i in range(0, chunk * 4, chunk)
        ]
    lengths = [r["completion_tokens"] for r in rows]
    return {
        "prompt_chars": {c: describe(spec[c]) for c in ("S", "Sprime")},
        "prompt_tokens": {
            c: describe([r["prompt_tokens"] for r in rows if r["condition"] == c])
            for c in ("S", "Sprime")
        },
        "spec_field_markers": {c: describe(fields[c]) for c in ("S", "Sprime")},
        "completion_length_quartile_rates": quartile_rates,
        "corr_completion_tokens_capability": statistics.correlation(
            lengths, [r["capability_pass"] for r in rows]
        ),
        "corr_completion_tokens_security": statistics.correlation(
            lengths, [r["security_pass"] for r in rows]
        ),
    }


def analysis_3_taxonomy(rows: list[dict]) -> dict[str, Any]:
    categories = (
        "added_validation",
        "restrictive_rejection",
        "sanitization_filtering",
        "extra_exception_handling",
        "refusal_or_noop",
        "unrelated_implementation_divergence",
        "unparseable",
    )
    return {
        "rates_by_condition": {
            category: by_condition(rows, category) for category in categories
        },
        "ast_counts_by_condition": {
            key: by_condition(rows, key) for key in ("n_if", "n_raise", "n_try", "n_return")
        },
        "restrictive_rejection_outcome_association": {
            flag: {
                "n": sum(r["restrictive_rejection"] == flag for r in rows),
                "security": mean([r["security_pass"] for r in rows if r["restrictive_rejection"] == flag]),
                "capability": mean([r["capability_pass"] for r in rows if r["restrictive_rejection"] == flag]),
            }
            for flag in (0, 1)
        },
    }


def analysis_4_concentration() -> dict[str, Any]:
    analysis = json.loads((STUDY4B / "study4b_analysis_FROZEN.json").read_text())
    differences = analysis["aggregates"]["security"]["task_differences"]
    values = [d["difference"] if isinstance(d, dict) else d for d in differences]
    total = sum(values)
    n = len(values)
    loo = [(total - v) / (n - 1) for v in values]
    ordered = sorted(values, reverse=True)
    return {
        "distribution": describe(values),
        "positive": sum(v > 0 for v in values),
        "zero": sum(v == 0 for v in values),
        "negative": sum(v < 0 for v in values),
        "leave_one_out_range": [min(loo), max(loo)],
        "top_k_contribution_share": {
            f"top_{k}": sum(ordered[:k]) / total for k in (1, 3, 5, 10)
        },
        "delta_excluding_top_5": (total - sum(ordered[:5])) / (n - 5),
    }


def analysis_5_tradeoff(rows: list[dict]) -> dict[str, Any]:
    security = task_rates(rows, "security_pass")
    capability = task_rates(rows, "capability_pass")
    cells: Counter[str] = Counter()
    for task in security:
        ds = security[task]["S"] - security[task]["Sprime"]
        dc = capability[task]["S"] - capability[task]["Sprime"]
        label = (
            f"security {'up' if ds > 0 else 'down' if ds < 0 else 'flat'} / "
            f"capability {'up' if dc > 0 else 'down' if dc < 0 else 'flat'}"
        )
        cells[label] += 1
    per_condition = {}
    for condition in ("S", "Sprime"):
        subset = [r for r in rows if r["condition"] == condition]
        per_condition[condition] = {
            "security_given_capability_pass": mean([r["security_pass"] for r in subset if r["capability_pass"]]),
            "security_given_capability_fail": mean([r["security_pass"] for r in subset if not r["capability_pass"]]),
            "n_capability_fail": sum(1 for r in subset if not r["capability_pass"]),
            "of_which_security_pass": sum(
                r["security_pass"] for r in subset if not r["capability_pass"]
            ),
        }
    return {"task_level_sign_cells": dict(cells), "descriptive_conditioning": per_condition}


def main() -> None:
    rows = load_rows()
    manifest = {
        "schema": "study4b-posthoc-exploratory-v1",
        "label": "POST-HOC EXPLORATORY MECHANISM ANALYSIS",
        "confirmatory_result_unchanged": True,
        "all_analyses_post_hoc": True,
        "no_new_generations": True,
        "no_causal_mediation_claims": True,
        "inputs_sha256": {
            name: sha256_file(STUDY4B / name)
            for name in (
                "study4b_generation_completion_FROZEN.json",
                "study4b_evaluation_FROZEN.json",
                "study4b_analysis_FROZEN.json",
                "study4b_ds47_stimuli_SEALED.json",
                "STUDY4B_CLOSURE_MANIFEST.json",
            )
        },
        "taxonomy_frozen_sha256": sha256_file(TAXONOMY),
        "n_completions_coded": len(rows),
        "analysis_1_length_executability": analysis_1_length_executability(rows),
        "analysis_2_specification_complexity": analysis_2_specification_complexity(rows),
        "analysis_3_behavioural_taxonomy": analysis_3_taxonomy(rows),
        "analysis_4_effect_concentration": analysis_4_concentration(),
        "analysis_5_capability_security_tradeoff": analysis_5_tradeoff(rows),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k.startswith("analysis_")}, indent=2))


if __name__ == "__main__":
    main()
