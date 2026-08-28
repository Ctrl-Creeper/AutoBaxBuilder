"""Study 3 — the one SRSWOR draw. Frozen before the formal draw is approved.

CR-1 (protocol §9): one simple random draw without replacement of N = 90 tasks from the
frozen 764-task frame. Seed = int(sha256(frozen protocol file)[0:8], 16) — the rule the
protocol itself pins; nothing else may set it. This tool reads exactly two inputs, both
hash-verified: the frozen protocol (for the seed) and the frozen frame. It imports no
benchmark record, no Study-1 artifact, and no outcome of any kind — there is nothing here
a Study-1 value could even enter through.

The formal draw runs only with --approved-formal-draw, withheld until after the tooling
freeze. Synthetic mode (--synthetic-protocol/--synthetic-frame/--out) exists for the
self-test only and refuses to touch the formal frame or the formal output path.
There is no re-draw: an existing manifest is never overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from study3_pins import (FRAME, FRAME_SHA, N_DRAW, PROTOCOL, PROTOCOL_SHA,
                         seed_from_protocol, sha256_file)

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "selection_study3.json"


def draw(frame: list[int], seed: int, n: int) -> list[int]:
    if len(frame) < n:
        sys.exit(f"frame has {len(frame)} tasks, cannot draw {n} without replacement")
    rng = np.random.default_rng(seed)
    return [int(i) for i in rng.choice(np.array(sorted(frame)), size=n, replace=False)]


def build_manifest(protocol_path: Path, protocol_sha: str, frame_path: Path,
                   frame_doc: dict, seed: int, n: int) -> dict:
    sel = draw(frame_doc["frame"], seed, n)
    return {
        "protocol": str(protocol_path.name),
        "protocol_sha256": protocol_sha,
        "frame": str(frame_path.name),
        "frame_sha256": hashlib.sha256(frame_path.read_bytes()).hexdigest(),
        "frame_size": len(frame_doc["frame"]),
        "seed": seed,
        "seed_derivation": "int(sha256(frozen protocol file)[0:8], 16)",
        "sampling": "SRSWOR, one draw; CR-1: no supplemental draw, no redraw, "
                    "no extended recruitment, whatever the eligible yield",
        "n": n,
        "selection": sel,
        "selection_sorted": sorted(sel),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--approved-formal-draw", action="store_true")
    ap.add_argument("--synthetic-protocol", type=Path)
    ap.add_argument("--synthetic-frame", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--n", type=int, default=N_DRAW,
                    help="test-only override; the formal draw is fixed at 90 by CR-1")
    a = ap.parse_args()

    synthetic = a.synthetic_protocol or a.synthetic_frame
    if synthetic:
        if not (a.synthetic_protocol and a.synthetic_frame and a.out):
            sys.exit("synthetic mode needs --synthetic-protocol, --synthetic-frame and --out")
        if a.synthetic_frame.resolve() == FRAME.resolve() or a.out.resolve() == MANIFEST.resolve():
            sys.exit("synthetic mode may not touch the formal frame or the formal manifest")
        sha = hashlib.sha256(a.synthetic_protocol.read_bytes()).hexdigest()
        frame_doc = json.loads(a.synthetic_frame.read_text())
        m = build_manifest(a.synthetic_protocol, sha, a.synthetic_frame, frame_doc,
                           int(sha[0:8], 16), a.n)
        a.out.write_text(json.dumps(m, indent=1) + "\n")
        print(f"synthetic draw: n={m['n']} seed={m['seed']} -> {a.out}")
        return

    if not a.approved_formal_draw:
        sys.exit("The formal 764->90 draw is not yet approved. This tool runs only with "
                 "--approved-formal-draw, granted after the tooling freeze is accepted.")
    if a.n != N_DRAW:
        sys.exit("CR-1 fixes the formal draw at N=90; --n is for synthetic tests only")
    if MANIFEST.exists():
        sys.exit("selection_study3.json already exists; there is no re-draw under CR-1")

    seed = seed_from_protocol("srswor_draw")  # verifies the protocol pin
    if sha256_file(FRAME) != FRAME_SHA:
        sys.exit("frame does not match its frozen hash; refusing to draw")
    frame_doc = json.loads(FRAME.read_text())

    m = build_manifest(PROTOCOL, PROTOCOL_SHA, FRAME, frame_doc, seed, N_DRAW)
    MANIFEST.write_text(json.dumps(m, indent=1) + "\n")
    print(f"formal draw complete: n=90 seed={seed}")
    print(f"selection manifest sha256 {sha256_file(MANIFEST)} — freeze this hash")


if __name__ == "__main__":
    main()
