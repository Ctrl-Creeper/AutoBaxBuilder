import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


PROMPT_ORDER = ["natural", "weak_security", "expert", "threat_modeling"]


def sample_status(sample: dict | None) -> tuple[str, list[int], str, int]:
    if sample is None:
        return "invalid", [], "0/0", 0

    ft_passed = sample.get("num_passed_ft", 0) or 0
    ft_total = sample.get("num_total_ft", 0) or 0
    ft_ex = sample.get("num_ft_exceptions", 0) or 0
    st_total = sample.get("num_total_st", 0) or 0
    st_ex = sample.get("num_st_exceptions", 0) or 0
    cwes = sorted(
        {
            int(cwe["num"])
            for cwe in sample.get("cwes", [])
            if isinstance(cwe, dict) and "num" in cwe
        }
    )

    if ft_total == 0 and st_total == 0:
        status = "invalid"
    elif ft_ex or st_ex:
        status = "exception"
    elif ft_passed != ft_total:
        status = "functional_failed"
    elif cwes:
        status = "security_failed"
    else:
        status = "passed"

    return status, cwes, f"{ft_passed}/{ft_total}", st_total


def sample_root_for(run_dir: Path, scenario_id: str, model: str) -> Path:
    return (
        run_dir
        / "results"
        / model
        / scenario_id
        / "Python-FastAPI"
        / "temp0.0-openapi-none"
    )


def load_samples_from_run_dir(
    entry_run_dir: Path,
    scenario_id: str,
    model: str,
    *,
    sample_offset: int,
    has_smoke_result: bool,
) -> list[dict]:
    sample_root = sample_root_for(entry_run_dir, scenario_id, model)
    samples = []
    for sample_dir in sorted(sample_root.glob("sample*")):
        sample_index_text = sample_dir.name.removeprefix("sample")
        sample_index = int(sample_index_text) if sample_index_text.isdigit() else -1
        test_results_path = sample_dir / "test_results.json"
        sample_data = (
            json.loads(test_results_path.read_text(encoding="utf-8"))
            if test_results_path.exists()
            else None
        )
        status, cwes, functional, security_total = sample_status(sample_data)
        samples.append(
            {
                "sample_index": sample_index,
                "status": status,
                "cwes": cwes,
                "functional": functional,
                "security_total": security_total,
                "test_results": str(test_results_path),
            }
        )
    if not samples and has_smoke_result:
        samples.append(
            {
                "sample_index": sample_offset,
                "status": "invalid",
                "cwes": [],
                "functional": "0/0",
                "security_total": 0,
                "test_results": str(sample_root / "sample0" / "test_results.json"),
            }
        )
    return samples


def load_sample_results(
    run_dir: Path, scenario_id: str, model: str, *, has_smoke_result: bool
) -> list[dict]:
    scenario_run_dir = run_dir / scenario_id
    repeat_dirs = sorted(scenario_run_dir.glob("repeat*"))
    if repeat_dirs:
        samples = []
        for repeat_dir in repeat_dirs:
            repeat_text = repeat_dir.name.removeprefix("repeat")
            repeat_index = int(repeat_text) if repeat_text.isdigit() else len(samples)
            repeat_smoke_result = repeat_dir / f"{scenario_id}_smoke_results.json"
            repeat_samples = load_samples_from_run_dir(
                repeat_dir,
                scenario_id,
                model,
                sample_offset=repeat_index,
                has_smoke_result=repeat_smoke_result.exists(),
            )
            for sample in repeat_samples:
                sample["repeat"] = repeat_index
                sample["sample_index"] = repeat_index
            samples.extend(repeat_samples)
        return samples

    return load_samples_from_run_dir(
        scenario_run_dir,
        scenario_id,
        model,
        sample_offset=0,
        has_smoke_result=has_smoke_result,
    )


def summarize(manifest_path: Path, run_dir: Path, model: str) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = []

    for entry in manifest:
        scenario_id = entry["scenario_id"]
        smoke_result_path = run_dir / scenario_id / f"{scenario_id}_smoke_results.json"
        samples = load_sample_results(
            run_dir,
            scenario_id,
            model,
            has_smoke_result=smoke_result_path.exists(),
        )
        status_counts = Counter(sample["status"] for sample in samples)
        cwes = sorted({cwe for sample in samples for cwe in sample["cwes"]})
        rows.append(
            {
                "scenario_id": scenario_id,
                "base_scenario": entry["base_scenario"],
                "prompt_category": entry["prompt_category"],
                "scenario_level": entry.get("scenario_level"),
                "domain": entry.get("domain"),
                "task_type": entry.get("task_type"),
                "num_samples": len(samples),
                "status_counts": dict(status_counts),
                "pass_rate": (
                    status_counts.get("passed", 0) / len(samples) if samples else 0.0
                ),
                "security_failure_rate": (
                    status_counts.get("security_failed", 0) / len(samples)
                    if samples
                    else 0.0
                ),
                "invalid_or_exception_rate": (
                    (
                        status_counts.get("invalid", 0)
                        + status_counts.get("exception", 0)
                    )
                    / len(samples)
                    if samples
                    else 1.0
                ),
                "cwes": cwes,
                "samples": samples,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "model": model,
        "run_dir": str(run_dir),
        "num_entries": len(rows),
        "total_samples": sum(row["num_samples"] for row in rows),
        "overall_status_counts": dict(
            Counter(
                sample["status"] for row in rows for sample in row.get("samples", [])
            )
        ),
        "prompt_status_counts": {
            prompt: dict(
                Counter(
                    sample["status"]
                    for row in rows
                    if row["prompt_category"] == prompt
                    for sample in row.get("samples", [])
                )
            )
            for prompt in PROMPT_ORDER
        },
        "rows": rows,
    }


def write_markdown(summary: dict, output_path: Path) -> None:
    lines = [
        "# Factorial prompt evaluation summary",
        "",
        f"Generated at: `{summary['generated_at']}`",
        "",
        f"Model: `{summary['model']}`",
        "",
        f"Run dir: `{summary['run_dir']}`",
        "",
        f"Entries: `{summary['num_entries']}`; samples: `{summary['total_samples']}`",
        "",
        f"Overall status counts: `{summary['overall_status_counts']}`",
        "",
        "## Prompt Category Counts",
        "",
        "| Prompt | passed | security_failed | exception | invalid | functional_failed |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for prompt in PROMPT_ORDER:
        counts = summary["prompt_status_counts"].get(prompt, {})
        lines.append(
            f"| {prompt} | {counts.get('passed', 0)} | "
            f"{counts.get('security_failed', 0)} | "
            f"{counts.get('exception', 0)} | {counts.get('invalid', 0)} | "
            f"{counts.get('functional_failed', 0)} |"
        )

    lines.extend(
        [
            "",
            "## Matrix",
            "",
            "| Base task | Level | Prompt | Samples | Pass rate | Security fail rate | Invalid/exception rate | CWEs | Status counts |",
            "|---|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    prompt_rank = {prompt: index for index, prompt in enumerate(PROMPT_ORDER)}
    rows = sorted(
        summary["rows"],
        key=lambda row: (row["base_scenario"], prompt_rank[row["prompt_category"]]),
    )
    for row in rows:
        cwes = ", ".join(f"CWE-{cwe}" for cwe in row["cwes"]) or "-"
        lines.append(
            f"| {row['base_scenario']} | {row.get('scenario_level') or '-'} | "
            f"{row['prompt_category']} | {row['num_samples']} | "
            f"{row['pass_rate']:.2f} | {row['security_failure_rate']:.2f} | "
            f"{row['invalid_or_exception_rate']:.2f} | {cwes} | "
            f"`{row['status_counts']}` |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/factorial_prompt_manifest.json"),
    )
    parser.add_argument(
        "--run-dir", type=Path, default=Path("artifacts/eval_runs_factorial")
    )
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--output-prefix", default="FACTORIAL_SUMMARY")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = summarize(args.manifest, args.run_dir, args.model)
    json_path = args.run_dir / f"{args.output_prefix}.json"
    md_path = args.run_dir / f"{args.output_prefix}.md"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_markdown(summary, md_path)
    print(json_path)
    print(md_path)
    print("entries", summary["num_entries"])
    print("samples", summary["total_samples"])
    print("overall", summary["overall_status_counts"])


if __name__ == "__main__":
    main()
