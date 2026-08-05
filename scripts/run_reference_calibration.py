"""Run v1.1 strict probes against the reference fixtures and record evidence.

For each fixture this places the fixture source where BaxBench expects a
generated solution and runs the test phase only, so no model endpoint is
contacted. Observed CWEs per probe are written back into the registry.
"""

import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class FixtureRunError(RuntimeError):
    """A fixture could not be run, or a probe produced no usable result.

    Raised instead of exiting so the sweep records the reason against the
    affected probes and keeps every result it has already collected.
    """


SCENARIO_DIR = Path("artifacts/factorial_prompt_scenarios_v1_1")
RUNS_DIR = Path("artifacts/reference_calibration_runs")
SCENARIO_ID_TEMPLATE = "{base_scenario}__natural__v1_1"
MODEL_LABEL = "reference-fixture"
ENV_ID = "Python-FastAPI"


def _relative_layout_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"calibration.{label} must be a nonempty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"calibration.{label} must stay inside the repository")
    return path


def calibration_layout(registry: dict) -> dict[str, object]:
    raw = registry.get("calibration")
    if raw is None:
        return {
            "scenario_dir": SCENARIO_DIR,
            "scenario_id_template": SCENARIO_ID_TEMPLATE,
            "runs_dir": RUNS_DIR,
        }
    if not isinstance(raw, dict):
        raise SystemExit("calibration must be an object")

    scenario_dir = _relative_layout_path(raw.get("scenario_dir"), "scenario_dir")
    runs_dir = _relative_layout_path(raw.get("runs_dir"), "runs_dir")
    template = raw.get("scenario_id_template")
    if not isinstance(template, str) or not template.strip():
        raise SystemExit("calibration.scenario_id_template must be a nonempty string")
    try:
        rendered = template.format(base_scenario="Scenario")
    except (KeyError, ValueError) as error:
        raise SystemExit(
            f"invalid calibration.scenario_id_template: {error}"
        ) from error
    if rendered.count("Scenario") != 1 or Path(rendered).name != rendered:
        raise SystemExit(
            "calibration.scenario_id_template must contain one base_scenario "
            "and produce a plain scenario id"
        )
    return {
        "scenario_dir": scenario_dir,
        "scenario_id_template": template,
        "runs_dir": runs_dir,
    }


def scenario_id(base_scenario: str, layout: dict[str, object]) -> str:
    return str(layout["scenario_id_template"]).format(base_scenario=base_scenario)


def scenario_file(base_scenario: str, layout: dict[str, object] | None = None) -> Path:
    layout = layout or calibration_layout({})
    identifier = scenario_id(base_scenario, layout)
    return Path(layout["scenario_dir"]) / base_scenario / f"{identifier}.py"


def fixtures_of(registry: dict) -> dict[str, dict]:
    """fixture_id -> {path, base_scenario}."""
    fixtures: dict[str, dict] = {}
    for probe in registry["probes"]:
        base_scenario = probe["probe_id"].split("/", 1)[0]
        for key in ("secure_fixture", "vulnerable_fixture"):
            fixture = probe[key]
            existing = fixtures.setdefault(
                fixture["id"],
                {"path": fixture["path"], "base_scenario": base_scenario},
            )
            if existing["path"] != fixture["path"]:
                raise SystemExit(
                    f"fixture id {fixture['id']} maps to two paths: "
                    f"{existing['path']} and {fixture['path']}"
                )
    return fixtures


def run_fixture(
    fixture_id: str,
    fixture: dict,
    timeout: int,
    layout: dict[str, object] | None = None,
    min_port: int | None = None,
) -> dict[str, dict]:
    """Returns test name -> {status, cwes} for one fixture, retrying once.

    Every probe reporting an exception means the environment failed, not the
    fixture -- the base image build hits a transient package-mirror error often
    enough to interrupt an unattended sweep. A real fixture defect never makes
    the whole suite except at once.
    """
    layout = layout or calibration_layout({})
    results = _run_fixture_once(fixture_id, fixture, timeout, layout, min_port)
    if results and all(row.get("status") == "exception" for row in results.values()):
        print(f"CALIBRATION_RETRY {fixture_id} (environment failure)", flush=True)
        results = _run_fixture_once(fixture_id, fixture, timeout, layout, min_port)
    return results


def _run_fixture_once(
    fixture_id: str,
    fixture: dict,
    timeout: int,
    layout: dict[str, object],
    min_port: int | None = None,
) -> dict[str, dict]:
    base_scenario = fixture["base_scenario"]
    selected_scenario_id = scenario_id(base_scenario, layout)
    run_dir = Path(layout["runs_dir"]) / fixture_id
    sample_dir = (
        run_dir
        / "results"
        / MODEL_LABEL
        / selected_scenario_id
        / ENV_ID
        / "temp0.0-openapi-none"
        / "sample0"
    )
    code_dir = sample_dir / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fixture["path"], code_dir / "app.py")
    # run_smoke_eval passes -f, but drop the previous result anyway so a crashed
    # run can never be read back as this run's evidence.
    (sample_dir / "test_results.json").unlink(missing_ok=True)

    command = [
        sys.executable,
        "scripts/run_smoke_eval.py",
        "--scenario-file",
        str(scenario_file(base_scenario, layout)),
        "--run-dir",
        str(run_dir),
        "--model",
        MODEL_LABEL,
        "--phase",
        "test",
        "--timeout",
        str(timeout),
    ]
    # Concurrent fixtures must not contend for the same published ports.
    if min_port is not None:
        command += ["--min-port", str(min_port), "--num-ports", "40"]
    print(f"CALIBRATION_RUN {fixture_id}", flush=True)
    completed = subprocess.run(command, env={**_env()}, check=False)
    if completed.returncode != 0:
        raise FixtureRunError(
            f"{fixture_id}: test phase exited {completed.returncode}"
        )

    results_path = sample_dir / "test_results.json"
    if not results_path.exists():
        raise FixtureRunError(f"{fixture_id}: no test_results.json at {results_path}")
    return json.loads(results_path.read_text(encoding="utf-8"))["full_results"]


def _env() -> dict:
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "src")
    # The images bake this value in (src/env/python.py), but probes sign their
    # tokens host-side. Unset, every probe for a JWT scenario fails its control
    # and the whole scenario records pending instead of evidence.
    env.setdefault("APP_SECRET", "supers3cret")
    return env


def observed_cwes(results: dict, test_name: str, fixture_id: str) -> list[int]:
    result = results.get(test_name)
    if result is None:
        raise FixtureRunError(f"{fixture_id}: probe {test_name} did not run")
    if result.get("status") == "exception":
        raise FixtureRunError(f"{fixture_id}: probe {test_name} raised an exception")
    raw = result.get("cwes", "")
    return sorted({int(part) for part in raw.split(",") if part.strip()})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("artifacts/reference_calibration_v1_1.json"),
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--only", help="calibrate a single base scenario", default=None)
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="fixtures to run concurrently; each gets its own published port range",
    )
    parser.add_argument("--min-port", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    layout = calibration_layout(registry)
    probes = [
        probe
        for probe in registry["probes"]
        if args.only is None or probe["probe_id"].startswith(f"{args.only}/")
    ]
    if not probes:
        raise SystemExit(f"no probes match --only {args.only}")

    wanted = {
        probe[key]["id"]
        for probe in probes
        for key in ("secure_fixture", "vulnerable_fixture")
    }
    fixtures = {
        fixture_id: fixture
        for fixture_id, fixture in fixtures_of(registry).items()
        if fixture_id in wanted
    }
    missing = [f["path"] for f in fixtures.values() if not Path(f["path"]).exists()]
    if missing:
        raise SystemExit(
            "missing fixture sources (run scripts/build_reference_fixtures.py): "
            + ", ".join(missing)
        )

    ordered = sorted(fixtures.items())
    results: dict[str, dict] = {}
    failures: dict[str, str] = {}

    def run_one(index: int, item: tuple[str, dict]) -> tuple[str, object]:
        fixture_id, fixture = item
        port = None if args.min_port is None else args.min_port + index * 40
        try:
            return fixture_id, run_fixture(
                fixture_id, fixture, args.timeout, layout, port
            )
        except FixtureRunError as error:
            return fixture_id, error

    # A fixture that cannot run costs its own probes, not the sweep. An earlier
    # revision raised out of the whole run, so one bad fixture discarded every
    # result already collected and the sweep had to be restarted per scenario.
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for fixture_id, outcome in pool.map(
            lambda pair: run_one(*pair), enumerate(ordered)
        ):
            if isinstance(outcome, FixtureRunError):
                failures[fixture_id] = str(outcome)
                print(f"CALIBRATION_FIXTURE_FAILED {outcome}", flush=True)
            else:
                results[fixture_id] = outcome

    calibrated = 0
    for probe in probes:
        test_name = probe["probe_id"].split("/", 1)[1]
        runs = []
        reason = None
        for key in ("secure_fixture", "vulnerable_fixture"):
            fixture_id = probe[key]["id"]
            if fixture_id in failures:
                reason = failures[fixture_id]
                break
            try:
                runs.append(
                    {
                        "fixture_id": fixture_id,
                        "observed_cwes": observed_cwes(
                            results[fixture_id], test_name, fixture_id
                        ),
                    }
                )
            except FixtureRunError as error:
                reason = str(error)
                break
        if reason is None:
            probe["runs"] = runs
            probe["status"] = "calibrated"
            probe.pop("blocked_reason", None)
            calibrated += 1
        else:
            # Not "calibrated" and not silently dropped: the probe carries the
            # reason it could not be evidenced, so a later sweep can retry it.
            probe["status"] = "pending"
            probe["blocked_reason"] = reason

    args.registry.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    print(f"{args.registry}: {calibrated}/{len(probes)} calibrated")
    if failures:
        print(f"{len(failures)} fixture(s) could not run:", flush=True)
        for fixture_id, reason in sorted(failures.items()):
            print(f"  {fixture_id}: {reason}", flush=True)


if __name__ == "__main__":
    main()
