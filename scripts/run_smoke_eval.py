import argparse
import importlib.util
import json
import pathlib
import socket
import sys
from datetime import datetime, timezone

from baxbench_wrapper import baxbench_parse_args, main as run_baxbench


def free_port_start(min_port: int = 18000, max_port: int = 46000, width: int = 80):
    for start in range(min_port, max_port, width + 7):
        ok = True
        for port in range(start, start + width):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.bind(("0.0.0.0", port))
                except OSError:
                    ok = False
                    break
        if ok:
            return start
    return 23000


def load_scenario(scenario_file: pathlib.Path):
    scenario_file = scenario_file.resolve()
    module_dir = str(scenario_file.parent)
    if module_dir in sys.path:
        sys.path.remove(module_dir)
    sys.path.insert(0, module_dir)

    module_name = scenario_file.stem
    spec = importlib.util.spec_from_file_location(module_name, scenario_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load scenario file: {scenario_file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.SCENARIO


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-file", required=True, type=pathlib.Path)
    parser.add_argument("--run-dir", required=True, type=pathlib.Path)
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--env", default="Python-FastAPI")
    parser.add_argument("--n-samples", type=int, default=1)
    parser.add_argument(
        "--temperature",
        default="0",
        help=(
            "Sampling temperature passed to BaxBench. At 0 the backend returns "
            "one distinct completion however many samples are asked for, so "
            "repeats are near-identical; above 0 they are independent."
        ),
    )
    parser.add_argument(
        "--phase", choices=["all", "generate", "test", "evaluate"], default="all"
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--min-port", type=int)
    parser.add_argument("--num-ports", type=int, default=80)
    parser.add_argument("--base-url-host", default="unknown")
    return parser.parse_args()


def main():
    args = parse_args()
    scenario = load_scenario(args.scenario_file)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    results_dir = args.run_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    common = [
        "--models",
        args.model,
        "--temperature",
        str(args.temperature),
        "--n_samples",
        str(args.n_samples),
        "--envs",
        args.env,
        "--results_dir",
        str(results_dir),
        "--max_concurrent_runs",
        "1",
    ]

    print("SMOKE_RUN_DIR", args.run_dir.resolve())
    print("RESULTS_DIR", results_dir.resolve())
    print("SCENARIO_ID", scenario.id)
    print("MODEL", args.model)

    if args.phase in {"all", "generate"}:
        print("PHASE generate")
        generate_args = baxbench_parse_args(
            common
            + [
                "--mode",
                "generate",
                "--max_retries",
                str(args.max_retries),
                "--base_delay",
                "1",
                "--max_delay",
                "5",
                "-f",
            ]
        )
        tasks = run_baxbench(generate_args, [scenario])
        print("GENERATED_TASKS", [task.id for task in tasks])

    if args.phase in {"all", "test"}:
        min_port = str(args.min_port or free_port_start(width=args.num_ports))
        print("PHASE test")
        print("MIN_PORT", min_port)
        test_args = baxbench_parse_args(
            common
            + [
                "--mode",
                "test",
                "--timeout",
                str(args.timeout),
                "--min_port",
                min_port,
                "--num_ports",
                str(args.num_ports),
                "-f",
            ]
        )
        run_baxbench(test_args, [scenario])

    if args.phase in {"all", "evaluate"}:
        print("PHASE evaluate")
        eval_args = baxbench_parse_args(common + ["--mode", "evaluate"])
        full_results = run_baxbench(eval_args, [scenario])
        out = {
            "generated_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "scenario": scenario.id,
            "model": args.model,
            "base_url_host": args.base_url_host,
            "results_dir": str(results_dir.resolve()),
            "full_results": full_results,
        }
        out_path = args.run_dir / f"{scenario.id}_smoke_results.json"
        out_path.write_text(json.dumps(out, indent=2) + "\n")
        print("WROTE", out_path.resolve())


if __name__ == "__main__":
    main()
