"""Audit deterministic passing factorial samples for candidate missing coverage.

This command is deliberately post-processing only. It never starts a container,
rewrites a test result, or changes a deterministic pass/fail classification.
"""

import argparse
import json
import os
from pathlib import Path

from llm_audit import (
    audit_provenance,
    build_audit_report,
    build_review_packet,
    call_openai_auditor,
    select_audit_samples,
    require_code_upload_confirmation,
    write_audit_report,
)
from summarize_factorial_eval import summarize


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use an LLM to flag candidate missing coverage in passed samples."
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/factorial_prompt_manifest.json"),
    )
    parser.add_argument("--model", default=os.environ.get("AUTOBAX_MODEL", "gpt-5.5"))
    parser.add_argument(
        "--auditor-model",
        default=os.environ.get(
            "AUTOBAX_AUDIT_MODEL", os.environ.get("AUTOBAX_MODEL", "gpt-5.5")
        ),
    )
    parser.add_argument(
        "--include-beginner",
        action="store_true",
        help="Audit beginner samples too; complex samples are selected by default.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-code-chars", type=int, default=30_000)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write bounded review packets without calling an external model.",
    )
    parser.add_argument(
        "--allow-code-upload",
        action="store_true",
        help="Required for live audit because redacted generated source is sent externally.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/llm_audit"),
    )
    return parser.parse_args()


def write_markdown(output_dir: Path, report: dict) -> Path:
    path = output_dir / "llm_audit_report.md"
    lines = [
        "# LLM Candidate Audit",
        "",
        f"Generation model: `{report['generation_model']}`",
        "",
        f"Auditor model: `{report['auditor_model']}`",
        "",
        f"Dry run: `{report['dry_run']}`",
        "",
        f"Selected samples: `{report['selection_count']}`",
        "",
        f"Candidate groups: `{report['candidate_count']}`",
        "",
        f"Audit errors: `{report['audit_error_count']}`",
        "",
        "The entries below are candidate review items only. They do not change "
        "deterministic benchmark status.",
        "",
        "| Scenario | Sample | Deterministic status | Audit status | Candidate CWEs |",
        "|---|---:|---|---|---|",
    ]
    for review in report["reviews"]:
        audit = review.get("audit", {})
        cwes = ", ".join(f"CWE-{cwe}" for cwe in audit.get("candidate_cwes", []))
        lines.append(
            f"| {review['scenario_id']} | {review['sample_index']} | "
            f"{review['deterministic_status']} | {review['audit_status']} | {cwes or '-'} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    if args.max_code_chars <= 0:
        raise SystemExit("--max-code-chars must be positive")
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be positive")
    try:
        require_code_upload_confirmation(
            dry_run=args.dry_run,
            allow_code_upload=args.allow_code_upload,
        )
    except PermissionError as exc:
        raise SystemExit(str(exc)) from exc

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    manifest_by_id = {entry["scenario_id"]: entry for entry in manifest}
    summary = summarize(args.manifest, args.run_dir, args.model)
    samples = select_audit_samples(
        summary,
        manifest_by_id,
        complex_only=not args.include_beginner,
        limit=args.limit,
    )

    packets = []
    reviews = []
    for sample in samples:
        review = {
            key: sample[key]
            for key in (
                "scenario_id",
                "base_scenario",
                "scenario_level",
                "prompt_category",
                "sample_index",
                "repeat",
                "deterministic_status",
                "test_results",
            )
        }
        try:
            packet = build_review_packet(sample, max_code_chars=args.max_code_chars)
            packets.append(packet)
            review["provenance"] = audit_provenance(
                packet=packet,
                auditor_model=args.auditor_model,
                base_url=os.environ.get("OPENAI_BASE_URL"),
            )
            review["redaction_count"] = packet["redaction_count"]
            if args.dry_run:
                review["audit_status"] = "dry_run"
            else:
                audit, raw_response = call_openai_auditor(
                    model=args.auditor_model,
                    packet=packet,
                    timeout=args.timeout,
                    allow_code_upload=args.allow_code_upload,
                )
                review["audit_status"] = "completed"
                review["audit"] = audit
                review["raw_auditor_response"] = raw_response
        except Exception as exc:
            review["audit_status"] = "audit_error"
            review["audit_error"] = str(exc)
        reviews.append(review)

    report = build_audit_report(
        generation_model=args.model,
        auditor_model=args.auditor_model,
        reviews=reviews,
    )
    report.update(
        {
            "dry_run": args.dry_run,
            "selection_count": len(samples),
            "audit_error_count": sum(
                review["audit_status"] == "audit_error" for review in reviews
            ),
            "manifest": str(args.manifest),
            "run_dir": str(args.run_dir),
        }
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    packet_path = args.output_dir / "llm_audit_packets.json"
    packet_path.write_text(
        json.dumps(packets, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    json_path = write_audit_report(args.output_dir, report)
    markdown_path = write_markdown(args.output_dir, report)
    print(packet_path)
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()
