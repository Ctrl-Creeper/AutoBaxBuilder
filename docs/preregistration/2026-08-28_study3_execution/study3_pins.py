"""Study 3 — frozen pins and shared mechanical helpers.

Frozen inputs (commit 75e7968): the Study-3 protocol and the mechanically built frame.
Every Study-3 execution module imports its constants and shared arithmetic from here.
The Study-1 packet machinery is imported AS CODE ONLY (frozen module `build_study1_packets`,
per the protocol's verbatim-reuse clause and the checklist's "imported as code only" rule);
no Study-1 result, submission, or sealed artifact is ever read.

Mechanical parse decisions documented at tooling freeze (implementation details of frozen
protocol wording, each with frozen precedent, none a new rule):

  - Eligibility "at least one safety case determined in both runs (both-agree)" is read at
    CASE level: there exists a safety case that BOTH runs call determined. This matches the
    protocol's own name for the rule ("both-agree"), and the frozen Study-1 scorer's use of
    "both" (case determined by both runs). The either-agree sensitivity variant is the case-
    level union, reported only in L2.
  - DS per-run profile: every capability case determined AND no safety case determined, in
    that run; DS requires the profile in both runs (protocol §1/§5 verbatim).
  - Parameter names are extracted from the original record's `ground_truth.code_before`
    def line — the frozen Round-2 writer-package rule (scripts/build_writer_package.py).
  - VO-STRUCT immutable-carrier predicate for a quote: after whitespace/case normalisation
    it locates in the setup segment, the closing instruction, or the function-name segment,
    or it equals one of the original parameter names (protocol §6's enumerated immutable
    carriers: setup block, function name, closing instruction, mandatory parameter mentions).
  - Presentation seeds derive from the frozen protocol hash by fixed slices; [0:8] is the
    protocol's own SRSWOR rule, the rest are disjoint slices pinned here:
    baseline task order [8:16], baseline run1/run2 case orders [16:24]/[24:32];
    S′ task order [32:40], S′ run1/run2 case orders [40:48]/[48:56]; writer ids [56:64].
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "docs/preregistration/2026-08-27_study1_execution"))

PROTOCOL = REPO / "docs/preregistration/2026-08-28_study3_constructive_separability_protocol.md"
PROTOCOL_SHA = "548addbd9277dbe901b8e1e599fdf3a6d4ef97e286610dbecc40bf1f5f5f81d7"
FRAME = REPO / "docs/preregistration/2026-08-28_study3_frame.json"
FRAME_SHA = "ce8fd588c4bd1dd2e4e4c0fdf7318fee20dc19d92d22c186b3a0e4a6102b64d9"

N_DRAW = 90  # CR-1: resource-fixed, one draw, never supplemented

SCHEMA_BASELINE = "study3-baseline-run-v1"
SCHEMA_SPRIME = "study3-sprime-run-v1"
SCHEMA_WRITER = "study3-writer-v1"
RUNS = ("run1", "run2")

SEED_SLICES = {
    "srswor_draw": (0, 8),          # the protocol's own frozen rule
    "baseline_task_order": (8, 16),
    "baseline_run1_cases": (16, 24),
    "baseline_run2_cases": (24, 32),
    "sprime_task_order": (32, 40),
    "sprime_run1_cases": (40, 48),
    "sprime_run2_cases": (48, 56),
    "writer_ids": (56, 64),
}

FAILURE_CODES = {"F1_LIST_COUPLING", "F2_SIGNATURE_CARRIER", "F3_PREAMBLE_CARRIER",
                 "F4_RETURN_CONTRACT_CARRIER", "F5_MATERIAL_DEFECT"}
EDITABLE_FIELDS = ("description", "context", "arguments", "return", "raise")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_pin(p: Path, expected: str, what: str) -> None:
    if sha256_file(p) != expected:
        sys.exit(f"{what} does not match its frozen hash; refusing to proceed")


def seed_from_protocol(name: str) -> int:
    """Seed derivation is anchored to the frozen protocol FILE, re-hashed at call time."""
    verify_pin(PROTOCOL, PROTOCOL_SHA, "Study-3 protocol")
    a, b = SEED_SLICES[name]
    return int(PROTOCOL_SHA[a:b], 16)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def param_names(rec: dict) -> list[str]:
    """Frozen Round-2 rule: identifiers of the def line in ground_truth.code_before."""
    for line in rec["ground_truth"]["code_before"].splitlines():
        m = re.match(r"\s*def\s+\w+\s*\((.*)\)\s*:", line)
        if m:
            return [p.split("=")[0].split(":")[0].strip() for p in m.group(1).split(",")
                    if p.strip() and p.strip() not in ("self",)]
    return []


def signature_line(rec: dict) -> str:
    for line in rec["ground_truth"]["code_before"].splitlines():
        if re.match(r"\s*def\s", line):
            return line.strip()
    return "(signature not found)"


def sprime_record(rec: dict, candidate: dict) -> dict:
    """A record whose S_t render IS the candidate S′ under constraint set C.

    Immutability by construction: function name, setup, testcases and ground_truth are
    copied from the original record object; only the five prose fields (and the optional
    security_policy) come from the writer's candidate. The writer never retypes a frozen
    component, so none can drift.
    """
    td = {"function_name": rec["task_description"]["function_name"]}
    for f in EDITABLE_FIELDS:
        td[f] = candidate["spec"][f]
    sp = candidate["spec"].get("security_policy")
    if sp is not None:
        td["security_policy"] = sp
    return {"index": rec["index"], "task_description": td,
            "unittest": {"setup": rec["unittest"]["setup"],
                         "testcases": rec["unittest"]["testcases"]},
            "ground_truth": rec["ground_truth"]}


def align_runs(key: dict, subs: dict[str, dict]) -> list[dict]:
    """One row per source case with both runs' judgements. The Study-1 alignment, verbatim
    in substance (arithmetic only; nothing adjudicated)."""
    rows = []
    for tid in sorted(key["tasks"]):
        meta = key["tasks"][tid]
        situations = meta["case_situations_source_order"]
        n = len(situations)
        j1 = {r: {e["case"]: e for e in subs[r]["tasks"][tid]["J1"]} for r in RUNS}
        for r in RUNS:
            order = meta[f"{r}_case_order"]
            if sorted(order) != list(range(n)):
                sys.exit(f"{tid}: {r} case order is not a permutation")
            if sorted(j1[r]) != list(range(1, n + 1)):
                sys.exit(f"{tid}: {r} case numbers are not 1..{n}")
        for s in range(n):
            row = {"task": tid, "source_index": s, "situation": situations[s]}
            for r in RUNS:
                pos = meta[f"{r}_case_order"].index(s) + 1
                e = j1[r][pos]
                row[f"{r}_determined"] = bool(e["determined"])
                row[f"{r}_quote"] = e.get("quote") or ""
                row[f"{r}_confidence"] = e.get("confidence")
            rows.append(row)
    return rows


def run_profile_ok(rows: list[dict], tid: str, run: str) -> bool:
    """DS per-run profile: all capability determined AND no safety determined."""
    t = [r for r in rows if r["task"] == tid]
    caps = [r for r in t if r["situation"] == "capability"]
    safs = [r for r in t if r["situation"] == "safety"]
    return (all(r[f"{run}_determined"] for r in caps)
            and not any(r[f"{run}_determined"] for r in safs))


def load_frozen_sums(sums_path: Path) -> dict[str, str]:
    return dict(line.split()[::-1]
                for line in sums_path.read_text().strip().splitlines())
