import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


MIN_GENERATION_TIMEOUT = 600.0

ACTIVE_PROCESSES: set[subprocess.Popen] = set()
ACTIVE_PROCESSES_LOCK = Lock()


def terminate_active_processes() -> None:
    with ACTIVE_PROCESSES_LOCK:
        processes = list(ACTIVE_PROCESSES)
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_manifest(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def filtered_entries(
    manifest: list[dict],
    *,
    base_scenario: str | None,
    prompt_category: str | None,
    limit: int | None,
) -> list[dict]:
    entries = []
    for row in manifest:
        if base_scenario and row["base_scenario"] != base_scenario:
            continue
        if prompt_category and row["prompt_category"] != prompt_category:
            continue
        entries.append(row)
    return entries[:limit] if limit is not None else entries


def run_entry(
    *,
    entry: dict,
    ordinal: int,
    repeat: int | None,
    use_repeat_dirs: bool,
    output_dir: Path,
    model: str,
    n_samples: int,
    phase: str,
    timeout: int,
    max_retries: int,
    base_url_host: str,
    min_port: int,
    num_ports: int,
    force: bool,
    log_dir: Path,
) -> int:
    scenario_id = entry["scenario_id"]
    run_dir = output_dir / scenario_id
    if use_repeat_dirs:
        run_dir = run_dir / f"repeat{repeat}"
    result_path = run_dir / f"{scenario_id}_smoke_results.json"
    if result_path.exists() and not force:
        print(f"FACTORIAL_SKIP {scenario_id} {utc_now()}", flush=True)
        return 0

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{scenario_id}.log"
    cmd = [
        sys.executable,
        "scripts/run_smoke_eval.py",
        "--scenario-file",
        entry["variant_scenario_file"],
        "--run-dir",
        str(run_dir),
        "--model",
        model,
        "--n-samples",
        str(n_samples),
        "--phase",
        phase,
        "--timeout",
        str(timeout),
        "--max-retries",
        str(max_retries),
        "--min-port",
        str(min_port),
        "--num-ports",
        str(num_ports),
        "--base-url-host",
        base_url_host,
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "src")

    print(
        f"FACTORIAL_START {scenario_id} repeat={repeat if repeat is not None else '-'} "
        f"worker_slot={ordinal} "
        f"min_port={min_port} {utc_now()}",
        flush=True,
    )
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        with ACTIVE_PROCESSES_LOCK:
            ACTIVE_PROCESSES.add(process)
        assert process.stdout is not None
        try:
            for line in process.stdout:
                print(line, end="", flush=True)
                log_file.write(line)
            status = process.wait()
        finally:
            with ACTIVE_PROCESSES_LOCK:
                ACTIVE_PROCESSES.discard(process)

    print(f"FACTORIAL_DONE {scenario_id} status={status} {utc_now()}", flush=True)
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run factorial prompt scenario smoke evaluations."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/factorial_prompt_manifest.json"),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("artifacts/eval_runs_factorial")
    )
    parser.add_argument("--model", default=os.environ.get("AUTOBAX_MODEL", "gpt-5.5"))
    parser.add_argument("--n-samples", type=int, default=1)
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Repeat each scenario in isolated run directories.",
    )
    parser.add_argument(
        "--phase", choices=["all", "generate", "test", "evaluate"], default="all"
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--max-retries", type=int, default=0)
    parser.add_argument("--base-url-host", default="ai.bnds.fun")
    parser.add_argument("--base-scenario")
    parser.add_argument("--prompt-category")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--port-base", type=int, default=18000)
    parser.add_argument("--num-ports", type=int, default=80)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def preflight(env_file: Path = Path(".env")) -> None:
    """Fail before the run rather than producing empty results after it.

    Two settings have each cost a full sweep. Without OPENAI_API_KEY the model
    client raises while being constructed, every scenario still exits 0, and each
    one writes a results file whose full_results is {} -- a whole run that looks
    successful and contains nothing. With OPENAI_TIMEOUT left at the client's
    60-second default, most samples time out mid-generation and land the same
    way. Both are read from the environment, and .env holds them but nothing
    loads it, so a shell that did not source it fails silently.
    """
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip().removeprefix("export ").strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            # Anything already exported wins: an explicit override on the
            # command line must not be undone by the file.
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set and was not found in .env. Every sample "
            "would write an empty result and still exit 0."
        )
    # Checked by value, not by presence: .env carries OPENAI_TIMEOUT=60, which is
    # the setting that emptied 18 of 22 samples on an earlier sweep. "It is set"
    # is exactly the reassurance that let it through.
    timeout = os.environ.get("OPENAI_TIMEOUT")
    if not timeout or float(timeout) < MIN_GENERATION_TIMEOUT:
        raise SystemExit(
            f"OPENAI_TIMEOUT is {timeout or 'unset'}; generation needs at least "
            f"{MIN_GENERATION_TIMEOUT:.0f}s. Below that, samples time out "
            f"mid-generation and are written as empty results with exit code 0. "
            f"Export OPENAI_TIMEOUT=1200."
        )
    print(
        f"PREFLIGHT ok base_url={os.environ.get('OPENAI_BASE_URL', 'default')} "
        f"timeout={os.environ['OPENAI_TIMEOUT']}s",
        flush=True,
    )


def main() -> None:
    args = parse_args()
    preflight()
    if args.n_samples > 1:
        # run_smoke_eval fixes temperature at 0, where BaxBench collapses the
        # requested samples to one. Asking for three yields one, and the run
        # looks complete at a third of the intended size.
        raise SystemExit(
            f"--n-samples {args.n_samples} produces a single sample at "
            f"temperature 0. Use --repeats {args.n_samples} instead, which runs "
            f"each scenario in its own directory."
        )
    manifest = load_manifest(args.manifest)
    entries = filtered_entries(
        manifest,
        base_scenario=args.base_scenario,
        prompt_category=args.prompt_category,
        limit=args.limit,
    )
    work_items = [
        (entry, repeat) for entry in entries for repeat in range(args.repeats)
    ]
    use_repeat_dirs = args.repeats > 1

    print(f"FACTORIAL_TOTAL {len(entries)}", flush=True)
    print(f"FACTORIAL_WORK_ITEMS {len(work_items)}", flush=True)
    print(f"FACTORIAL_WORKERS {args.workers}", flush=True)

    log_dir = args.output_dir / "_batch_logs"
    failures = []
    if args.workers <= 1:
        for index, (entry, repeat) in enumerate(work_items):
            status = run_entry(
                entry=entry,
                ordinal=index,
                repeat=repeat,
                use_repeat_dirs=use_repeat_dirs,
                output_dir=args.output_dir,
                model=args.model,
                n_samples=args.n_samples,
                phase=args.phase,
                timeout=args.timeout,
                max_retries=args.max_retries,
                base_url_host=args.base_url_host,
                min_port=args.port_base + index * args.num_ports,
                num_ports=args.num_ports,
                force=args.force,
                log_dir=log_dir,
            )
            if status != 0:
                failures.append(entry["scenario_id"])
    else:
        try:
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = {}
                for index, (entry, repeat) in enumerate(work_items):
                    future = executor.submit(
                        run_entry,
                        entry=entry,
                        ordinal=index,
                        repeat=repeat,
                        use_repeat_dirs=use_repeat_dirs,
                        output_dir=args.output_dir,
                        model=args.model,
                        n_samples=args.n_samples,
                        phase=args.phase,
                        timeout=args.timeout,
                        max_retries=args.max_retries,
                        base_url_host=args.base_url_host,
                        min_port=args.port_base + index * args.num_ports,
                        num_ports=args.num_ports,
                        force=args.force,
                        log_dir=log_dir,
                    )
                    futures[future] = f"{entry['scenario_id']}#repeat{repeat}"
                for future in as_completed(futures):
                    scenario_id = futures[future]
                    try:
                        status = future.result()
                    except Exception as exc:
                        print(f"FACTORIAL_EXCEPTION {scenario_id}: {exc}", flush=True)
                        failures.append(scenario_id)
                        continue
                    if status != 0:
                        failures.append(scenario_id)
        except KeyboardInterrupt:
            print("FACTORIAL_INTERRUPTED terminating active children", flush=True)
            terminate_active_processes()
            raise

    if failures:
        print("FACTORIAL_FAILURES " + ",".join(failures), flush=True)
        raise SystemExit(1)
    print("FACTORIAL_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
