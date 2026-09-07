"""Sole authoritative accepted-writer input for Study-3 construction.

GAP-7 fixes the accepted-input interface to Writer Run 2. There is no path argument,
fallback, directory scan, or existence-based selection: callers receive exactly the
hash-pinned ACCEPT_FIRST_RUN2 artifact or the process hard-stops.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from study3_pins import load_frozen_sums, sha256_file

HERE = Path(__file__).resolve().parent
WRITER_DIR = HERE / "writer_handoff"
RUN2_MANIFEST = "SHA256SUMS_WRITER_FROZEN_RUN2"
ACCEPTED_REL = Path("submissions/writer_output_ACCEPT_FIRST_RUN2.json")
ACCEPTED_SHA256 = "f2b0e73ab1d8b5efcb22bb53c2b8d026446994992195d9b55b483d8de593b49e"


def load_authoritative_writer() -> dict:
    """Load only the frozen Run-2 accepted artifact after two matching hash checks."""
    manifest_path = WRITER_DIR / RUN2_MANIFEST
    try:
        frozen = load_frozen_sums(manifest_path)
    except (OSError, ValueError):
        sys.exit("HARD STOP — Run-2 writer terminal manifest is missing")

    rel = str(ACCEPTED_REL)
    if frozen.get(rel) != ACCEPTED_SHA256:
        sys.exit("HARD STOP — Run-2 writer terminal manifest does not pin the "
                 "authoritative accepted artifact hash")

    accepted_path = WRITER_DIR / ACCEPTED_REL
    if not accepted_path.is_file():
        sys.exit("HARD STOP — authoritative Run-2 accepted writer artifact is missing")
    if sha256_file(accepted_path) != ACCEPTED_SHA256:
        sys.exit("HARD STOP — authoritative Run-2 accepted writer artifact hash mismatch")
    return json.loads(accepted_path.read_text())
