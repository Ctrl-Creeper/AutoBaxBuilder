#!/usr/bin/env python3
"""Generate the v1.2 taxonomy-expansion prompt wrapper matrix transactionally."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from scripts.generate_factorial_prompt_scenarios import (
    PROMPT_CATEGORY_INSTRUCTIONS,
    PROMPT_ORDER,
    PROTECTED_MANIFEST_NAMES,
    PROTECTED_OUTPUT_NAMES,
    build_manifest_entry,
    load_prompt_variants,
    validate_scenario_source,
    wrapper_source,
)
from taxonomy_expansion import discover_expansion_seeds, validate_expansion_seeds


BENCHMARK_VERSION = "taxonomy_expansion_v1_2"


def _resolve(path: Path, label: str) -> Path:
    try:
        return path.resolve()
    except (OSError, RuntimeError) as error:
        raise ValueError(f"{label} cannot be resolved safely: {error}") from error


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_path(path: Path, start: Path) -> str:
    return os.path.relpath(path, start=start).replace(os.sep, "/")


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


def _assert_safe_existing_output(output_dir: Path) -> Path:
    if output_dir.is_symlink():
        raise ValueError(f"Output directory must not be a symlink: {output_dir}")
    root = _resolve(output_dir, "output directory")
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f"Output path is not a directory: {output_dir}")
    if output_dir.exists():
        try:
            children = list(output_dir.rglob("*"))
        except OSError as error:
            raise ValueError(f"Cannot inspect output directory: {error}") from error
        for child in children:
            if child.is_symlink():
                raise ValueError(f"Output directory contains a symlink: {child}")
    return root


def _safe_stage_path(output_dir: Path) -> Path:
    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = parent / f".{output_dir.name}.staging-{uuid.uuid4().hex}"
    if not _is_within(
        _resolve(stage, "staging directory"), _resolve(parent, "output parent")
    ):
        raise ValueError("Staging directory escapes output parent")
    return stage


def _render_manifest_path(path: Path, manifest_parent: Path) -> str:
    return _relative_path(path, manifest_parent)


def _validate_output_topology(
    output_root: Path,
    artifacts_dir: Path,
    seeds_dir: Path,
    prompt_variants_dir: Path,
    manifest_path: Path,
    base_directories: list[Path],
) -> None:
    for root in (seeds_dir, prompt_variants_dir):
        if (
            output_root == root
            or _is_within(output_root, root)
            or _is_within(root, output_root)
        ):
            raise ValueError(f"Output directory overlaps protected input root: {root}")
    for root in (artifacts_dir, manifest_path.parent):
        if output_root == root or _is_within(root, output_root):
            raise ValueError(
                f"Output directory contains a protected input root: {root}"
            )
    if _is_within(manifest_path, output_root):
        raise ValueError("Output directory must not contain the manifest path")
    for base_directory in base_directories:
        if (
            output_root == base_directory
            or _is_within(base_directory, output_root)
            or _is_within(output_root, base_directory)
        ):
            raise ValueError(
                f"Output directory overlaps base scenario directory: {base_directory}"
            )


def _replace_output_and_manifest(
    *, output_dir: Path, stage_dir: Path, manifest_path: Path, manifest_text: str
) -> None:
    backup_dir = output_dir.parent / f".{output_dir.name}.backup-{uuid.uuid4().hex}"
    old_output = output_dir.exists()
    swapped = False
    try:
        if old_output:
            os.replace(output_dir, backup_dir)
        os.replace(stage_dir, output_dir)
        swapped = True
        _write_text_atomically(manifest_path, manifest_text)
    except Exception:
        if swapped and output_dir.exists():
            failed_dir = (
                output_dir.parent / f".{output_dir.name}.failed-{uuid.uuid4().hex}"
            )
            os.replace(output_dir, failed_dir)
            shutil.rmtree(failed_dir, ignore_errors=True)
        if old_output and backup_dir.exists():
            os.replace(backup_dir, output_dir)
        raise
    else:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)


def generate_expansion_wrappers(
    seeds_dir: Path,
    artifacts_dir: Path,
    prompt_variants_dir: Path,
    output_dir: Path,
    manifest_path: Path,
    batch: str = "v1_2",
) -> list[dict]:
    """Generate four wrappers per seed using a rollback-safe directory swap."""
    seeds_dir = _resolve(Path(seeds_dir), "seeds directory")
    artifacts_dir = _resolve(Path(artifacts_dir), "artifacts directory")
    prompt_variants_dir = _resolve(
        Path(prompt_variants_dir), "prompt variants directory"
    )
    output_dir = Path(output_dir)
    output_root = _assert_safe_existing_output(output_dir)
    manifest_path = _resolve(Path(manifest_path), "manifest path")
    if (
        output_root.name in PROTECTED_OUTPUT_NAMES
        or manifest_path.name in PROTECTED_MANIFEST_NAMES
    ):
        raise ValueError("Refusing protected v1/v1.1 factorial output or manifest path")
    manifest_parent = manifest_path.parent

    seeds = discover_expansion_seeds(seeds_dir, batch)
    seed_report = validate_expansion_seeds(seeds, batch)
    if seed_report["errors"]:
        raise ValueError("Invalid expansion seeds: " + "; ".join(seed_report["errors"]))
    prompt_variants = load_prompt_variants(prompt_variants_dir)
    _validate_output_topology(
        output_root,
        artifacts_dir,
        seeds_dir,
        prompt_variants_dir,
        manifest_path,
        [artifacts_dir / seed["title"] for _, seed in seeds],
    )

    planned: list[tuple[Path, str]] = []
    manifest: list[dict] = []
    for seed_file, seed in seeds:
        title = seed["title"]
        base_scenario_file = artifacts_dir / title / f"{title}_iw0.py"
        resolved_base = _resolve(base_scenario_file, "base scenario")
        if not _is_within(resolved_base, artifacts_dir):
            raise ValueError(
                f"Base scenario path escapes artifacts directory: {base_scenario_file}"
            )
        if not resolved_base.is_file():
            raise ValueError(f"Missing base scenario: {base_scenario_file}")
        valid_base, base_error = validate_scenario_source(resolved_base)
        if not valid_base:
            raise ValueError(f"Base scenario {base_scenario_file} {base_error}")

        for prompt_id in PROMPT_ORDER:
            scenario_id = f"{title}__{prompt_id}"
            final_wrapper = output_root / title / f"{scenario_id}.py"
            if final_wrapper.parent.is_symlink():
                raise ValueError(
                    f"Wrapper output parent is a symlink: {final_wrapper.parent}"
                )
            resolved_wrapper = _resolve(final_wrapper, "wrapper output path")
            if not _is_within(resolved_wrapper, output_root):
                raise ValueError(
                    f"Wrapper output path escapes output directory: {final_wrapper}"
                )
            relative_base = _relative_path(resolved_base.parent, final_wrapper.parent)
            source = wrapper_source(
                base_title=title,
                base_module_name=resolved_base.stem,
                base_relative_path=relative_base,
                scenario_id=scenario_id,
                scenario_instructions=PROMPT_CATEGORY_INSTRUCTIONS[prompt_id],
            )
            planned.append((final_wrapper, source))
            entry = build_manifest_entry(
                seed_file=_resolve(seed_file, "seed file"),
                seed=seed,
                prompt_id=prompt_id,
                prompt_variant=prompt_variants[prompt_id],
                base_scenario_file=resolved_base,
                variant_scenario_file=final_wrapper,
            )
            for key, path in (
                ("base_seed_file", _resolve(seed_file, "seed file")),
                ("base_scenario_file", resolved_base),
                ("variant_scenario_file", final_wrapper),
            ):
                entry[key] = _render_manifest_path(path, manifest_parent)
            entry.update(
                {
                    "benchmark_version": BENCHMARK_VERSION,
                    "expansion_batch": batch,
                    "oracle_contract": seed["oracle_contract"],
                    "base_scenario_sha256": _sha256(resolved_base),
                    "wrapper_sha256": hashlib.sha256(
                        source.encode("utf-8")
                    ).hexdigest(),
                }
            )
            manifest.append(entry)

    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    stage_dir = _safe_stage_path(output_root)
    try:
        for final_wrapper, source in planned:
            stage_wrapper = stage_dir / final_wrapper.relative_to(output_root)
            _write_text_atomically(stage_wrapper, source)
        _replace_output_and_manifest(
            output_dir=output_root,
            stage_dir=stage_dir,
            manifest_path=manifest_path,
            manifest_text=manifest_text,
        )
    except Exception:
        shutil.rmtree(stage_dir, ignore_errors=True)
        raise
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
        "--prompt-variants-dir", type=Path, default=REPOSITORY_ROOT / "prompt_variants"
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
