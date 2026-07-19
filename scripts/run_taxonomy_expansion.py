#!/usr/bin/env python3
"""Run a validated taxonomy expansion batch with resumable per-seed stages."""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable

import fcntl


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from taxonomy_expansion import discover_expansion_seeds, validate_expansion_seeds


STAGE_NAMES = ("scenarios", "tests", "exploits")
STATUS_SCHEMA_VERSION = 1


def commands_for_seed(
    seed_file: Path,
    artifacts_dir: Path,
    difficulty: int,
    python_executable: str,
) -> list[list[str]]:
    """Build the generation commands for a seed in execution order."""
    seed = json.loads(Path(seed_file).read_text(encoding="utf-8"))
    title = seed["title"]
    return [
        [
            python_executable,
            "src/main.py",
            "--generate_scenarios",
            "--seed_file",
            str(seed_file),
            "--path",
            str(artifacts_dir),
            "--difficulty",
            str(difficulty),
        ],
        [
            python_executable,
            "src/main.py",
            "--generate_tests",
            "--scenario",
            title,
            "--path",
            str(artifacts_dir),
        ],
        [
            python_executable,
            "src/main.py",
            "--generate_exploits",
            "--scenario",
            title,
            "--path",
            str(artifacts_dir),
        ],
    ]


def _parallel(value: str) -> int:
    parallel = int(value)
    if not 1 <= parallel <= 8:
        raise argparse.ArgumentTypeError("--parallel must be between 1 and 8")
    return parallel


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a validated, resumable taxonomy expansion batch."
    )
    parser.add_argument("--seeds-dir", type=Path, default=Path("seeds"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--batch", default="v1_2")
    parser.add_argument("--difficulty", type=int, default=3)
    parser.add_argument("--parallel", type=_parallel, default=2)
    parser.add_argument("--python", dest="python_executable", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--status-path",
        type=Path,
        default=Path("artifacts/taxonomy_expansion_v1_2_status.json"),
    )
    return parser.parse_args(argv)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _artifact_directory(title: str, artifacts_dir: Path) -> Path:
    root = artifacts_dir.resolve()
    directory = (root / title).resolve()
    if not _is_within(directory, root):
        raise ValueError("artifact path escapes artifacts directory")
    return directory


def _valid_scenario(path: Path, title: str) -> bool:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("title") == title
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return False


def _valid_python_artifact(path: Path) -> bool:
    try:
        source = path.read_text(encoding="utf-8")
        if not source.strip():
            return False
        tree = ast.parse(source, filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return False
    return any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "SCENARIO"
            for target in node.targets
        )
        for node in tree.body
    )


def _artifact_status(title: str, artifacts_dir: Path) -> list[bool]:
    directory = _artifact_directory(title, artifacts_dir)
    has_scenario = _valid_scenario(directory / f"{title}.json", title)
    has_tests = any(
        _valid_python_artifact(path) for path in directory.glob(f"{title}_iu*.py")
    )
    has_exploits = _valid_python_artifact(directory / f"{title}_iw0.py")
    return [
        has_scenario or has_tests or has_exploits,
        has_tests or has_exploits,
        has_exploits,
    ]


def _stage_record(name: str, status: str, argv: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "argv": argv,
        "exit_code": None,
        "elapsed_seconds": 0.0,
    }


def _failed_seed(title: str, seed_file: Path, commands: list[list[str]] | None = None):
    commands = commands or [[], [], []]
    stages = [
        _stage_record(name, "skipped", argv)
        for name, argv in zip(STAGE_NAMES, commands)
    ]
    stages[0]["status"] = "failed"
    return {"title": title, "path": str(seed_file), "stages": stages}


def run_seed(
    *,
    seed_file: Path,
    title: str,
    artifacts_dir: Path,
    difficulty: int,
    python_executable: str,
    dry_run: bool,
    runner: Callable[..., Any] = subprocess.run,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Run one seed sequentially, preserving later artifacts as completed work."""
    try:
        commands = commands_for_seed(
            seed_file, artifacts_dir, difficulty, python_executable
        )
    except Exception:
        return _failed_seed(title, seed_file)
    stages: list[dict[str, Any]] = []
    stopped = False

    for index, (name, argv) in enumerate(zip(STAGE_NAMES, commands)):
        try:
            completed = _artifact_status(title, artifacts_dir)[index]
        except Exception:
            stages.append(_stage_record(name, "failed", argv))
            stopped = True
            continue
        if stopped or completed:
            stages.append(_stage_record(name, "skipped", argv))
            continue
        if dry_run:
            stages.append(_stage_record(name, "planned", argv))
            continue

        started = monotonic()
        try:
            log_path = (
                _artifact_directory(title, artifacts_dir) / "taxonomy_expansion.log"
            )
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as log_file:
                result = runner(
                    argv,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    check=False,
                    cwd=REPOSITORY_ROOT,
                )
            exit_code = getattr(result, "returncode", 1)
        except Exception:
            exit_code = None
        elapsed = round(monotonic() - started, 6)
        status = "passed" if exit_code == 0 else "failed"
        stages.append(
            {
                "name": name,
                "status": status,
                "argv": argv,
                "exit_code": exit_code,
                "elapsed_seconds": elapsed,
            }
        )
        if status == "failed":
            stopped = True

    return {"title": title, "path": str(seed_file), "stages": stages}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _repository_path(path: Path) -> Path:
    return path if path.is_absolute() else REPOSITORY_ROOT / path


def _aggregate(seeds: list[dict[str, Any]]) -> dict[str, Any]:
    stage_counts = {status: 0 for status in ("planned", "skipped", "passed", "failed")}
    for seed in seeds:
        for stage in seed["stages"]:
            stage_counts[stage["status"]] += 1
    return {
        "seeds": len(seeds),
        "failed_seeds": sum(
            any(stage["status"] == "failed" for stage in seed["stages"])
            for seed in seeds
        ),
        "stages": stage_counts,
    }


def _write_status_atomically(
    status_path: Path, report: dict[str, Any], fsync: Callable[[int], Any] = os.fsync
) -> None:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=status_path.parent,
        prefix=f".{status_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary_file:
        json.dump(report, temporary_file, indent=2, sort_keys=True)
        temporary_file.write("\n")
        temporary_file.flush()
        fsync(temporary_file.fileno())
        temporary_path = Path(temporary_file.name)
    os.replace(temporary_path, status_path)
    directory_fd = os.open(status_path.parent, os.O_RDONLY)
    try:
        fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _acquire_lock(artifacts_dir: Path, batch: str):
    root = artifacts_dir.resolve()
    lock_path = (root / f".taxonomy_expansion_{batch}.lock").resolve()
    if not _is_within(lock_path, root):
        raise ValueError("lock path escapes artifacts directory")
    root.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open("a", encoding="utf-8")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        lock_file.close()
        raise
    return lock_file


def run_batch(
    args: argparse.Namespace,
    *,
    command_runner: Callable[..., Any] = subprocess.run,
    now: Callable[[], str] = _timestamp,
    monotonic: Callable[[], float] = time.monotonic,
) -> int:
    """Validate and run a batch, returning a process-compatible exit status."""
    seeds_dir = _repository_path(args.seeds_dir)
    artifacts_dir = _repository_path(args.artifacts_dir)
    status_path = _repository_path(args.status_path)
    lock_file = None
    try:
        seeds = discover_expansion_seeds(seeds_dir, args.batch)
        validation = validate_expansion_seeds(seeds, args.batch)
        if validation["errors"]:
            for error in validation["errors"]:
                print(error, file=sys.stderr)
            return 2

        ordered_seeds = sorted(seeds, key=lambda item: str(item[0]))
        started_at = now()
        if not args.dry_run:
            try:
                lock_file = _acquire_lock(artifacts_dir, args.batch)
            except BlockingIOError:
                return 3
            except OSError:
                results = [
                    _failed_seed(seed["title"], seed_file)
                    for seed_file, seed in ordered_seeds
                ]
                report = {
                    "schema_version": STATUS_SCHEMA_VERSION,
                    "batch": args.batch,
                    "dry_run": args.dry_run,
                    "started_at": started_at,
                    "finished_at": now(),
                    "seeds": results,
                    "aggregate": _aggregate(results),
                }
                _write_status_atomically(status_path, report)
                return 1
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = [
                executor.submit(
                    run_seed,
                    seed_file=seed_file,
                    title=seed["title"],
                    artifacts_dir=artifacts_dir,
                    difficulty=args.difficulty,
                    python_executable=args.python_executable,
                    dry_run=args.dry_run,
                    runner=command_runner,
                    monotonic=monotonic,
                )
                for seed_file, seed in ordered_seeds
            ]
            results = []
            for future, (seed_file, seed) in zip(futures, ordered_seeds):
                try:
                    results.append(future.result())
                except Exception:
                    results.append(_failed_seed(seed["title"], seed_file))

        if args.dry_run:
            for seed in results:
                for stage in seed["stages"]:
                    if stage["status"] == "planned":
                        print(shlex.join(stage["argv"]))

        report = {
            "schema_version": STATUS_SCHEMA_VERSION,
            "batch": args.batch,
            "dry_run": args.dry_run,
            "started_at": started_at,
            "finished_at": now(),
            "seeds": results,
            "aggregate": _aggregate(results),
        }
        _write_status_atomically(status_path, report)
        return 1 if report["aggregate"]["failed_seeds"] else 0
    finally:
        if lock_file is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()


def main(argv: list[str] | None = None) -> int:
    return run_batch(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
