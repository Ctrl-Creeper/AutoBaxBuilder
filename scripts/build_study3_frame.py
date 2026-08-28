"""Build the Study-3 sampling frame mechanically from frozen manifests.

Frame = Round-2 frame (864) minus (Study-1/Round-2 selection 90) minus (ordered reserve 10)
minus (IDR1 12) minus (feasibility 12). The latter two are already outside the 864 (they sit in
the Round-2 exclusion log); the subtraction is verified idempotent, not assumed. No benchmark
content is read; only frozen index manifests. Output is deterministic (sorted lists, fixed
serialization), so its SHA256 is reproducible.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEL_DIR = ROOT / "docs/preregistration/2026-08-25_round2_selection"
FEAS = ROOT / "docs/preregistration/2026-08-24_instrument_feasibility/selection.json"
OUT = ROOT / "docs/preregistration/2026-08-28_study3_frame.json"

EXPECTED_FRAME_SHA_PREFIX = "3840d50f"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    frame_doc = json.loads((SEL_DIR / "round2_sampling_frame.json").read_text())
    sel_doc = json.loads((SEL_DIR / "round2_selection.json").read_text())
    exl_doc = json.loads((SEL_DIR / "round2_exclusion_log.json").read_text())
    feas_doc = json.loads(FEAS.read_text())

    frame = set(frame_doc["frame"])
    assert len(frame) == 864 == frame_doc["frame_size"], "frame size mismatch"
    assert sel_doc["frame_sha256"].startswith(EXPECTED_FRAME_SHA_PREFIX), "frame sha mismatch"

    s90 = set(sel_doc["selection"])
    r10 = set(sel_doc["reserve_ordered"])
    idr1 = {e["index"] for e in exl_doc
            if e["reason"] == "development: Instrument Development Round 1"}
    feas = {s["index"] for s in feas_doc["selection"]}

    assert len(s90) == 90 and len(r10) == 10 and not (s90 & r10)
    assert len(idr1) == 12 and len(feas) == 12
    assert idr1 == feas, "IDR1 and feasibility manifests must be index-identical"
    assert s90 <= frame and r10 <= frame
    assert not (idr1 & frame), "IDR1/feasibility must already be outside the 864 frame"

    exclusion = sorted(s90 | r10 | idr1 | feas)
    study3_frame = sorted(frame - s90 - r10 - idr1 - feas)
    assert len(study3_frame) == 864 - 90 - 10 == 764

    out = {
        "built_from": {
            "round2_sampling_frame.json": sha(SEL_DIR / "round2_sampling_frame.json"),
            "round2_selection.json": sha(SEL_DIR / "round2_selection.json"),
            "round2_exclusion_log.json": sha(SEL_DIR / "round2_exclusion_log.json"),
            "feasibility_selection.json": sha(FEAS),
        },
        "rule": "864 frame minus selection-90 minus reserve-10 minus IDR1-12 minus "
                "feasibility-12; IDR1 == feasibility and both already outside the 864 "
                "(idempotent, applied anyway); fixed at freeze, no substitution ever",
        "exclusion_list": exclusion,
        "frame_size": len(study3_frame),
        "frame": study3_frame,
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"study3 frame: {len(study3_frame)} tasks; exclusions {len(exclusion)}")
    print(f"wrote {OUT.name}  sha256 {sha(OUT)}")


if __name__ == "__main__":
    main()
