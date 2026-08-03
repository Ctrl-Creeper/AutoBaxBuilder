"""Summarize manually reviewed LLM candidate-audit outcomes."""

import argparse
import json
from pathlib import Path

from llm_audit_triage import summarize_triage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("artifacts/LLM_AUDIT_TRIAGE_SUMMARY"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = json.loads(args.triage.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SystemExit("triage file must be a JSON array")
    report = summarize_triage(records)
    json_path = args.output_prefix.with_suffix(".json")
    md_path = args.output_prefix.with_suffix(".md")
    md_path.write_text(
        "\n".join(
            [
                "# LLM Audit Triage Summary",
                "",
                f"Reviewed candidates: {report['reviewed_count']}",
                "",
                f"Confirmed missing coverage: {report['confirmed_count']}",
                "",
                f"False positives: {report['false_positive_count']}",
                "",
                f"Confirmation rate: {report['confirmation_rate']:.2%}",
                "",
                f"Deterministic tests added: {report['deterministic_tests_added']}",
                "",
                f"Deterministic-test yield: {report['deterministic_test_yield']:.2%}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
