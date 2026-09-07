"""Read-only post-build audit for the formal Study-3 S-prime packets.

The audit independently reconstructs the authorized 53-task population, candidate render,
frozen case source, anonymous mapping, and both case permutations. It never runs testcase
extraction, a verifier, the scorer, DS derivation, or VO certification. The JSON report
contains only hashes, counts, and check results; candidate and case contents are never
printed or written to the report.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from packet_build import BEGIN_S, END_S, INSTRUCTIONS, load_shipped_get_prompt, render_task  # noqa: E402
from run2_writer_input import (ACCEPTED_REL, ACCEPTED_SHA256, RUN2_MANIFEST,  # noqa: E402
                               load_authoritative_writer)
from study3_pins import (PROTOCOL_SHA, RUNS, SCHEMA_SPRIME, SEED_SLICES,  # noqa: E402
                         load_case_manifest, sha256_file, sprime_record)
from validate_study3_submission import J1_KEYS, TASK_KEYS  # noqa: E402

SPRIME = HERE / "sprime"
ELIGIBILITY = HERE / "eligibility_study3.json"
WRITER_DIR = HERE / "writer_handoff"
WRITER_KEY = WRITER_DIR / "sealed/_KEY_DO_NOT_SHOW_WRITER.json"
CASE_MANIFEST = HERE / "sealed_materialization/FROZEN_CASE_MANIFEST.json"
REPORT = HERE / "sprime_packet_audit_report.json"

ELIGIBILITY_SHA256 = "a9db938ba633bc400ac035d9a200501c8bb7c70986f9b38c2e964885f483f3a6"
CASE_MANIFEST_SHA256 = "2422431ac301aa4e439fe4ff2bdc7e23d6dfd2ffdf836cd8bdbda3ed25df2a36"
BUILDER_SHA256 = "f60f0b82a89ec301de95b8ff6dd8c39ed62e35e0a521338e3cc765cb0b546cf5"
PACKET_BUILD_SHA256 = "c7fd203d5d30eda1c7c5049d6de9d217aecbdca25f4fcdfd91469024534e11cb"
MAPPING_SHA256 = "f8c615689c16c53f913706fc7f6a72fbaa39dfd4378f474492739ea7df83ee5f"
RUN1_CASE_ORDER_SHA256 = "8025a077d73d0d5fe41e1b63a9131a3c52335f8edd47be39cea5412bcdc64c46"
RUN2_CASE_ORDER_SHA256 = "49a31293a52a67039e8e1c89bd0bcfc8ef653b6b8f77c949bb911b2dea85adf5"

checks: list[dict[str, object]] = []


def canonical_sha(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def check(name: str, ok: bool) -> None:
    checks.append({"name": name, "passed": bool(ok)})
    print(f"  {'ok  ' if ok else 'FAIL'} {name}")


def finish(summary: dict[str, object] | None = None) -> None:
    passed = sum(bool(c["passed"]) for c in checks)
    failed = len(checks) - passed
    report = {
        "protocol_sha256": PROTOCOL_SHA,
        "checks_passed": passed,
        "checks_failed": failed,
        "checks": checks,
        **(summary or {}),
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\n{passed} passed, {failed} failed")
    print("S-PRIME PACKET AUDIT PASSED" if not failed else "S-PRIME PACKET AUDIT FAILED")
    raise SystemExit(1 if failed else 0)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def main() -> None:  # noqa: C901
    if not SPRIME.is_dir():
        check("formal S-prime build exists", False)
        finish()

    # Frozen inputs and sole constructive writer interface.
    check("eligibility manifest matches frozen hash",
          sha256_file(ELIGIBILITY) == ELIGIBILITY_SHA256)
    check("FROZEN_CASE_MANIFEST matches frozen hash",
          sha256_file(CASE_MANIFEST) == CASE_MANIFEST_SHA256)
    check("frozen builder and shared packet builder match tooling hashes",
          sha256_file(HERE / "build_study3_sprime_packets.py") == BUILDER_SHA256
          and sha256_file(HERE / "packet_build.py") == PACKET_BUILD_SHA256)
    check("authoritative writer loader has no caller-selected input",
          len(inspect.signature(load_authoritative_writer).parameters) == 0
          and str(ACCEPTED_REL) == "submissions/writer_output_ACCEPT_FIRST_RUN2.json"
          and RUN2_MANIFEST == "SHA256SUMS_WRITER_FROZEN_RUN2")

    writer = load_authoritative_writer()
    accepted_path = WRITER_DIR / ACCEPTED_REL
    check("Run-2 ACCEPT_FIRST artifact is the sole hash-pinned constructive input",
          sha256_file(accepted_path) == ACCEPTED_SHA256)

    eligibility = json.loads(ELIGIBILITY.read_text())
    writer_key = json.loads(WRITER_KEY.read_text())
    key_path = SPRIME / "sealed/_KEY_DO_NOT_SHOW_CODERS.json"
    key = json.loads(key_path.read_text())
    eligible = sorted(eligibility["eligible_indices"].values())
    eligible_set = set(eligible)
    writer_indices = {writer_key["tasks"][wid]["index"] for wid in writer["tasks"]}
    key_indices = [meta["index"] for meta in key["tasks"].values()]

    check("accepted writer task membership is exactly confirmatory eligibility",
          len(writer["tasks"]) == 53 and writer_indices == eligible_set
          and set(writer["tasks"]) == set(writer_key["tasks"]))
    check("packet population contains exactly 53 tasks",
          len(key["tasks"]) == 53 and len(set(key_indices)) == 53)
    check("packet membership equals the confirmatory eligible set",
          sorted(key_indices) == eligible)
    check("zero either-only sensitivity tasks were added",
          set(key_indices) == eligible_set
          and eligibility["m"] == 53
          and eligibility["either_agree_count_sensitivity_only"] == 56)
    check("no redraw, replacement, supplement, or outcome filtering changed membership",
          set(key_indices) == writer_indices == eligible_set)

    # Provenance hashes and frozen randomization.
    check("sealed key pins Run-2 writer, eligibility, and frozen cases",
          key.get("writer_output_sha256") == ACCEPTED_SHA256
          and key.get("eligibility_manifest_sha256") == ELIGIBILITY_SHA256
          and key.get("frozen_case_manifest_sha256") == CASE_MANIFEST_SHA256
          and key.get("protocol_sha256") == PROTOCOL_SHA
          and key.get("schema_version") == SCHEMA_SPRIME
          and key.get("stage") == "sprime")

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
    seeds = {
        "task_order": int(PROTOCOL_SHA[32:40], 16),
        "run1": int(PROTOCOL_SHA[40:48], 16),
        "run2": int(PROTOCOL_SHA[48:56], 16),
    }
    check("sealed seeds equal the frozen S-prime seed slices", key.get("seeds") == seeds)
    order = np.random.default_rng(seeds["task_order"]).permutation(len(eligible))
    assignment = {f"Q{pos:02d}": eligible[int(i)] for pos, i in enumerate(order, 1)}
    actual_assignment = {tid: meta["index"] for tid, meta in key["tasks"].items()}
    check("shared anonymous task mapping reproduces from the frozen task seed",
          actual_assignment == assignment and canonical_sha(assignment) == MAPPING_SHA256)

    cases_by_index = load_case_manifest()
    expected_case_orders: dict[str, dict[str, list[int]]] = {}
    case_order_hashes = {"run1": RUN1_CASE_ORDER_SHA256, "run2": RUN2_CASE_ORDER_SHA256}
    for run in RUNS:
        rng = np.random.default_rng(seeds[run])
        expected_case_orders[run] = {
            tid: [int(i) for i in rng.permutation(len(cases_by_index[idx]))]
            for tid, idx in sorted(assignment.items())
        }
        actual = {tid: key["tasks"][tid][f"{run}_case_order"] for tid in sorted(assignment)}
        check(f"{run} case order matches its frozen independent seed",
              actual == expected_case_orders[run]
              and canonical_sha(expected_case_orders[run]) == case_order_hashes[run])
    check("the two runs share task mapping and use distinct frozen case permutations",
          expected_case_orders["run1"] != expected_case_orders["run2"])

    # Independently reconstruct candidates and packet files without exposing content.
    from secodeplt_task_runner import load
    records = {record["index"]: record for record in load(only_stdlib=False)}
    get_prompt = load_shipped_get_prompt()
    candidates_by_index = {
        writer_key["tasks"][wid]["index"]: sprime_record(
            records[writer_key["tasks"][wid]["index"]], candidate)
        for wid, candidate in writer["tasks"].items()
    }
    expected_specs = {idx: get_prompt(record) for idx, record in candidates_by_index.items()}

    visible_files_ok = True
    candidate_ok = True
    cases_ok = True
    permutation_ok = True
    rerender_ok = True
    situation_key_ok = True
    total_rows: dict[str, int] = {}
    payload: dict[str, str] = {}
    for run in RUNS:
        package = SPRIME / f"{run}_package"
        expected_files = {Path("INSTRUCTIONS.md"), Path("answers_template.json"),
                          Path("PACKET_FINGERPRINT")}
        expected_files.update(Path("tasks") / f"{tid}.md" for tid in assignment)
        actual_files = {path.relative_to(package) for path in package.rglob("*") if path.is_file()}
        visible_files_ok &= actual_files == expected_files
        canon = {}
        rows_seen = 0
        for tid, idx in sorted(assignment.items()):
            meta = key["tasks"][tid]
            cases = cases_by_index[idx]
            order_for_task = expected_case_orders[run][tid]
            md = (package / f"tasks/{tid}.md").read_text()
            parts = md.split(BEGIN_S, 1)
            if len(parts) != 2 or END_S not in parts[1]:
                candidate_ok = rerender_ok = False
                continue
            shown_spec = parts[1].split(END_S, 1)[0].strip()
            candidate_ok &= shown_spec == expected_specs[idx]
            situation_key_ok &= meta["case_situations_source_order"] == [
                case["situation"] for case in cases]
            permutation_ok &= meta[f"{run}_case_order"] == order_for_task
            rerender_ok &= md == render_task(tid, expected_specs[idx], cases, order_for_task)
            rows = re.findall(r"^\| \d+ \| `(.*)` \| `(.*)` \|$", md, re.MULTILINE)
            rows_seen += len(rows)
            expected_rows = [[cases[i]["input"], cases[i]["expected"]] for i in order_for_task]
            cases_ok &= [list(row) for row in rows] == expected_rows
            canon[tid] = {"s_t": shown_spec,
                          "cases": sorted([case["input"], case["expected"]]
                                          for case in cases)}
        total_rows[run] = rows_seen
        payload[run] = hashlib.sha256(
            json.dumps(canon, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    check("visible package file sets contain only the frozen instrument and 53 task files",
          visible_files_ok)
    check("every candidate render is reconstructed from the authoritative Run-2 artifact",
          candidate_ok and set(candidates_by_index) == eligible_set)
    check("every displayed case is byte-equal to FROZEN_CASE_MANIFEST", cases_ok)
    check("all per-task presentation permutations match the sealed key", permutation_ok)
    check("every task file byte-rerenders from candidate plus frozen cases", rerender_ok)
    check("sealed case-identity mapping is item-equal to the frozen manifest", situation_key_ok)

    n_manifest_cases = sum(len(cases_by_index[idx]) for idx in eligible)
    n_key_cases = sum(len(meta["case_situations_source_order"])
                      for meta in key["tasks"].values())
    check("each run contains exactly the frozen population's 239 cases",
          total_rows == {"run1": 239, "run2": 239}
          and n_manifest_cases == n_key_cases == 239)
    check("two-run semantic payload is identical and matches the sealed hash",
          payload["run1"] == payload["run2"]
          and payload == key["canonical_payload_sha256"])
    fingerprints = {
        run: (SPRIME / f"{run}_package/PACKET_FINGERPRINT").read_text().strip()
        for run in RUNS
    }
    check("both packet fingerprints equal the canonical semantic-payload hash",
          fingerprints == payload)

    # Frozen J1 instrument, blinding, and sealed-key placement.
    static_equal = all(
        (SPRIME / f"run1_package/{name}").read_bytes()
        == (SPRIME / f"run2_package/{name}").read_bytes()
        for name in ("INSTRUCTIONS.md", "answers_template.json", "PACKET_FINGERPRINT")
    )
    check("run differences are limited to frozen case presentation and run metadata",
          static_equal)
    check("verification instructions are byte-identical to the frozen J1 instrument",
          all((SPRIME / f"{run}_package/INSTRUCTIONS.md").read_text() == INSTRUCTIONS
              for run in RUNS))

    hard_banned = [
        "writer", "obstruction", "failure", "qualifying", "eligib", "baseline",
        "round-2", "round2", "run-1", "run1", "gap-6", "gap6", "gap-7", "gap7",
        "study-1", "study1", "secodeplt", "cwe", "provenance", "materializ",
        "manifest", "sealed", "_key_", "security case", "capability case",
    ]
    hard_patterns = [r"\bDS\b", r"\bVO\b", r"\bUR\b", r"\bF[1-5]\b"]
    leaks: list[str] = []
    for run in RUNS:
        package = SPRIME / f"{run}_package"
        for path in sorted(package.rglob("*")):
            if not path.is_file():
                continue
            text = path.read_text()
            if path.parent.name == "tasks":
                text = text.split(BEGIN_S, 1)[0] + text.split(END_S, 1)[1]
                text = re.sub(r"^\| \d+ \|.*$", "", text, flags=re.MULTILINE)
            framing = text + "\n" + str(path.relative_to(package))
            low = framing.lower()
            leaks.extend(f"{run}:{word}" for word in hard_banned if word in low)
            leaks.extend(f"{run}:{pattern}" for pattern in hard_patterns
                         if re.search(pattern, framing))
    check("researcher-generated verifier-visible material contains no banned metadata",
          not leaks)

    inside_keys = [path for run in RUNS
                   for path in (SPRIME / f"{run}_package").rglob("*")
                   if path.is_file() and "KEY" in path.name.upper()]
    check("sealed key is outside both verifier-visible packages",
          key_path.is_file() and not inside_keys)

    templates_ok = True
    for run in RUNS:
        template = json.loads((SPRIME / f"{run}_package/answers_template.json").read_text())
        templates_ok &= (
            template.get("schema_version") == SCHEMA_SPRIME
            and set(template) == {"schema_version", "coder_id",
                                  "packet_fingerprint_sha256", "tasks"}
            and set(template["tasks"]) == set(assignment)
            and all(set(task) == TASK_KEYS
                    and all(set(item) == J1_KEYS for item in task["J1"])
                    and len(task["J1"]) == len(cases_by_index[assignment[tid]])
                    for tid, task in template["tasks"].items())
            and all(item["determined"] is None and item["quote"] == ""
                    and item["confidence"] is None
                    for task in template["tasks"].values() for item in task["J1"])
        )
    check("blank templates implement only the frozen per-case J1 schema", templates_ok)

    # A pinned/source-level boundary proves the build itself cannot extract cases or compute outcomes.
    builder_path = HERE / "build_study3_sprime_packets.py"
    builder_source = builder_path.read_text().lower()
    builder_imports = imported_modules(builder_path)
    forbidden_modules = {"materialize_cases", "derive_ds", "score_study3", "vo_certificates"}
    check("packet build has no testcase re-extraction path",
          "extract_testcases" not in builder_source
          and "materialize_cases" not in builder_source
          and "testcases" not in imported_modules(builder_path))
    check("packet build imports no scorer, DS, VO, or outcome module",
          not (builder_imports & forbidden_modules)
          and not any(token in builder_source for token in
                      ("procedure_invalid_candidate", "predicted_ds", "derive_ds(")))
    check("packet build contains no Run-1 accepted-input fallback",
          "study3_writer_accepted" not in builder_source
          and "sha256sums_writer_frozen\"" not in builder_source
          and "first_submission_anchor.json" not in builder_source)

    sealed_key_sha = sha256_file(key_path)
    finish({
        "n_tasks": len(key["tasks"]),
        "n_cases_per_run": total_rows,
        "semantic_payload_sha256": payload["run1"],
        "packet_fingerprints": fingerprints,
        "sealed_key_sha256": sealed_key_sha,
        "anonymous_mapping_sha256": canonical_sha(assignment),
        "case_order_sha256": {run: canonical_sha(expected_case_orders[run]) for run in RUNS},
    })


if __name__ == "__main__":
    main()
