"""GAP-7 fixtures for the sole authoritative Writer Run-2 accepted input.

The interface fixtures use temporary directories and never print candidate content. Formal
artifacts are read only for hashes, task-id membership, and the accepted task count. Packet
and scorer behavior fixtures are synthetic.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import tempfile
from pathlib import Path

import numpy as np

import run2_writer_input
from packet_build import build_packages
from score_study3 import classify, cp_interval, map_ds_to_baseline, score
from study3_pins import PROTOCOL_SHA, SCHEMA_SPRIME, SEED_SLICES

HERE = Path(__file__).resolve().parent
EXPECTED_ACCEPTED_SHA = "f2b0e73ab1d8b5efcb22bb53c2b8d026446994992195d9b55b483d8de593b49e"
EXPECTED_CASE_MANIFEST_SHA = "2422431ac301aa4e439fe4ff2bdc7e23d6dfd2ffdf836cd8bdbda3ed25df2a36"

PASS = FAIL = 0


def check(name: str, ok: bool) -> None:
    global PASS, FAIL
    print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    PASS, FAIL = PASS + ok, FAIL + (not ok)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(raw)


def manifest_line(digest: str = EXPECTED_ACCEPTED_SHA) -> str:
    return f"{digest}  submissions/writer_output_ACCEPT_FIRST_RUN2.json\n"


def expect_hard_stop(writer_dir: Path) -> bool:
    original = run2_writer_input.WRITER_DIR
    run2_writer_input.WRITER_DIR = writer_dir
    try:
        run2_writer_input.load_authoritative_writer()
    except SystemExit as exc:
        return "HARD STOP" in str(exc)
    finally:
        run2_writer_input.WRITER_DIR = original
    return False


def synthetic_record(idx: int) -> dict:
    return {
        "index": idx,
        "task_description": {
            "function_name": f"combine_{idx}",
            "description": "Combine x and y.",
            "context": "Used by a deterministic fixture.",
            "arguments": "x and y are integers.",
            "return": "The integer sum.",
            "raise": "ValueError for negative inputs.",
        },
        "unittest": {
            "setup": f"LIMIT = {idx * 10}",
            "testcases": "testcases = {'capability': [], 'safety': []}",
        },
        "ground_truth": {"code_before": f"def combine_{idx}(x, y):"},
    }


def main() -> None:
    formal_writer_dir = HERE / "writer_handoff"
    accepted = formal_writer_dir / "submissions/writer_output_ACCEPT_FIRST_RUN2.json"

    with tempfile.TemporaryDirectory(prefix="gap7_old_path_") as td:
        root = Path(td)
        (root / "study3_writer_ACCEPTED.json").write_bytes(accepted.read_bytes())
        (root / "SHA256SUMS_WRITER_FROZEN").write_text(
            f"{EXPECTED_ACCEPTED_SHA}  study3_writer_ACCEPTED.json\n")
        check("old Run-1 accepted path is never accepted", expect_hard_stop(root))

    with tempfile.TemporaryDirectory(prefix="gap7_missing_") as td:
        root = Path(td)
        (root / "SHA256SUMS_WRITER_FROZEN_RUN2").write_text(manifest_line())
        check("missing Run-2 accepted artifact is a hard stop", expect_hard_stop(root))

    with tempfile.TemporaryDirectory(prefix="gap7_mismatch_") as td:
        root = Path(td)
        (root / "submissions").mkdir()
        (root / "submissions/writer_output_ACCEPT_FIRST_RUN2.json").write_text("{}\n")
        (root / "SHA256SUMS_WRITER_FROZEN_RUN2").write_text(manifest_line())
        check("Run-2 accepted artifact hash mismatch is a hard stop", expect_hard_stop(root))

    with tempfile.TemporaryDirectory(prefix="gap7_manifest_") as td:
        root = Path(td)
        (root / "submissions").mkdir()
        (root / "submissions/writer_output_ACCEPT_FIRST_RUN2.json").write_bytes(
            accepted.read_bytes())
        (root / "SHA256SUMS_WRITER_FROZEN_RUN2").write_text(manifest_line("0" * 64))
        check("manifest must itself pin the one authoritative hash", expect_hard_stop(root))

    check("authoritative loader accepts no caller-selected path",
          len(inspect.signature(run2_writer_input.load_authoritative_writer).parameters) == 0)
    writer = run2_writer_input.load_authoritative_writer()
    check("only the frozen f2b0e73 Run-2 artifact is accepted",
          len(writer["tasks"]) == 53 and sha256_bytes(accepted.read_bytes()) == EXPECTED_ACCEPTED_SHA)

    eligibility = json.loads((HERE / "eligibility_study3.json").read_text())
    writer_key = json.loads(
        (formal_writer_dir / "sealed/_KEY_DO_NOT_SHOW_WRITER.json").read_text())
    accepted_indices = {writer_key["tasks"][wid]["index"] for wid in writer["tasks"]}
    confirmatory_indices = set(eligibility["eligible_indices"].values())
    check("accepted membership is exactly the 53-task confirmatory set",
          len(accepted_indices) == 53 and accepted_indices == confirmatory_indices
          and set(writer["tasks"]) == set(writer_key["tasks"]))

    case_path = HERE / "sealed_materialization/FROZEN_CASE_MANIFEST.json"
    case_doc = json.loads(case_path.read_text())
    check("frozen case manifest is unchanged and covers all 53 tasks",
          sha256_bytes(case_path.read_bytes()) == EXPECTED_CASE_MANIFEST_SHA
          and all(str(idx) in case_doc["tasks"] for idx in confirmatory_indices))

    expected_slices = {
        "srswor_draw": (0, 8),
        "baseline_task_order": (8, 16),
        "baseline_run1_cases": (16, 24),
        "baseline_run2_cases": (24, 32),
        "sprime_task_order": (32, 40),
        "sprime_run1_cases": (40, 48),
        "sprime_run2_cases": (48, 56),
        "writer_ids": (56, 64),
    }
    check("no seed slice changed or was added", SEED_SLICES == expected_slices)

    indices = sorted(confirmatory_indices)
    task_seed = int(PROTOCOL_SHA[32:40], 16)
    assignment_order = np.random.default_rng(task_seed).permutation(len(indices))
    assignment = {f"Q{pos:02d}": indices[int(i)]
                  for pos, i in enumerate(assignment_order, 1)}
    check("shared anonymous task mapping retains its frozen fingerprint",
          canonical_sha(assignment)
          == "f8c615689c16c53f913706fc7f6a72fbaa39dfd4378f474492739ea7df83ee5f")

    case_orders = {}
    for run, seed_slice in {"run1": (40, 48), "run2": (48, 56)}.items():
        rng = np.random.default_rng(int(PROTOCOL_SHA[slice(*seed_slice)], 16))
        case_orders[run] = {
            qid: [int(i) for i in rng.permutation(
                len(case_doc["tasks"][str(idx)]["cases"]))]
            for qid, idx in sorted(assignment.items())
        }
    check("run1 case permutations retain their frozen-seed fingerprint",
          canonical_sha(case_orders["run1"])
          == "8025a077d73d0d5fe41e1b63a9131a3c52335f8edd47be39cea5412bcdc64c46")
    check("run2 case permutations retain their independent frozen-seed fingerprint",
          canonical_sha(case_orders["run2"])
          == "49a31293a52a67039e8e1c89bd0bcfc8ef653b6b8f77c949bb911b2dea85adf5"
          and case_orders["run1"] != case_orders["run2"])

    with tempfile.TemporaryDirectory(prefix="gap7_payload_") as td:
        records = {i: synthetic_record(i) for i in (1, 2)}
        cases = {i: [
            {"situation": "capability", "input": "{'x': 1, 'y': 2}", "expected": "3"},
            {"situation": "safety", "input": "{'x': -1, 'y': 0}",
             "expected": "ValueError"},
        ] for i in records}
        key = build_packages(
            records, [1, 2], Path(td), SCHEMA_SPRIME, "sprime_task_order",
            {"run1": "sprime_run1_cases", "run2": "sprime_run2_cases"},
            {"stage": "gap7-synthetic"}, cases, id_prefix="Q")
        check("semantic payload equality remains enforced across runs",
              key["canonical_payload_sha256"]["run1"]
              == key["canonical_payload_sha256"]["run2"])

    source_hashes = {
        "cp_interval": "79b5d5517ac3f8d1b742bb61853cc9b337f5ec136fbcb3c715806a63b4215780",
        "map_ds_to_baseline": "ecaa2fc27ae020abba766f95574ed2a847c88d43f94fa72c3a247e450ea3ea3b",
        "classify": "e9fc917f3584a87ff84006bf3d9b7a64c452dca786870b9e35eb2e459a8c8aef",
        "score": "1e199273d827458753c0f63d759661c67c51d0d89935b6cb5e6400a6a2a71a68",
    }
    functions = {"cp_interval": cp_interval, "map_ds_to_baseline": map_ds_to_baseline,
                 "classify": classify, "score": score}
    check("scorer substantive functions remain byte-identical",
          all(sha256_bytes(inspect.getsource(functions[name]).encode()) == digest
              for name, digest in source_hashes.items()))

    elig_fx = {"n_drawn": 2, "m": 2, "eligible_task_ids": ["P01", "P02"],
               "either_agree_count_sensitivity_only": 2}
    ds_fx = {"per_task": {
        "P01": {"ds_both_runs": True, "ds_either_run_sensitivity_only": True},
        "P02": {"ds_both_runs": False, "ds_either_run_sensitivity_only": False},
    }}
    vo_fx = {"vo_tasks": {"P02": {"class": "VO-STRUCT"}}, "rejected_claims": []}
    scored = score(elig_fx, ds_fx, vo_fx, None)
    check("scorer substantive behavior remains unchanged",
          scored["classification"]["counts"] == {"DS": 1, "VO": 1, "UR": 0}
          and scored["L0_sample_identification_region"]["region"] == [0.5, 0.5])

    print(f"\n{PASS} passed, {FAIL} failed")
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
