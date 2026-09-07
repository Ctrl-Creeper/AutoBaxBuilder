"""Study 3 — Run-2 writer package mechanical diff audit (GAP-6 repair gate).

Run2 writer-visible package − Run1 writer-visible package. The only licensed difference
is INSTRUCTIONS.md, and its new bytes must equal the frozen GAP-6 repair diff applied to
the Run-1 bytes. Any other file added, removed or changed → HARD STOP (exit 1). The
sealed key must be byte-identical (same 53 tasks, same W-id mapping). Report carries
hashes and counts only.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from study3_pins import sha256_file

HERE = Path(__file__).resolve().parent
RUN1 = HERE / "writer_handoff/run1_writer_package"
RUN2 = HERE / "writer_handoff/writer_package"
DIFF = HERE / "GAP6_proposed_repair.diff"
KEY = HERE / "writer_handoff/sealed/_KEY_DO_NOT_SHOW_WRITER.json"
RUN1_KEY_SHA = "3c9fc2925dd0511af5be6ebf27d2c1bf4ce6ab5b6d89937c5b74bffc73475106"
DIFF_SHA = "cd6ae5f9959b26c0f1bee72fe3e92cbb487cb13bd161df8c18d3a8ea928af482"


def files(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): sha256_file(p) for p in sorted(root.rglob("*")) if p.is_file()}


def main() -> None:
    if sha256_file(DIFF) != DIFF_SHA:
        sys.exit("HARD STOP — repair diff is not the frozen GAP-6 diff")
    r1, r2 = files(RUN1), files(RUN2)
    added, removed = sorted(set(r2) - set(r1)), sorted(set(r1) - set(r2))
    changed = sorted(k for k in r1.keys() & r2.keys() if r1[k] != r2[k])

    with tempfile.TemporaryDirectory() as td:
        wp = Path(td) / "writer_package"
        wp.mkdir()
        (wp / "INSTRUCTIONS.md").write_bytes((RUN1 / "INSTRUCTIONS.md").read_bytes())
        subprocess.run(["patch", "-p1", "-s"], cwd=td, stdin=DIFF.open("rb"), check=True)
        expected = (wp / "INSTRUCTIONS.md").read_bytes()
    instructions_ok = expected == (RUN2 / "INSTRUCTIONS.md").read_bytes()

    report = {
        "run1_files": len(r1), "run2_files": len(r2),
        "added": added, "removed": removed, "changed": changed,
        "instructions_run1_sha256": r1.get("INSTRUCTIONS.md"),
        "instructions_run2_sha256": r2.get("INSTRUCTIONS.md"),
        "instructions_equals_patch_of_run1": instructions_ok,
        "sealed_key_sha256": sha256_file(KEY),
        "sealed_key_unchanged": sha256_file(KEY) == RUN1_KEY_SHA,
        "n_tasks": sum(1 for k in r2 if k.startswith("tasks/")),
    }
    ok = (not added and not removed and changed == ["INSTRUCTIONS.md"]
          and instructions_ok and report["sealed_key_unchanged"] and report["n_tasks"] == 53)
    report["verdict"] = "ONLY_LICENSED_DIFFERENCES" if ok else "HARD_STOP_UNLICENSED_DIFFERENCE"
    (HERE / "run2_package_diff_audit.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
