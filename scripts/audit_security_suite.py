"""Audit the versioned security-suite manifest against importable scenarios."""

import argparse
import json
import ast
from pathlib import Path


def function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/factorial_prompt_manifest_v1_1.json"),
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("artifacts/SECURITY_SUITE_V1_1_AUDIT"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = []
    failures = []

    for entry in manifest:
        scenario_file = Path(entry["variant_scenario_file"])
        base_file = Path(entry["base_scenario_file"])
        expected = (
            entry["security_suite"]["strict_base_tests"]
            + entry["security_suite"]["added_variant_tests"]
        )
        base_names = function_names(base_file)
        enhancement_names = function_names(Path("src/benchmark_v11.py"))
        wrapper_text = scenario_file.read_text(encoding="utf-8")
        missing_base_tests = [
            name
            for name in entry["security_suite"]["strict_base_tests"]
            if name not in base_names
        ]
        missing_variant_tests = [
            name
            for name in entry["security_suite"]["added_variant_tests"]
            if name not in enhancement_names
        ]
        expected_id = entry["scenario_id"]
        wrapper_has_expected_id = repr(expected_id) in wrapper_text
        wrapper_uses_strict_selector = "selected_security_tests_for" in wrapper_text
        wrapper_uses_variant_selector = "additional_security_tests_for" in wrapper_text
        ok = (
            not missing_base_tests
            and not missing_variant_tests
            and wrapper_has_expected_id
            and wrapper_uses_strict_selector
            and wrapper_uses_variant_selector
        )
        row = {
            "scenario_id": expected_id,
            "expected_tests": expected,
            "missing_base_tests": missing_base_tests,
            "missing_variant_tests": missing_variant_tests,
            "wrapper_has_expected_id": wrapper_has_expected_id,
            "wrapper_uses_strict_selector": wrapper_uses_strict_selector,
            "wrapper_uses_variant_selector": wrapper_uses_variant_selector,
            "ok": ok,
        }
        rows.append(row)
        if not ok:
            failures.append(row)

    report = {
        "manifest": str(args.manifest),
        "entries": len(rows),
        "unique_base_scenarios": sorted({entry["base_scenario"] for entry in manifest}),
        "total_security_test_bindings": sum(len(row["expected_tests"]) for row in rows),
        "failures": failures,
        "rows": rows,
    }
    json_path = args.output_prefix.with_suffix(".json")
    md_path = args.output_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Security Suite v1.1 Audit",
        "",
        f"Entries: `{report['entries']}`",
        "",
        f"Security-test bindings: `{report['total_security_test_bindings']}`",
        "",
        f"Failures: `{len(failures)}`",
        "",
        "| Scenario | Tests | Result |",
        "|---|---|---|",
    ]
    for row in rows:
        result = "ok" if row["ok"] else "failed"
        lines.append(
            f"| {row['scenario_id']} | {', '.join(row['expected_tests'])} | {result} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json_path)
    print(md_path)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
