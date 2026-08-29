"""Study 3 — the one authorized case materialization (GAP-3 Amendment 2).

Runs the already-frozen benchmark case extractor (packet_build/build_study1_packets
`extract_cases`, verbatim import — the only file permitted to invoke it after Amendment 2)
EXACTLY ONCE per selected task, in one documented environment, and freezes the complete
case objects — situations, inputs, and expected behaviour b — into the sealed
FROZEN_CASE_MANIFEST. From that freeze onward, no Study-3 component re-executes testcase
extraction: every downstream consumer (baseline builder, packet audit, writer handoff,
S′ builder, VO derivation) reads this manifest and nothing else for case values.

Amendment-2 clauses enforced here mechanically:
  - one authorized run: an existing manifest is never overwritten (immutable; clause 10);
  - b is exactly what the pinned extractor produced — no normalization, sanitization,
    canonicalization, repair, or hand-editing of any value (clause 6);
  - if extraction fails for ANY selected task (exception, timeout, missing dependency,
    unserializable case object), this exits WITHOUT writing a manifest — hard stop, no
    task-level handling rule (clause 11);
  - sensitive/environment-derived raw values live only in the sealed manifest; the public
    audit artifact carries per-case hashes, counts, situations, dependency metadata, and
    the environment record (clause 7);
  - the environment record captures pins, runtime, OS, env variables, locale/timezone,
    cwd construction, and sha256 of mechanically identifiable host resources (absolute-path
    string literals in the testcase source that name existing regular files); the
    materialization timestamp is provenance, never an input to any rerun (clause 5).
"""

from __future__ import annotations

import hashlib
import json
import locale
import os
import platform
import re
import sys
import time
from pathlib import Path

from study3_pins import sha256_file, verify_pin
from build_study1_packets import extract_cases  # frozen extractor; sole authorized call site

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SELECTION = HERE / "selection_study3.json"
SELECTION_SHA = "b194696cdf54b94dfad4e4a213314a6fadb081876e94565708bb4ea64984bab3"
SEALED_DIR = HERE / "sealed_materialization"
MANIFEST = SEALED_DIR / "FROZEN_CASE_MANIFEST.json"
PUBLIC = HERE / "case_materialization_public.json"

RUNNER = REPO / "scripts/secodeplt_task_runner.py"
DATA = Path("/Users/lewiswu/网络安全/SeCodePLT/virtue_code_eval/data/safety/secodeplt/data.json")


def host_resources(rec: dict) -> dict[str, str]:
    """sha256 of mechanically identifiable host files the extraction may read: absolute-path
    string literals in the testcase source that exist as regular files."""
    src = rec["unittest"]["setup"] + "\n" + rec["unittest"]["testcases"]
    out = {}
    for lit in set(re.findall(r"[\"'](/[^\"']+)[\"']", src)):
        p = Path(lit)
        if p.is_file():
            try:
                out[lit] = hashlib.sha256(p.read_bytes()).hexdigest()
            except OSError:
                out[lit] = "unreadable"
    return out


def environment_record() -> dict:
    return {
        "pins": {
            "selection_manifest_sha256": SELECTION_SHA,
            "benchmark_data_json_sha256": sha256_file(DATA),
            "benchmark_data_json_path": str(DATA),
            "task_runner_sha256": sha256_file(RUNNER),
            "extractor": "packet_build.extract_cases (frozen Study-1 machinery, "
                         "subprocess exec of setup+testcases, timeout 60s)",
        },
        "runtime": {"python": sys.version, "executable": sys.executable},
        "os": {"platform": platform.platform(), "machine": platform.machine(),
               "system": platform.system(), "release": platform.release()},
        "working_directory_construction": "fresh tempfile.TemporaryDirectory per task, "
                                          "extraction subprocess cwd inside it",
        "environment_variables": {k: os.environ.get(k, "<unset>")
                                  for k in ("PATH", "PYTHONHASHSEED", "LANG", "LC_ALL",
                                            "TZ", "HOME", "TMPDIR")},
        "locale": locale.setlocale(locale.LC_ALL, None),
        "timezone": time.strftime("%Z%z"),
        "materialized_at_provenance_only": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def materialize(records: dict[int, dict], selection: list[int]):
    """One pass of the frozen extractor over the selection. Values pass through verbatim
    (clause 6). Returns (tasks, public_tasks, failures); the caller writes nothing if
    failures is non-empty (clause 11)."""
    tasks, public_tasks, failures = {}, {}, []
    for idx in sorted(selection):
        rec = records.get(idx)
        if rec is None:
            failures.append({"index": idx, "failure": "record missing from loader"})
            continue
        try:
            cases = extract_cases(rec)
        except Exception as e:  # noqa: BLE001 — any failure is a clause-11 hard stop
            failures.append({"index": idx, "failure": f"{type(e).__name__}: {e}"})
            continue
        if not cases or not all(
                isinstance(c, dict) and set(c) == {"situation", "input", "expected"}
                and all(isinstance(c[k], str) for k in c) for c in cases):
            failures.append({"index": idx, "failure": "incomplete or unserializable "
                                                      "(situation, input, expected) objects"})
            continue
        tasks[str(idx)] = {"cases": cases}
        public_tasks[str(idx)] = {
            "case_count": len(cases),
            "situations": [c["situation"] for c in cases],
            "case_hashes": [{"input_sha256": hashlib.sha256(c["input"].encode()).hexdigest(),
                             "expected_sha256":
                                 hashlib.sha256(c["expected"].encode()).hexdigest()}
                            for c in cases],
            "host_resources_sha256": host_resources(rec),
        }
    return tasks, public_tasks, failures


def main() -> None:
    if "--approved-materialization" not in sys.argv:
        sys.exit("The one authorized materialization is not yet approved. Runs only with "
                 "--approved-materialization.")
    if MANIFEST.exists():
        sys.exit("FROZEN_CASE_MANIFEST already exists; it is immutable and there is no "
                 "rematerialization (Amendment 2, clauses 10-11). HARD STOP.")

    verify_pin(SELECTION, SELECTION_SHA, "selection manifest")
    selection = json.loads(SELECTION.read_text())["selection"]

    sys.path.insert(0, str(REPO / "scripts"))
    from secodeplt_task_runner import load
    records = {r["index"]: r for r in load(only_stdlib=False)}

    env = environment_record()
    tasks, public_tasks, failures = materialize(records, selection)

    if failures:
        for f in failures:
            print(f"  MATERIALIZATION FAILURE index {f['index']}: {f['failure']}")
        sys.exit(f"HARD STOP — {len(failures)} selected task(s) failed the authorized "
                 "materialization. No manifest is written; no task-level handling rule is "
                 "invented here (Amendment 2, clause 11). Report and await adjudication.")

    SEALED_DIR.mkdir(exist_ok=True)
    manifest = {"amendment": "GAP-3 Amendment 2 — frozen case materialization",
                "environment": env, "n_tasks": len(tasks), "tasks": tasks}
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    msha = sha256_file(MANIFEST)
    public = {"amendment": "GAP-3 Amendment 2 — frozen case materialization",
              "sealed_manifest_sha256": msha,
              "environment": env, "n_tasks": len(public_tasks), "tasks": public_tasks,
              "note": "raw case values live only in the sealed manifest; this artifact "
                      "carries hashes and dependency metadata (clause 7)"}
    PUBLIC.write_text(json.dumps(public, indent=1, ensure_ascii=False) + "\n")

    n_cases = sum(t["case_count"] for t in public_tasks.values())
    print(f"materialized {len(tasks)} tasks, {n_cases} cases — one authorized run complete")
    print(f"sealed FROZEN_CASE_MANIFEST sha256 {msha} — freeze this hash; the manifest is "
          "now immutable (later mismatch = hard stop, never rematerialization)")
    print(f"public artifact sha256 {sha256_file(PUBLIC)}")


if __name__ == "__main__":
    main()
