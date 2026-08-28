"""Study 3 — baseline packet builder (original S_t of the 90 drawn tasks).

Two content sources, both verified: the frozen Study-3 selection manifest — whose draw is
RE-DERIVED here from the frozen protocol seed and frozen frame and asserted equal, a check
stronger than a pinned hash — and the original benchmark records it points to. Nothing else
is read. In particular this builder never reads Study-1 outcomes, Round-2 judgements, or any
writer/S′ artifact: it measures the benchmark as shipped, exactly as the Study-1 builder did,
and the data-flow audit holds it to that boundary mechanically.

The formal build runs only with --approved-packet-build, withheld until the formal draw is
frozen. Baseline eligibility is NOT computed here — it is derived only after both baseline
submissions are independently frozen (derive_eligibility.py).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from select_study3_sample import draw
from study3_pins import (FRAME, FRAME_SHA, N_DRAW, SCHEMA_BASELINE, seed_from_protocol,
                         sha256_file, verify_pin)
from packet_build import build_packages

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "selection_study3.json"


def main() -> None:
    if "--approved-packet-build" not in sys.argv:
        sys.exit("The formal baseline packet build is not yet approved. This builder runs "
                 "only with --approved-packet-build.")
    if (HERE / "baseline" / "run1_package").exists():
        sys.exit("baseline/run1_package already exists; a frozen build is never overwritten")

    manifest = json.loads(MANIFEST.read_text())
    verify_pin(FRAME, FRAME_SHA, "Study-3 frame")
    frame_doc = json.loads(FRAME.read_text())
    rederived = draw(frame_doc["frame"], seed_from_protocol("srswor_draw"), N_DRAW)
    if manifest["selection"] != rederived:
        sys.exit("selection manifest does not reproduce from the frozen protocol seed and "
                 "frame; refusing to build")

    from secodeplt_task_runner import load  # noqa: E402  (benchmark loader only)
    records = {r["index"]: r for r in load(only_stdlib=False)}

    key = build_packages(
        records, manifest["selection"], HERE / "baseline",
        schema_version=SCHEMA_BASELINE,
        task_seed_name="baseline_task_order",
        run_seed_names={"run1": "baseline_run1_cases", "run2": "baseline_run2_cases"},
        key_extra={"stage": "baseline",
                   "selection_manifest_sha256": sha256_file(MANIFEST)})
    n_cases = sum(len(v["case_situations_source_order"]) for v in key["tasks"].values())
    print(f"baseline packets built: {len(key['tasks'])} tasks, {n_cases} cases")
    print(f"payload sha {key['canonical_payload_sha256']['run1'][:16]}… (identical across runs)")


if __name__ == "__main__":
    main()
