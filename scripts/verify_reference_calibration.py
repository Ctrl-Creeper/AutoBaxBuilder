"""Summarize declared reference-fixture calibration without running Docker."""

import argparse
import json
import re
from pathlib import Path

from reference_calibration import summarize_calibration


def report_heading(registry: dict) -> str:
    benchmark_version = str(registry.get("benchmark_version", "unknown"))
    match = re.search(r"_v(\d+)_(\d+)$", benchmark_version)
    label = f"v{match.group(1)}.{match.group(2)}" if match else benchmark_version
    return f"# Reference Calibration {label} Report"


def default_output_prefix(registry: dict) -> Path:
    benchmark_version = str(registry.get("benchmark_version", "unknown"))
    match = re.search(r"_v(\d+)_(\d+)$", benchmark_version)
    suffix = f"V{match.group(1)}_{match.group(2)}" if match else "UNKNOWN"
    return Path(f"artifacts/REFERENCE_CALIBRATION_{suffix}_REPORT")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("artifacts/reference_calibration_v1_1.json"),
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=None,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    report = summarize_calibration(registry)
    output_prefix = args.output_prefix or default_output_prefix(registry)
    json_path = output_prefix.with_suffix(".json")
    markdown_path = output_prefix.with_suffix(".md")
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        report_heading(registry),
        "",
        f"Total probes: `{report['total_probes']}`",
        "",
        f"Calibrated: `{report['calibrated_count']}`",
        "",
        f"Pending: `{report['pending_count']}`",
        "",
        f"Needs review: `{report['needs_review_count']}`",
        "",
        f"Invalid: `{report['invalid_count']}`",
        "",
        "| Probe | Status | Errors |",
        "|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['probe_id']} | {row['status']} | {'; '.join(row['errors']) or '-'} |"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json_path)
    print(markdown_path)
    if report["invalid_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
