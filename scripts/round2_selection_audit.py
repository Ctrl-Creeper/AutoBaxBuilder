"""Procedural audit of the Round-2 selection.

Checks only that the draw was carried out correctly. It deliberately computes
nothing about what was drawn: no CWE distribution, no case counts, no property
that bears on Axis 1 or on any Round-2 outcome. Protocol v2's selection rules put
those off limits at this stage, and a "balance check" is the usual route by which
a draw gets quietly rerolled.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

OUT = Path("docs/preregistration/2026-08-25_round2_selection")
IDR1 = {666, 813, 1364, 643, 1083, 681, 1072, 1067, 893, 1350, 816, 434}
INSPECTED = {45, 150, 484, 913, 971, 1068, 1233, 1341}

man = json.loads((OUT / "round2_selection.json").read_text())
frame_doc = json.loads((OUT / "round2_sampling_frame.json").read_text())
frame, sel, res = frame_doc["frame"], man["selection"], man["reserve_ordered"]

fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


check(len(sel) == 90, f"selection contains exactly 90 tasks (found {len(sel)})")
check(len(set(sel)) == len(sel), "all selected ids are unique")
check(set(sel) <= set(frame), "every selected id is drawn from the recorded frame")
check(not (set(sel) & IDR1), "zero overlap with Instrument Development Round 1")
check(not (set(sel) & INSPECTED), "zero overlap with tasks inspected while drafting the protocol")
check(not (set(sel) & set(res)), "reserve is disjoint from the selection")
check(len(set(res)) == len(res) and set(res) <= set(frame), "reserve ids are unique and from the frame")

check(hashlib.sha256(json.dumps(frame).encode()).hexdigest() == frame_doc["frame_sha256"],
      "recorded frame hash matches the frame as stored")

# --- the draw must be reconstructible from the recorded metadata alone
seed = man["rng"]["seed"]
check(seed == int(man["protocol"][:8], 16), "seed is the recorded derivation of the protocol hash")
order = np.random.default_rng(seed).permutation(len(frame))
check([int(frame[i]) for i in order[:90]] == sel, "selection reproduces from seed and frame")
check([int(frame[i]) for i in order[90:100]] == res, "reserve reproduces from seed and frame")
check(man["rng"]["bit_generator"] == "PCG64" and np.__version__ in man["rng"]["library"],
      f"generator and library version as recorded (numpy {np.__version__})")

check(man["frame_size"] == len(frame), "recorded frame size matches the frame")
check(bool(man["reserve_activation"]["allowed_only_for"]) and
      bool(man["reserve_activation"]["forbidden_for"]),
      "reserve activation conditions are recorded, both permitted and forbidden")

print(f"\n{'AUDIT PASSED' if not fails else str(len(fails)) + ' FAILURES'}")
sys.exit(1 if fails else 0)
