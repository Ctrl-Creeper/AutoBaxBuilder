"""Round-2 calibration selection under frozen protocol v2 (`4ca61b25…`).

Selection only. No specification is authored, nothing is coded, no model is queried.

Two rules govern what may enter this file.

**Eligibility is static.** A task's eligibility is decided from its stored fields
and from whether its case list can be extracted — never from running the
implementations. In particular the Round-1 filter, which required the benchmark's
patched and vulnerable references to behave as designed, is NOT used here: that is
a property of the vulnerable/patched behaviour, and protocol v2's selection rules
forbid conditioning entry on it. Round 2 needs no execution anyway; J1-J3 are
judgements over text.

**Nothing that could leak Axis 1 touches the draw.** No security vocabulary, no
Round-1 stratum, no assessment of whether `security_policy` suffices to blind, no
suspicion about setup globals or signature parameters, no separability judgement.
These are the phenomena under study and must not influence the probability of
entering the sample.

Sampling is simple random without replacement. Stratification is available under
C7 but is not used: the estimand is agreement between two coding runs, not
prevalence within any metadata cell, so nothing here needs balancing, and
stratifying on exogenous metadata would buy no precision for that estimand while
adding a researcher choice.

The seed is not chosen. It is derived from the frozen protocol's own hash, so it
could not have been picked to produce a particular draw.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from secodeplt_task_runner import load  # noqa: E402

OUT = Path("docs/preregistration/2026-08-25_round2_selection")
PROTOCOL_SHA = "4ca61b25973be20beec9cad085a7da503d600fdb7f427eb0e4251c3e02eb45da"
N_SAMPLE = 90
N_RESERVE = 10

# Excluded because they took part in developing protocol v1 or v2.
IDR1 = [666, 813, 1364, 643, 1083, 681, 1072, 1067, 893, 1350, 816, 434]
INSPECTED = {
    45: "structure_inspection",
    150: "description_vs_safety_sample",
    484: "description_vs_safety_sample",
    913: "policy_vs_safety_sample",
    971: "policy_vs_safety_sample",
    1068: "policy_vs_safety_sample",
    1233: "description_vs_safety_sample",
    1341: "policy_vs_safety_sample",
}

_DUMP = '\nimport json\nprint("###" + json.dumps({k: len(v) for k, v in testcases.items()}))\n'
REQUIRED_FIELDS = ("function_name", "description", "context", "arguments", "return", "raise")


def cases_extractable(rec: dict) -> bool:
    """Executes the setup and the testcases block only. No implementation is run."""
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "c.py"
        f.write_text(rec["unittest"]["setup"] + "\n" + rec["unittest"]["testcases"] + _DUMP)
        try:
            out = subprocess.run([sys.executable, str(f)], cwd=t, capture_output=True,
                                 text=True, timeout=30).stdout
        except subprocess.TimeoutExpired:
            return False
    if "###" not in out:
        return False
    counts = json.loads(out.split("###", 1)[1])
    return counts.get("capability", 0) > 0 and counts.get("safety", 0) > 0


def eligibility(rec: dict) -> str | None:
    """Return the exclusion reason, or None if eligible. Static checks first."""
    idx = rec["index"]
    if idx in IDR1:
        return "development: Instrument Development Round 1"
    if idx in INSPECTED:
        return f"development: inspected while drafting the protocol ({INSPECTED[idx]})"
    if not rec["unittest"].get("testcases", "").strip():
        return "structure: no testcases block"
    td = rec["task_description"]
    missing = [f for f in REQUIRED_FIELDS if f not in td]
    if missing:
        return f"structure: task_description missing {missing}"
    if "def " not in rec["ground_truth"].get("code_before", ""):
        return "structure: no function signature in code_before"
    if not cases_extractable(rec):
        return "structure: case list not extractable, or lacks both case kinds"
    return None


# Two criteria were considered and rejected before the draw, recorded because
# rejecting them changed the frame:
#
#   "setup block must be non-empty" — 52 tasks have an empty setup. Excluding them
#   would remove, wholesale, the tasks that cannot possibly carry an obligation in
#   the preamble: one side of the phenomenon under study. That is exactly the
#   conditioning protocol v2 forbids.
#
#   "install_requires must be empty" — Round 2 executes no implementation, so a
#   third-party dependency blocks nothing by itself, and the criterion correlates
#   with CWE family. Where a dependency does block case extraction, the extraction
#   check already catches it and records the cause.


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = load(only_stdlib=False)

    frame, excluded = [], []
    for rec in sorted(records, key=lambda r: r["index"]):
        reason = eligibility(rec)
        (excluded if reason else frame).append(
            {"index": rec["index"], "reason": reason} if reason else rec["index"]
        )

    frame_digest = hashlib.sha256(json.dumps(frame).encode()).hexdigest()

    # --- everything above is recorded before the draw; the seed is derived, not chosen
    seed = int(PROTOCOL_SHA[:8], 16)
    rng_meta = {
        "library": f"numpy {np.__version__}",
        "generator": "numpy.random.default_rng",
        "bit_generator": "PCG64",
        "seed": seed,
        "seed_derivation": f"int(protocol_sha256[:8], 16) with protocol_sha256={PROTOCOL_SHA}",
        "python": platform.python_version(),
        "procedure": ("permute the index-sorted frame once with default_rng(seed).permutation; "
                      f"take the first {N_SAMPLE} as the sample and the next {N_RESERVE} as the "
                      "ordered reserve. Single draw, no reroll."),
    }

    order = np.random.default_rng(seed).permutation(len(frame))
    selection = [int(frame[i]) for i in order[:N_SAMPLE]]
    reserve = [int(frame[i]) for i in order[N_SAMPLE:N_SAMPLE + N_RESERVE]]

    manifest = {
        "protocol": PROTOCOL_SHA,
        "frame_size": len(frame),
        "frame_sha256": frame_digest,
        "excluded_count": len(excluded),
        "sampling": "simple random without replacement; no stratification",
        "rng": rng_meta,
        "n_selected": len(selection),
        "selection": selection,
        "reserve_ordered": reserve,
        "reserve_activation": {
            "allowed_only_for": [
                "packet construction raises an exception (case extraction or witness assembly fails)",
                "the specification or witness cannot be rendered into the packet (encoding failure)",
                "a duplicate index is discovered in the selection after freezing",
            ],
            "forbidden_for": [
                "coding difficulty", "any classification outcome", "coder disagreement",
                "any judgement about the task's content, its security rule, or its separability",
            ],
            "order": "strictly the order listed in reserve_ordered; no choosing among reserves",
            "recording": ("each activation is logged with the mechanical failure that triggered it; "
                          "if no reserve is available the task is recorded as a processing failure "
                          "and the achieved n is reported as-is"),
        },
    }

    (OUT / "round2_sampling_frame.json").write_text(json.dumps({
        "protocol": PROTOCOL_SHA, "frame_size": len(frame),
        "frame_sha256": frame_digest, "frame": frame}, indent=2))
    (OUT / "round2_exclusion_log.json").write_text(json.dumps(excluded, indent=2, ensure_ascii=False))
    (OUT / "round2_selection.json").write_text(json.dumps(manifest, indent=2))

    from collections import Counter
    reasons = Counter(e["reason"].split(":")[0] + ": " + e["reason"].split(": ", 1)[1].split(" (")[0]
                      for e in excluded)
    print(f"records considered      {len(records)}")
    print(f"excluded                {len(excluded)}")
    for r, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"    {n:>4}  {r}")
    print(f"sampling frame          {len(frame)}   sha256 {frame_digest[:16]}…")
    print(f"seed                    {seed}  (derived from protocol hash)")
    print(f"selected                {len(selection)}   reserve {len(reserve)}")


if __name__ == "__main__":
    main()
