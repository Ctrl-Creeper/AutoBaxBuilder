"""Rebuild an LLM candidate-audit summary without another model request."""

import argparse
import json
from pathlib import Path

from llm_audit import build_audit_report, write_audit_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild candidate groups from saved LLM audit reviews."
    )
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def write_markdown(output_dir: Path, report: dict) -> Path:
    lines = [
        "# Rebuilt LLM Candidate-Audit Summary",
        "",
        f"Selected samples: {report.get('selection_count', 0)}",
        "",
        f"Candidate groups: {report['candidate_count']}",
        "",
        f"Audit errors: {report.get('audit_error_count', 0)}",
        "",
        "These are unverified coverage candidates. They do not change deterministic scores.",
        "",
    ]
    for index, group in enumerate(report["candidate_groups"], start=1):
        audit = group["audit"]
        cwes = ", ".join(f"CWE-{cwe}" for cwe in audit["candidate_cwes"])
        lines.extend(
            [
                f"## Candidate {index}: {cwes}",
                "",
                f"Fingerprint: {group['fingerprint']}",
                "",
                f"Attack surface: {audit['attack_surface']}",
                "",
                f"Evidence: {audit['evidence']}",
                "",
                f"Suggested deterministic test: {audit['suggested_test']}",
                "",
                "Sample references:",
            ]
        )
        for sample in group["sample_refs"]:
            lines.append(
                "- {scenario_id}, sample {sample_index}, repeat {repeat}".format(
                    **sample
                )
            )
        lines.append("")
    path = output_dir / "llm_audit_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    source = json.loads(args.source_report.read_text(encoding="utf-8"))
    reviews = source.get("reviews")
    if not isinstance(reviews, list):
        raise SystemExit("source report must contain a reviews array")

    report = build_audit_report(
        generation_model=str(source.get("generation_model", "unknown")),
        auditor_model=str(source.get("auditor_model", "unknown")),
        reviews=reviews,
    )
    for key in (
        "dry_run",
        "selection_count",
        "audit_error_count",
        "manifest",
        "run_dir",
    ):
        if key in source:
            report[key] = source[key]

    json_path = write_audit_report(args.output_dir, report)
    markdown_path = write_markdown(args.output_dir, report)
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()
