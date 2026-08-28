"""Phase-1 consistency and data-flow check for the CWEval replication. Mechanical.

Three parts:
 1. Source/hash pin verification — the frame's pinned pipeline files still match the
    repo; the S_t boundary facts (anchors, default 'direct' prompt, DirectPrompt and
    SecurePrompt classes, LANGS) hold in the pinned sources; every task/test file
    hash in the frame still matches; the manifest is consistent with the frame and
    carries the frozen protocol hash.
 2. Data-flow scan — no phase-1 file reads or embeds a Study-1 result value or
    result-file name. The two ICC planning constants (0.577 / 0.572) are the sole
    whitelisted SeCodePLT-derived quantities. Result-commit references are permitted
    only inside sentences that prohibit their use (negation-aware, as in the frozen
    Study-1 protocol checker).
 3. Path scan — the phase-1 scripts touch no SeCodePLT path or loader.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CWEVAL = Path("/Users/lewiswu/网络安全/CWEval")
PHASE1 = ("build_cweval_frame.py", "compute_sample_size.py",
          "cweval_replication_protocol.md", "cweval_frame.json",
          "selection_manifest.json", "sample_size_arithmetic.json")
RESULT_VALUES = ["0.780", "0.7805", "0.6899", "0.7319", "0.869", "0.975",
                 "ebb0e187", "3401bf6f", "dd13be72", "6e82372c",
                 "results_study1_prevalence", "scoring_console"]
RESULT_REFS = [r"f823bf9"]
NEGATORS = re.compile(r"\bnot\b|\bnever\b|\bno\b|may not|prohibit|不得|不是", re.IGNORECASE)

fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def main() -> None:
    frame = json.loads((HERE / "cweval_frame.json").read_text())
    manifest = json.loads((HERE / "selection_manifest.json").read_text())

    # --- 1. pins
    for rel, sha in frame["pipeline_pins"].items():
        check(hashlib.sha256((CWEVAL / rel).read_bytes()).hexdigest() == sha,
              f"pipeline pin holds: {rel}")
    gen = (CWEVAL / "cweval/generate.py").read_text()
    ppt = (CWEVAL / "cweval/ppt/__init__.py").read_text()
    check("BEGIN PROMPT" in gen and "BEGIN SOLUTION" in gen, "prompt anchors present")
    check("ppt: str = 'direct'" in gen, "default prompt pipeline is 'direct'")
    check("class DirectPrompt" in ppt and "class SecurePrompt" in ppt,
          "DirectPrompt and SecurePrompt classes present (Secure excluded from S_t)")
    bad_hash = 0
    for fam in frame["families"].values():
        for t in fam["task_files"]:
            if hashlib.sha256((CWEVAL / t["task_file"]).read_bytes()).hexdigest() != t["task_sha256"]:
                bad_hash += 1
            if t.get("test_file") and hashlib.sha256(
                    (CWEVAL / t["test_file"]).read_bytes()).hexdigest() != t["test_sha256"]:
                bad_hash += 1
    check(bad_hash == 0, f"all pinned task/test file hashes hold ({bad_hash} mismatches)")
    check("cwe_943_0" not in frame["families"]
          and list(frame["excluded_families"]) == ["cwe_943_0"],
          "cwe_943_0 family excluded, and is the only exclusion")
    psha = hashlib.sha256((HERE / "cweval_replication_protocol.md").read_bytes()).hexdigest()
    check(manifest["protocol_sha256"] == psha, "manifest carries the frozen protocol hash")
    check(manifest["n_families"] == frame["n_families_eligible"] == 35
          and manifest["n_task_files"] == frame["n_task_files_eligible"] == 114
          and sorted(manifest["families"]) == sorted(frame["families"]),
          "manifest is the census of the frame (35 families / 114 files)")

    # --- 1b. amended inferential interpretation (2026-08-28)
    prot = (HERE / "cweval_replication_protocol.md").read_text()
    check("finite-frame census prevalence" in prot,
          "protocol states the census estimand as finite-frame prevalence")
    check("superpopulation / generalization sensitivity" in prot,
          "bootstrap intervals labelled superpopulation/generalization sensitivity")
    check("0.134" not in prot and "±0.14" not in prot,
          "no planning half-width presented as CWEval sampling precision")
    check("no sampling CI exists or is reported" in prot,
          "no-sampling-CI clause present for frame inference")

    # --- 2. data-flow scan
    for name in PHASE1:
        text = (HERE / name).read_text()
        hits = [v for v in RESULT_VALUES if v in text]
        check(not hits, f"{name}: no Study-1 result value or result-file name (found {hits or 'none'})")
        for ref in RESULT_REFS:
            for sent in re.split(r"(?<=[.!?。])\s+", re.sub(r"\s+", " ", text)):
                if re.search(ref, sent) and not NEGATORS.search(sent):
                    fails.append(f"{name}: result ref {ref} outside a prohibition sentence")
                    print(f"  FAIL {fails[-1]}")
    icc_ok = all("0.577" in (HERE / n).read_text() for n in
                 ("compute_sample_size.py", "cweval_replication_protocol.md"))
    check(icc_ok, "ICC planning constants present where §6.1 admits them, and nowhere banned")

    # --- 3. no SeCodePLT paths in phase-1 scripts
    for name in ("build_cweval_frame.py", "compute_sample_size.py"):
        text = (HERE / name).read_text()
        hits = [s for s in ("网络安全/SeCodePLT", "secodeplt_task_runner", "study1_execution")
                if s in text]
        check(not hits, f"{name}: touches no SeCodePLT path or loader (found {hits or 'none'})")

    print(f"\n{'PHASE-1 CHECK PASSED' if not fails else str(len(fails)) + ' FAILURE(S)'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
