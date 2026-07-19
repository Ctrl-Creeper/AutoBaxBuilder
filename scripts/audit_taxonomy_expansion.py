#!/usr/bin/env python3
"""Statically audit the v1.2 taxonomy-expansion prompt wrapper matrix."""

import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from scripts.generate_factorial_prompt_scenarios import (
    PROMPT_CATEGORY_INSTRUCTIONS,
    PROMPT_ORDER,
    load_prompt_variants,
    validate_scenario_source,
    wrapper_source,
)
from taxonomy_expansion import discover_expansion_seeds, validate_expansion_seeds


BENCHMARK_VERSION = "taxonomy_expansion_v1_2"
CONTROLLED_VARIABLES = [
    "api_spec",
    "text_spec",
    "functional_tests",
    "security_tests",
    "needs_db",
    "needs_secret",
    "target_cwes",
]
VARIED_VARIABLES = ["scenario_id", "scenario_instructions"]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _resolve_root_or_record(path: Path, label: str, errors: list[str]) -> Path | None:
    try:
        return Path(path).resolve()
    except (OSError, RuntimeError) as error:
        errors.append(f"{label} cannot be resolved safely: {error}")
        return None


def _write_text_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary_file:
        temporary_file.write(text)
        temporary_file.flush()
        os.fsync(temporary_file.fileno())
        temporary_path = Path(temporary_file.name)
    try:
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _python_source(path: Path) -> tuple[str | None, str | None]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None, "is not valid UTF-8"
    except OSError as error:
        return None, f"cannot be read: {error}"
    if not source.strip():
        return None, "is empty"
    valid, error = validate_scenario_source(path)
    return (source, None) if valid else (None, error)


def _wrapper_scenario_id(source: str) -> str | None:
    """Read SCENARIO.id without importing the generated wrapper module."""
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(
            isinstance(target, ast.Name) and target.id == "SCENARIO"
            for target in targets
        ):
            continue
        if not isinstance(node.value, ast.Call):
            return None
        for keyword in node.value.keywords:
            if (
                keyword.arg == "id"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ):
                return keyword.value.value
        return None
    return None


def _manifest_file_path(value: object, manifest_parent: Path) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return None
    return manifest_parent / path


def _checked_file(
    value: object,
    parent: Path,
    manifest_parent: Path,
    label: str,
    errors: list[str],
) -> Path | None:
    path = _manifest_file_path(value, manifest_parent)
    if path is None:
        errors.append(f"{label} must be a nonempty path string")
        return None
    try:
        resolved_path = path.resolve()
    except (OSError, RuntimeError):
        errors.append(f"{label} cannot be resolved safely: {path}")
        return None
    if not _is_within(resolved_path, parent):
        errors.append(f"{label} escapes its required directory: {path}")
        return None
    if not resolved_path.is_file():
        errors.append(f"{label} is missing: {path}")
        return None
    return resolved_path


def _expected_taxonomy(seed: dict, prompt_id: str) -> dict:
    taxonomy = dict(seed["taxonomy"])
    taxonomy["prompt_category"] = prompt_id
    return taxonomy


def _render_markdown(report: dict) -> str:
    seed_report = report["seed_report"]
    lines = [
        "# Taxonomy Expansion v1.2 Audit",
        "",
        f"Status: {'PASS' if not report['errors'] else 'FAIL'}",
        f"Seeds: {seed_report['seed_count']}",
        f"Manifest rows: {report['manifest_row_count']}",
        f"Bases: {report['base_count']}",
        "",
        "## Seed balance",
        "",
    ]
    for level in ("beginner", "complex"):
        lines.append(f"- {level}: {seed_report['level_counts'].get(level, 0)}")
    lines.extend(["", "## Errors", ""])
    if report["errors"]:
        lines.extend(f"- {error}" for error in report["errors"])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def audit_taxonomy_expansion(
    seeds_dir: Path,
    artifacts_dir: Path,
    prompt_variants_dir: Path,
    output_dir: Path,
    manifest_path: Path,
    audit_json_path: Path,
    audit_markdown_path: Path,
    batch: str = "v1_2",
    seeds_only: bool = False,
) -> dict:
    """Audit seeds and, unless requested otherwise, their generated wrappers."""
    root_errors: list[str] = []
    seeds_dir = _resolve_root_or_record(seeds_dir, "seeds directory", root_errors)
    artifacts_dir = _resolve_root_or_record(
        artifacts_dir, "artifacts directory", root_errors
    )
    output_dir = _resolve_root_or_record(output_dir, "output directory", root_errors)
    manifest_path = _resolve_root_or_record(manifest_path, "manifest path", root_errors)
    manifest_parent = manifest_path.parent if manifest_path is not None else None
    audit_json_path = _resolve_root_or_record(
        audit_json_path, "audit JSON path", root_errors
    )
    audit_markdown_path = _resolve_root_or_record(
        audit_markdown_path, "audit Markdown path", root_errors
    )

    if None in (seeds_dir, artifacts_dir, output_dir, manifest_path, manifest_parent):
        seeds = []
        seed_report = {
            "batch": batch,
            "seed_count": 0,
            "level_counts": {},
            "prompt_counts": {},
            "titles": [],
            "cwes": [],
            "errors": [],
        }
    else:
        seeds = discover_expansion_seeds(seeds_dir, batch)
        seed_report = validate_expansion_seeds(seeds, batch)
    errors = root_errors + list(seed_report["errors"])
    report = {
        "batch": batch,
        "benchmark_version": BENCHMARK_VERSION,
        "seeds_only": seeds_only,
        "seed_report": seed_report,
        "manifest_row_count": 0,
        "base_count": 0,
        "prompt_counts": {},
        "errors": [],
    }

    if not seeds_only and not seed_report["errors"] and not root_errors:
        try:
            prompt_variants = load_prompt_variants(Path(prompt_variants_dir).resolve())
        except Exception as error:
            errors.append(f"unable to load prompt variants: {error}")
            prompt_variants = {}
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, list):
                errors.append("manifest root must be a list")
                manifest = []
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            errors.append(f"unable to read manifest {manifest_path}: {error}")
            manifest = []

        seed_by_title = {seed["title"]: (path.resolve(), seed) for path, seed in seeds}
        scenario_ids: list[str] = []
        bases: set[str] = set()
        prompt_counts: Counter[str] = Counter()
        expected_ids = {
            f"{title}__{prompt_id}"
            for title in seed_by_title
            for prompt_id in PROMPT_ORDER
        }

        for index, row in enumerate(manifest):
            prefix = f"manifest row {index}"
            if not isinstance(row, dict):
                errors.append(f"{prefix} must be an object")
                continue
            scenario_id = row.get("scenario_id")
            if not isinstance(scenario_id, str):
                errors.append(f"{prefix} scenario_id must be a string")
                continue
            scenario_ids.append(scenario_id)
            base_title = row.get("base_scenario")
            prompt_id = row.get("prompt_category")
            if isinstance(base_title, str):
                bases.add(base_title)
            if isinstance(prompt_id, str):
                prompt_counts[prompt_id] += 1
            if base_title not in seed_by_title:
                errors.append(f"{prefix} has unknown base_scenario {base_title!r}")
                continue
            if prompt_id not in PROMPT_ORDER:
                errors.append(f"{prefix} has invalid prompt_category {prompt_id!r}")
                continue

            seed_file, seed = seed_by_title[base_title]
            expected_id = f"{base_title}__{prompt_id}"
            if scenario_id != expected_id:
                errors.append(f"{prefix} scenario_id does not match base and prompt")
            if row.get("benchmark_version") != BENCHMARK_VERSION:
                errors.append(f"{prefix} has wrong benchmark_version")
            if row.get("expansion_batch") != batch:
                errors.append(f"{prefix} has wrong expansion_batch")
            if row.get("oracle_contract") != seed["oracle_contract"]:
                errors.append(f"{prefix} oracle_contract differs from current seed")
            if row.get("target_cwes") != seed["target_cwes"]:
                errors.append(f"{prefix} target_cwes differs from current seed")
            if row.get("taxonomy") != _expected_taxonomy(seed, prompt_id):
                errors.append(f"{prefix} taxonomy differs from current seed")
            for key, expected in (
                ("scenario_level", seed["taxonomy"]["scenario_level"]),
                ("domain", seed["taxonomy"]["domain"]),
                ("task_type", seed["taxonomy"]["task_type"]),
                (
                    "prompt_label",
                    prompt_variants.get(prompt_id, {}).get("label", prompt_id),
                ),
                (
                    "prompt_description",
                    prompt_variants.get(prompt_id, {}).get("description", ""),
                ),
                ("controlled_variables", CONTROLLED_VARIABLES),
                ("varied_variables", VARIED_VARIABLES),
            ):
                if row.get(key) != expected:
                    errors.append(
                        f"{prefix} {key} does not match the expected declaration"
                    )

            declared_seed = _checked_file(
                row.get("base_seed_file"),
                seeds_dir,
                manifest_parent,
                f"{prefix} base_seed_file",
                errors,
            )
            if declared_seed is None or declared_seed != seed_file:
                errors.append(f"{prefix} base_seed_file differs from current seed path")

            expected_base = (
                artifacts_dir / base_title / f"{base_title}_iw0.py"
            ).resolve()
            base_file = _checked_file(
                row.get("base_scenario_file"),
                artifacts_dir,
                manifest_parent,
                f"{prefix} base_scenario_file",
                errors,
            )
            if base_file is not None:
                if base_file != expected_base:
                    errors.append(
                        f"{prefix} base_scenario_file does not match its base title"
                    )
                _, source_error = _python_source(base_file)
                if source_error:
                    errors.append(f"{prefix} base_scenario_file {source_error}")
                elif row.get("base_scenario_sha256") != _sha256(base_file):
                    errors.append(f"{prefix} base_scenario_sha256 does not match file")

            expected_wrapper = (output_dir / base_title / f"{expected_id}.py").resolve()
            wrapper_file = _checked_file(
                row.get("variant_scenario_file"),
                output_dir,
                manifest_parent,
                f"{prefix} variant_scenario_file",
                errors,
            )
            if wrapper_file is not None:
                if wrapper_file != expected_wrapper:
                    errors.append(
                        f"{prefix} variant_scenario_file does not match its id"
                    )
                wrapper_text, source_error = _python_source(wrapper_file)
                if source_error:
                    errors.append(f"{prefix} variant_scenario_file {source_error}")
                else:
                    expected_source = wrapper_source(
                        base_title=base_title,
                        base_module_name=f"{base_title}_iw0",
                        base_relative_path=os.path.relpath(
                            expected_base.parent, start=expected_wrapper.parent
                        ).replace(os.sep, "/"),
                        scenario_id=expected_id,
                        scenario_instructions=PROMPT_CATEGORY_INSTRUCTIONS[prompt_id],
                    )
                    if _wrapper_scenario_id(wrapper_text) != expected_id:
                        errors.append(
                            f"{prefix} wrapper SCENARIO id does not match expected id"
                        )
                    elif wrapper_text != expected_source:
                        errors.append(
                            f"{prefix} wrapper source does not import the intended base"
                        )
                    if row.get("wrapper_sha256") != _sha256(wrapper_file):
                        errors.append(f"{prefix} wrapper_sha256 does not match file")

        if len(manifest) != 32:
            errors.append(
                f"manifest must contain exactly 32 rows; found {len(manifest)}"
            )
        if len(set(scenario_ids)) != len(scenario_ids):
            errors.append("manifest scenario_id values must be unique")
        if set(scenario_ids) != expected_ids:
            errors.append(
                "manifest scenario_id values do not form the expected 8 by 4 matrix"
            )
        if len(bases) != 8:
            errors.append(
                f"manifest must contain exactly 8 base scenarios; found {len(bases)}"
            )
        base_levels = Counter(
            seed_by_title[base][1]["taxonomy"]["scenario_level"]
            for base in bases
            if base in seed_by_title
        )
        for level in ("beginner", "complex"):
            if base_levels[level] != 4:
                errors.append(
                    f"manifest must contain 4 {level} base scenarios; found {base_levels[level]}"
                )
        for prompt_id in PROMPT_ORDER:
            if prompt_counts[prompt_id] != 8:
                errors.append(
                    f"manifest must contain 8 {prompt_id} rows; found {prompt_counts[prompt_id]}"
                )
        expected_wrapper_files = {
            (output_dir / title / f"{title}__{prompt_id}.py").resolve()
            for title in seed_by_title
            for prompt_id in PROMPT_ORDER
        }
        try:
            output_entries = list(output_dir.rglob("*"))
            actual_wrapper_files = set(output_dir.rglob("*.py"))
        except OSError as error:
            errors.append(f"unable to enumerate wrapper output: {error}")
            output_entries = []
            actual_wrapper_files = set()
        for path in output_entries:
            if path.is_symlink():
                errors.append(f"wrapper output contains a symlink: {path}")
        resolved_actual_files = set()
        for path in actual_wrapper_files:
            try:
                resolved_path = path.resolve()
            except (OSError, RuntimeError) as error:
                errors.append(
                    f"wrapper output path cannot be resolved safely: {path}: {error}"
                )
                continue
            if path.is_symlink() or not _is_within(resolved_path, output_dir):
                errors.append(f"wrapper output path escapes output directory: {path}")
                continue
            resolved_actual_files.add(resolved_path)
        for path in sorted(expected_wrapper_files - resolved_actual_files):
            errors.append(f"expected wrapper is missing from output: {path}")
        for path in sorted(resolved_actual_files - expected_wrapper_files):
            errors.append(f"unmanifested wrapper exists in output: {path}")
        report.update(
            {
                "manifest_row_count": len(manifest),
                "base_count": len(bases),
                "prompt_counts": dict(sorted(prompt_counts.items())),
            }
        )

    report["errors"] = sorted(set(errors))
    if audit_json_path is not None:
        _write_text_atomically(
            audit_json_path, json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
    if audit_markdown_path is not None:
        _write_text_atomically(audit_markdown_path, _render_markdown(report))
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically audit the v1.2 taxonomy-expansion wrapper matrix."
    )
    parser.add_argument("--seeds-dir", type=Path, default=REPOSITORY_ROOT / "seeds")
    parser.add_argument(
        "--artifacts-dir", type=Path, default=REPOSITORY_ROOT / "artifacts"
    )
    parser.add_argument(
        "--prompt-variants-dir",
        type=Path,
        default=REPOSITORY_ROOT / "prompt_variants",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_ROOT / "artifacts/factorial_prompt_scenarios_expansion_v1_2",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=REPOSITORY_ROOT
        / "artifacts/factorial_prompt_manifest_expansion_v1_2.json",
    )
    parser.add_argument(
        "--audit-json-path",
        type=Path,
        default=REPOSITORY_ROOT / "artifacts/TAXONOMY_EXPANSION_V1_2_AUDIT.json",
    )
    parser.add_argument(
        "--audit-markdown-path",
        type=Path,
        default=REPOSITORY_ROOT / "artifacts/TAXONOMY_EXPANSION_V1_2_AUDIT.md",
    )
    parser.add_argument("--batch", default="v1_2")
    parser.add_argument("--seeds-only", action="store_true")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    report = audit_taxonomy_expansion(
        seeds_dir=args.seeds_dir,
        artifacts_dir=args.artifacts_dir,
        prompt_variants_dir=args.prompt_variants_dir,
        output_dir=args.output_dir,
        manifest_path=args.manifest_path,
        audit_json_path=args.audit_json_path,
        audit_markdown_path=args.audit_markdown_path,
        batch=args.batch,
        seeds_only=args.seeds_only,
    )
    print(f"taxonomy expansion audit: {'PASS' if not report['errors'] else 'FAIL'}")
    print(args.audit_json_path)
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
