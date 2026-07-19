#!/usr/bin/env python3
"""Generate the v1.2 taxonomy-expansion prompt wrapper matrix."""

import argparse
import ast
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
    build_manifest_entry,
    load_prompt_variants,
    wrapper_source,
)
from taxonomy_expansion import discover_expansion_seeds, validate_expansion_seeds


BENCHMARK_VERSION = "taxonomy_expansion_v1_2"


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _has_top_level_scenario_assignment(path: Path) -> tuple[bool, str]:
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False, "is not valid UTF-8"
    except OSError as error:
        return False, f"cannot be read: {error}"
    if not source.strip():
        return False, "is empty"
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return False, f"contains invalid Python: {error.msg}"
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(
                isinstance(target, ast.Name) and target.id == "SCENARIO"
                for target in targets
            ):
                return True, ""
    return False, "does not assign SCENARIO at module scope"


def _write_text_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary_file:
        temporary_file.write(text)
        temporary_path = Path(temporary_file.name)
    try:
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def generate_expansion_wrappers(
    seeds_dir: Path,
    artifacts_dir: Path,
    prompt_variants_dir: Path,
    output_dir: Path,
    manifest_path: Path,
    batch: str = "v1_2",
) -> list[dict]:
    """Generate four prompt wrappers for each complete, valid expansion seed."""
    seeds_dir = Path(seeds_dir).resolve()
    artifacts_dir = Path(artifacts_dir).resolve()
    prompt_variants_dir = Path(prompt_variants_dir).resolve()
    output_dir = Path(output_dir).resolve()
    manifest_path = Path(manifest_path).resolve()

    seeds = discover_expansion_seeds(seeds_dir, batch)
    seed_report = validate_expansion_seeds(seeds, batch)
    if seed_report["errors"]:
        raise ValueError("Invalid expansion seeds: " + "; ".join(seed_report["errors"]))

    prompt_variants = load_prompt_variants(prompt_variants_dir)
    planned_wrappers: list[tuple[Path, str]] = []
    manifest: list[dict] = []

    for seed_file, seed in seeds:
        title = seed["title"]
        base_scenario_file = artifacts_dir / title / f"{title}_iw0.py"
        resolved_base = base_scenario_file.resolve()
        if not _is_within(resolved_base, artifacts_dir):
            raise ValueError(
                f"Base scenario path escapes artifacts directory: {base_scenario_file}"
            )
        if not base_scenario_file.is_file():
            raise ValueError(f"Missing base scenario: {base_scenario_file}")
        valid_base, base_error = _has_top_level_scenario_assignment(base_scenario_file)
        if not valid_base:
            raise ValueError(f"Base scenario {base_scenario_file} {base_error}")

        for prompt_id in PROMPT_ORDER:
            scenario_id = f"{title}__{prompt_id}"
            variant_scenario_file = output_dir / title / f"{scenario_id}.py"
            resolved_wrapper = variant_scenario_file.resolve()
            if not _is_within(resolved_wrapper, output_dir):
                raise ValueError(
                    f"Wrapper path escapes output directory: {variant_scenario_file}"
                )
            source = wrapper_source(
                base_title=title,
                base_module_name=base_scenario_file.stem,
                scenario_id=scenario_id,
                scenario_instructions=PROMPT_CATEGORY_INSTRUCTIONS[prompt_id],
            )
            planned_wrappers.append((variant_scenario_file, source))
            entry = build_manifest_entry(
                seed_file=seed_file.resolve(),
                seed=seed,
                prompt_id=prompt_id,
                prompt_variant=prompt_variants[prompt_id],
                base_scenario_file=base_scenario_file,
                variant_scenario_file=variant_scenario_file,
            )
            entry.update(
                {
                    "benchmark_version": BENCHMARK_VERSION,
                    "expansion_batch": batch,
                    "oracle_contract": seed["oracle_contract"],
                    "base_scenario_sha256": _sha256(base_scenario_file),
                    "wrapper_sha256": hashlib.sha256(
                        source.encode("utf-8")
                    ).hexdigest(),
                }
            )
            manifest.append(entry)

    for wrapper_path, source in planned_wrappers:
        _write_text_atomically(wrapper_path, source)
    _write_text_atomically(
        manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate v1.2 taxonomy-expansion prompt wrappers."
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
    parser.add_argument("--batch", default="v1_2")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    manifest = generate_expansion_wrappers(
        seeds_dir=args.seeds_dir,
        artifacts_dir=args.artifacts_dir,
        prompt_variants_dir=args.prompt_variants_dir,
        output_dir=args.output_dir,
        manifest_path=args.manifest_path,
        batch=args.batch,
    )
    print(f"generated {len(manifest)} taxonomy expansion prompt wrappers")
    print(args.manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
