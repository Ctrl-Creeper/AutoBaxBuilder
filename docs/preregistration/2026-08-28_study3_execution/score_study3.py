"""Study 3 — final classification and the three-layer report. Frozen before any outcome.

Classification is a pure function of two frozen derivations: classify(ds, vo) → DS / VO /
UR, with DS ∧ VO a HARD STOP (instrument-defect halt; nothing is reconciled, the process
exits). Writer declarations are read only to print the §7 descriptive distribution; they
enter no classification path (classify() cannot see them).

Output, exactly the frozen protocol §7 list and nothing else:
  - counts and shares P̂(DS), P̂(VO), P̂(UR) over the m measured-eligible tasks;
  - the SAMPLE IDENTIFICATION REGION [P̂(DS), 1−P̂(VO)] — a descriptive identification
    statement, NOT a confidence interval, and never labelled as one;
  - L1: exactly two Clopper–Pearson 95% intervals conditional on the realized m (π_DS,
    π_VO). No percentile-bootstrap CI, no Imbens–Manski interval, no combined interval of
    any kind is computed anywhere in this file;
  - L2: the frozen sensitivity contrasts — DS either-run profile vs the both-runs
    definition; eligibility both-agree (m) vs either-agree count;
  - baseline eligibility rate, realized m (a result, not a target; m = 0 branch
    prespecified), writer declaration distribution, coupling-claim count, rejected VO
    claims (descriptive).

A self-guard scans the serialized output for banned inference vocabulary
("bootstrap", "imbens", "combined_interval", a bare "confidence_interval" key) and refuses
to write if any appears — the scorer cannot mislabel its own layers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scipy import stats

from run2_writer_input import load_authoritative_writer
from study3_pins import load_frozen_sums, sha256_file

HERE = Path(__file__).resolve().parent
OUT = HERE / "results_study3.json"

BANNED_OUTPUT = ("bootstrap", "imbens", "combined_interval", '"confidence_interval"')

FORMAL_RUN2_ACCEPTED = "FORMAL_RUN2_ACCEPTED"
FORMAL_PROCEDURE_INVALID = "FORMAL_PROCEDURE_INVALID"
RUN1_GATE_SHA256 = "357e241ea030ee598f8a091a4f9dacc2947f1f5de9249a9f1ce189cecf19f4c4"
RUN1_MANIFEST_SHA256 = "9ee2c753306b90c62bbbfe816150119737cd9b2eb04d67079665fe6efa70fd71"
GAP6_MANIFEST_SHA256 = "ef6350ae135f94a9de4c10d2004a77196df9c75b042c2c25b069c948e826533e"
GAP6_AUDIT_SHA256 = "a5ac01698990a04a6a9cd6d67dd6bc54d851f19de0a951172c91d7ea2f9a167c"
GAP6_RECORD_SHA256 = "a52fc7ee3704ae265dfc37dac860487969c848f91f3a43ba5f4146d1675b8dca"
RUN2_MANIFEST_SHA256 = "0d9c21779e618ed1bdadb7ee08b958411a339e75cb167e595f39616a8f4e9e63"
RUN2_TERMINAL_SHA256 = "ee64173d1479c8a143f9acd9eedc9466c8181f3c618bd29f84ea8367c3ae4545"
RUN2_ACCEPTED_SHA256 = "f2b0e73ab1d8b5efcb22bb53c2b8d026446994992195d9b55b483d8de593b49e"
SPRIME_BUILD_MANIFEST_SHA256 = "574632cd27e2317363d261d8c46e9d330fffeca3a65d14cf4f15dc3423fb21ab"
SPRIME_PROVENANCE_SHA256 = "0a6565a4b85a41362b5df0e8995327e232f9b657fc4260f46ac758e1f18642c5"
SPRIME_FROZEN_MANIFEST_SHA256 = "2a642e79c48845a146c0dbedc061e8ddc9a13c0221b3c826b0daa70e1077794d"
DS_MANIFEST_SHA256 = "a9dbd5ca69db9d447a72d0092d0b063465d13ff8f0c4aeac3e87b346aac9f206"
DS_DERIVATION_SHA256 = "3377d187c2c37177f37e1c9b5d648b34468d10bd4239404b971888c835e4efe7"
VO_MANIFEST_SHA256 = "38d60bbb2e6fdf489ae47d6c345d143d1c590a3b16dd0c3bcdd21ed03c584803"
VO_DERIVATION_SHA256 = "cd2cc35b269a1d27d9093462685eae09ace6dc07d9fec95002f9cba55d3c0060"
VO_AUDIT_SHA256 = "152de48a4b9ee5ce5d3577ac53fba76837c238af400f222061e1482ebc4aa9c0"
VO_PROVENANCE_SHA256 = "9059365a44633831e509eb0a514def18c5f5ae075fe12410a8c5b3c88ce23d46"
VO_EXECUTABILITY_AUDIT_SHA256 = "d4554d7a9706bcbd3736fed6c8544aa41d00a2b0a4c58b0b130fd1eaf15275ca"
VO_TOOL_SHA256 = "6bc60024915a81b88b866300adb7e3c7ca255a0f82333d858a91462bcd05df4a"


def _require_sha256(path: Path, expected: str, label: str) -> None:
    if not path.is_file() or sha256_file(path) != expected:
        sys.exit(f"HARD STOP - {label} is missing or has the wrong hash")


def _require_manifest_entry(manifest: Path, rel: str, expected: str, label: str) -> None:
    try:
        frozen = load_frozen_sums(manifest)
    except (OSError, ValueError):
        sys.exit(f"HARD STOP - {label} manifest is missing or malformed")
    if frozen.get(rel) != expected:
        sys.exit(f"HARD STOP - {label} manifest has the wrong entry")


def _require_run1_gate(gate_path: Path) -> None:
    manifest = HERE / "writer_handoff/SHA256SUMS_WRITER_FROZEN"
    _require_sha256(manifest, RUN1_MANIFEST_SHA256, "Run-1 manifest")
    _require_manifest_entry(manifest, "GATE_UNREPAIRABLE_FROZEN.json", RUN1_GATE_SHA256,
                            "Run-1 gate")
    _require_sha256(gate_path, RUN1_GATE_SHA256, "Run-1 gate")
    if json.loads(gate_path.read_text()).get("verdict") != "UNREPAIRABLE_FIRST_SUBMISSION":
        sys.exit("HARD STOP - Run-1 gate has the wrong terminal status")


def _require_gap6_disposition() -> None:
    _require_sha256(HERE / "SHA256SUMS_GAP6", GAP6_MANIFEST_SHA256,
                    "GAP-6 disposition manifest")
    _require_sha256(HERE / "GAP6_writer_instrument_contract_audit.md", GAP6_AUDIT_SHA256,
                    "GAP-6 disposition audit")
    record = HERE / "GAP6_REPAIR_RECORD.md"
    _require_sha256(record, GAP6_RECORD_SHA256, "GAP-6 disposition record")
    text = record.read_text()
    required = ("WRITER_INSTRUMENT_CONTRACT_FAILURE",
                "Run 1 enters no DS/VO/UR identification result")
    if not all(marker in text for marker in required):
        sys.exit("HARD STOP - GAP-6 disposition has the wrong status")


def _require_run2_terminal() -> None:
    manifest = HERE / "writer_handoff/SHA256SUMS_WRITER_FROZEN_RUN2"
    _require_sha256(manifest, RUN2_MANIFEST_SHA256, "Run-2 terminal manifest")
    _require_manifest_entry(manifest, "WRITER_RUN2_TERMINAL_STATE.md", RUN2_TERMINAL_SHA256,
                            "Run-2 terminal")
    terminal = HERE / "writer_handoff/WRITER_RUN2_TERMINAL_STATE.md"
    _require_sha256(terminal, RUN2_TERMINAL_SHA256, "Run-2 terminal")
    if "Status: **ACCEPT_FIRST_RUN2**" not in terminal.read_text():
        sys.exit("HARD STOP - Run-2 terminal has the wrong status")
    rel = "submissions/writer_output_ACCEPT_FIRST_RUN2.json"
    _require_manifest_entry(manifest, rel, RUN2_ACCEPTED_SHA256, "Run-2 accepted artifact")
    _require_sha256(HERE / "writer_handoff" / rel, RUN2_ACCEPTED_SHA256,
                    "Run-2 accepted artifact")


def _require_run2_ds_provenance(ds_path: Path) -> None:
    build_manifest = HERE / "SHA256SUMS_SPRIME_PACKET_BUILD"
    _require_sha256(build_manifest, SPRIME_BUILD_MANIFEST_SHA256,
                    "S-prime build provenance manifest")
    _require_manifest_entry(build_manifest, "sprime_packet_build_provenance.json",
                            SPRIME_PROVENANCE_SHA256, "S-prime build provenance")
    provenance_path = HERE / "sprime_packet_build_provenance.json"
    _require_sha256(provenance_path, SPRIME_PROVENANCE_SHA256,
                    "S-prime build provenance")
    provenance = json.loads(provenance_path.read_text())
    writer = provenance.get("authoritative_writer_input", {})
    if writer != {
        "path": "writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json",
        "terminal_state": "ACCEPT_FIRST_RUN2",
        "sha256": RUN2_ACCEPTED_SHA256,
        "sole_constructive_input": True,
    }:
        sys.exit("HARD STOP - S-prime provenance does not name the sole Run-2 input")

    ds_manifest = HERE / "SHA256SUMS_DS_ONLY"
    _require_sha256(ds_manifest, DS_MANIFEST_SHA256, "DS derivation manifest")
    _require_manifest_entry(ds_manifest, "ds_derivation.json", DS_DERIVATION_SHA256,
                            "DS derivation")
    sprime_manifest = HERE / "submissions_sprime/SHA256SUMS_SPRIME_FROZEN"
    _require_manifest_entry(ds_manifest, "submissions_sprime/SHA256SUMS_SPRIME_FROZEN",
                            SPRIME_FROZEN_MANIFEST_SHA256, "S-prime submission freeze")
    _require_sha256(sprime_manifest, SPRIME_FROZEN_MANIFEST_SHA256,
                    "S-prime submission freeze")
    _require_sha256(ds_path, DS_DERIVATION_SHA256, "DS derivation")


def _require_vo_struct_provenance() -> None:
    manifest = HERE / "SHA256SUMS_VO_STRUCT_FROZEN"
    _require_sha256(manifest, VO_MANIFEST_SHA256, "VO-STRUCT freeze manifest")
    entries = (
        ("vo_certificates.json", VO_DERIVATION_SHA256),
        ("VO_STRUCT_EXECUTION_AUDIT.json", VO_AUDIT_SHA256),
        ("VO_STRUCT_EXECUTION_PROVENANCE.json", VO_PROVENANCE_SHA256),
        ("VO_STRUCT_EXECUTABILITY_AUDIT.md", VO_EXECUTABILITY_AUDIT_SHA256),
        ("vo_certificates.py", VO_TOOL_SHA256),
    )
    for rel, expected in entries:
        _require_manifest_entry(manifest, rel, expected, "VO-STRUCT freeze")
        _require_sha256(HERE / rel, expected, f"VO-STRUCT {rel}")
    provenance = json.loads((HERE / "VO_STRUCT_EXECUTION_PROVENANCE.json").read_text())
    formal = provenance.get("formal_artifact", {})
    closed = provenance.get("vo_defect", {})
    if formal.get("sha256") != VO_DERIVATION_SHA256:
        sys.exit("HARD STOP - VO-STRUCT provenance has the wrong formal artifact")
    if not (closed.get("status") == "PERMANENTLY_CLOSED"
            and closed.get("input_directory_present") is False
            and closed.get("certificate_files_present") == 0
            and closed.get("attestation_files_present") == 0):
        sys.exit("HARD STOP - VO-DEFECT is not frozen closed")
    if (HERE / "vo_defect").exists():
        sys.exit("HARD STOP - VO-DEFECT input directory exists")


def _has_post_run1_provenance() -> bool:
    markers = (
        "SHA256SUMS_GAP6",
        "GAP6_writer_instrument_contract_audit.md",
        "GAP6_REPAIR_RECORD.md",
        "writer_handoff/SHA256SUMS_WRITER_FROZEN_RUN2",
        "writer_handoff/WRITER_RUN2_TERMINAL_STATE.md",
        "writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json",
        "SHA256SUMS_SPRIME_PACKET_BUILD",
        "sprime_packet_build_provenance.json",
        "submissions_sprime/SHA256SUMS_SPRIME_FROZEN",
        "SHA256SUMS_DS_ONLY",
    )
    return any((HERE / rel).exists() for rel in markers)


def cp_interval(k: int, n: int) -> list[float]:
    """Clopper–Pearson 95%, conditional on n. The audit-adopted L1 estimator."""
    if n == 0:
        return [0.0, 1.0]
    lo = 0.0 if k == 0 else float(stats.beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(0.975, k + 1, n - k))
    return [lo, hi]


def map_ds_to_baseline(ds: dict, elig: dict) -> dict:
    """The baseline (P…) and S′ (Q…) task-id namespaces meet only through the shared
    source index; mechanical re-keying, nothing else."""
    idx_to_q = {v: k for k, v in ds["task_index"].items()}
    return {"per_task": {t: ds["per_task"][idx_to_q[elig["eligible_indices"][t]]]
                         for t in elig["eligible_task_ids"]}}


def classify(ds: bool, vo: bool) -> str:
    """Pure. Sees nothing but the two frozen derivations' booleans."""
    if ds and vo:
        sys.exit("HARD STOP — DS and VO certified for the same task: instrument/procedure "
                 "defect (protocol §6). Interpretation stops here; nothing is reconciled "
                 "silently and no classification is emitted.")
    return "DS" if ds else "VO" if vo else "UR"


def score(elig: dict, ds: dict, vo: dict, writer_declarations: dict | None,
          procedure_invalid: frozenset | set = frozenset()) -> dict:
    m = elig["m"]
    results: dict = {
        "n_drawn": elig["n_drawn"],
        "m_measured_eligible": m,
        "m_note": "m is a result, not a target (CR-1: no supplemental draw whatever m is)",
        "baseline_eligibility_rate": m / elig["n_drawn"] if elig["n_drawn"] else None,
    }
    if m == 0:
        results["no_eligible_tasks"] = True
        for layer in ("classification", "L0_sample_identification_region",
                      "L1_sampling_clopper_pearson", "L2_measurement_sensitivity"):
            results[layer] = "no eligible tasks (prespecified m = 0 branch)"
        return results

    per_task = {}
    for tid in elig["eligible_task_ids"]:
        if tid in procedure_invalid:
            if tid in ds.get("per_task", {}):
                sys.exit(f"HARD STOP — {tid} is routed procedure-invalid (GAP-5 / "
                         "Interpretation Note 2) yet appears in the S′ derivation: it "
                         "entered verification runs it was barred from")
            d = False  # GAP-5 clause 4: never DS
        else:
            d = ds["per_task"][tid]["ds_both_runs"]
        v = tid in vo["vo_tasks"]
        per_task[tid] = classify(d, v)
    k_ds = sum(1 for c in per_task.values() if c == "DS")
    k_vo = sum(1 for c in per_task.values() if c == "VO")
    k_ur = m - k_ds - k_vo

    results["classification"] = {"per_task": per_task,
                                 "counts": {"DS": k_ds, "VO": k_vo, "UR": k_ur},
                                 "shares": {"P_hat_DS": k_ds / m, "P_hat_VO": k_vo / m,
                                            "P_hat_UR": k_ur / m}}
    results["L0_sample_identification_region"] = {
        "region": [k_ds / m, 1 - k_vo / m],
        "statement": "descriptive identification statement over the measured-eligible "
                     "sample; NOT a confidence interval; width = P_hat_UR "
                     "(identification, irreducible by sample size)"}
    results["L1_sampling_clopper_pearson"] = {
        "pi_ds_cp95": cp_interval(k_ds, m),
        "pi_vo_cp95": cp_interval(k_vo, m),
        "conditional_on_m": m,
        "targets": "procedure-inclusive pi_DS, pi_VO over the eligible subpopulation "
                   "(frozen eligibility rule); FPC ignored (conservative); per-endpoint "
                   "only, never merged with L0 or each other"}
    results["L2_measurement_sensitivity"] = {
        "ds_either_run_share_sensitivity_only":
            sum(ds["per_task"][t]["ds_either_run_sensitivity_only"]
                for t in elig["eligible_task_ids"] if t not in procedure_invalid) / m,
        "ds_both_runs_definition_share": k_ds / m,
        "eligibility_both_agree_m": m,
        "eligibility_either_agree_count_sensitivity_only":
            elig["either_agree_count_sensitivity_only"],
        "note": "sensitivity descriptives only; never a confirmatory classification"}
    results["descriptive"] = {
        "procedure_invalid_candidate": {
            "count": len(procedure_invalid),
            "task_ids": sorted(procedure_invalid),
            "note": "procedure diagnostic, not a fourth epistemic outcome (GAP-5 / "
                    "Interpretation Note 2); these tasks remain in m, are never DS, and "
                    "classify VO/UR via the independent certificate path"},
        "rejected_vo_claims": len(vo.get("rejected_claims", [])),
        "vo_classes": {c["class"]: sum(1 for x in vo["vo_tasks"].values()
                                       if x["class"] == c["class"])
                       for c in vo["vo_tasks"].values()} if vo["vo_tasks"] else {},
    }
    if writer_declarations is not None:
        dist: dict[str, int] = {}
        for t in writer_declarations["tasks"].values():
            code = (t.get("failure") or {}).get("code") or "none"
            dist[code] = dist.get(code, 0) + 1
        results["descriptive"]["writer_declaration_distribution"] = dist
        results["descriptive"]["coupling_claims_F1"] = dist.get("F1_LIST_COUPLING", 0)
        results["descriptive"]["note"] = ("writer declarations are descriptive only; they "
                                          "enter no classification path")
    return results


def resolve_terminal_state() -> str:
    """Resolve the formal constructive terminal without inspecting task outcomes."""
    ds_path = HERE / "ds_derivation.json"
    gate_path = HERE / "writer_handoff/GATE_UNREPAIRABLE_FROZEN.json"
    if ds_path.exists() and gate_path.exists():
        _require_run1_gate(gate_path)
        _require_gap6_disposition()
        _require_run2_terminal()
        _require_run2_ds_provenance(ds_path)
        _require_vo_struct_provenance()
        return FORMAL_RUN2_ACCEPTED
    if gate_path.exists():
        if _has_post_run1_provenance():
            sys.exit("HARD STOP - unknown terminal combination: historical Run-1 "
                     "provenance exists without a complete formal Run-2 DS path")
        _require_run1_gate(gate_path)
        return FORMAL_PROCEDURE_INVALID
    sys.exit("HARD STOP - no recognized formal constructive terminal state")


def main() -> None:
    if OUT.exists():
        sys.exit("results_study3.json already exists; a frozen scoring is never redone")
    elig = json.loads((HERE / "eligibility_study3.json").read_text())

    if elig["m"] == 0:
        results = score(elig, {}, {}, None)
    else:
        terminal = resolve_terminal_state()
        if terminal == FORMAL_RUN2_ACCEPTED:
            ds_path = HERE / "ds_derivation.json"
            ds = json.loads(ds_path.read_text())
            ds_by_baseline_tid = map_ds_to_baseline(ds, elig)
            procedure_invalid: frozenset = frozenset()
            writer = load_authoritative_writer()
        elif terminal == FORMAL_PROCEDURE_INVALID:
            gate_path = HERE / "writer_handoff/GATE_UNREPAIRABLE_FROZEN.json"
            frozen = load_frozen_sums(HERE / "writer_handoff/SHA256SUMS_WRITER_FROZEN")
            if sha256_file(gate_path) != frozen[gate_path.name]:
                sys.exit("unrepairable gate verdict does not match its frozen hash; "
                         "refusing to score")
            if json.loads(gate_path.read_text()).get("verdict") \
                    != "UNREPAIRABLE_FIRST_SUBMISSION":
                sys.exit("frozen gate report exists but its verdict is not "
                         "UNREPAIRABLE_FIRST_SUBMISSION; refusing to score")
            ds_by_baseline_tid = {"per_task": {}}
            procedure_invalid = frozenset(elig["eligible_task_ids"])
            writer = None  # the formal writer output never passed the validator;
            #                its declaration distribution is not parsed (Note 2)
        else:
            sys.exit("HARD STOP - terminal resolver returned an unknown state")
        vo = json.loads((HERE / "vo_certificates.json").read_text())
        results = score(elig, ds_by_baseline_tid, vo, writer,
                        procedure_invalid=procedure_invalid)

    serialized = json.dumps(results, indent=1, ensure_ascii=False)
    hits = [b for b in BANNED_OUTPUT if b in serialized.lower()]
    if hits:
        sys.exit(f"self-guard: banned inference vocabulary in output {hits}; refusing to write")
    OUT.write_text(serialized + "\n")
    print(serialized)
    print(f"\nresults sha256 {sha256_file(OUT)} — freeze this hash")


if __name__ == "__main__":
    main()
