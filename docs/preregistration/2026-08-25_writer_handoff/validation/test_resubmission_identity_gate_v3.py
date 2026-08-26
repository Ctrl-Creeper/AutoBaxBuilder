"""Self-test for resubmission identity gate v3, including substitution probes.

v3 removes A4.2's fragment-survival guard. That guard was the only thing in the gate
aimed specifically at substitution, so before freezing v3 the question has to be
answered empirically rather than argued: **can a quotation now be swapped for a
different real clause and survive?**

Two probes, both using text that genuinely exists in the frozen input, so neither is
caught by A4.2's exact-presence condition:

  S1  the quotation is replaced by another real clause from the *same* field
  S2  the quotation is replaced by a real clause from a *different* field

Each probe is run through gate v3 **and** through the frozen writer validator,
because the claim under test is about the pipeline, not about either layer alone.
If S1 survives both, that is recorded as a limitation of A4.2 rather than patched
with an invented similarity rule.

Run:  python test_resubmission_identity_gate_v3.py
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE3 = HERE / "resubmission_identity_gate_v3.py"
VALIDATOR = HERE / "validate_writer_output.py"
SUB = HERE.parent / "submissions"
TASKS = HERE.parent / "writer_package/tasks"
LIVE = Path("/Users/lewiswu/网络安全/writer_package/writer_output.json")
sys.path.insert(0, str(HERE))
from validate_writer_output import norm, parse_original, sentences  # noqa: E402


def flagged_quote() -> set:
    msgs = json.loads((SUB / "writer_validator_report_on_resubmission1.json").read_text())["hard_failures"]
    return {(g.group(1), int(g.group(2))) for m in msgs
            if "the quoted original is not present in the frozen" in m
            for g in [re.match(r"(W\d\d) edit (\d+)", m)] if g}


def run(tool: Path, sub: dict) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(sub, f, ensure_ascii=False)
        p = f.name
    r = subprocess.run([sys.executable, str(tool), p], capture_output=True, text=True)
    Path(p).unlink()
    return r.returncode, r.stdout + r.stderr


def pipeline(sub: dict) -> tuple[bool, bool]:
    """(gate v3 accepted, frozen validator accepted)"""
    g, _ = run(GATE3, sub)
    v, _ = run(VALIDATOR, sub)
    return g == 0, v == 0


def main() -> None:
    base = json.loads(LIVE.read_text())
    fq = flagged_quote()

    print("baseline — the submission as received")
    g, v = pipeline(base)
    print(f"  gate v3 {'PASS' if g else 'FAIL'}   frozen validator {'PASS' if v else 'FAIL'}")
    failures = 0 if g else 1
    if not g:
        print("  FAIL the submission should now clear gate v3")

    # --- choose a flagged entry whose field holds more than one clause
    target = None
    for wid, i in sorted(fq):
        orig = parse_original((TASKS / f"{wid}.md").read_text())
        f = base["tasks"][wid]["edits"][i - 1]["field"]
        others = [s for s in sentences(orig.get(f, ""))
                  if norm(s) and norm(s) not in norm(base["tasks"][wid]["edits"][i - 1]["original"])
                  and len(s) > 25]
        if others:
            target = (wid, i, f, others[0], orig)
            break
    if not target:
        sys.exit("no flagged entry has a second clause in its field; probes cannot be built")
    wid, i, field, other_clause, orig = target
    print(f"\nprobe target: {wid} edit {i}, field {field!r}")

    print("\nS1 — quotation swapped for another real clause in the SAME field")
    s1 = copy.deepcopy(base)
    s1["tasks"][wid]["edits"][i - 1]["original"] = other_clause
    g1, v1 = pipeline(s1)
    print(f"  substituted text: {other_clause[:70]!r}")
    print(f"  gate v3 {'PASS' if g1 else 'BLOCKED'}   frozen validator {'PASS' if v1 else 'BLOCKED'}")
    blocked1 = not (g1 and v1)
    print(f"  {'ok   blocked by the pipeline' if blocked1 else 'NOT BLOCKED — a limitation, not a bug to patch'}")

    print("\nS2 — quotation swapped for a real clause from a DIFFERENT field")
    other_field = next(f for f in ("description", "return", "raise", "arguments")
                       if f != field and sentences(orig.get(f, "")))
    foreign = max(sentences(orig[other_field]), key=len)
    s2 = copy.deepcopy(base)
    s2["tasks"][wid]["edits"][i - 1]["original"] = foreign
    g2, v2 = pipeline(s2)
    print(f"  substituted text (from {other_field!r}): {foreign[:70]!r}")
    print(f"  gate v3 {'PASS' if g2 else 'BLOCKED'}   frozen validator {'PASS' if v2 else 'BLOCKED'}")
    blocked2 = not (g2 and v2)
    print(f"  {'ok   blocked by the pipeline' if blocked2 else 'NOT BLOCKED'}")

    print("\ncarried-over negatives from v2, re-run against v3")
    from test_resubmission_identity_gate_v2 import negatives, positive, prev
    p = prev()
    for name, sub in negatives(p, positive(p)).items():
        code, _ = run(GATE3, sub)
        good = code == 1
        print(f"  {'ok  ' if good else 'FAIL'} {name}")
        failures += 0 if good else 1

    if not blocked1:
        print("\nRECORDED LIMITATION: with the fragment guard removed, A4.2 cannot by itself "
              "distinguish completing a quotation from swapping it for another real clause in "
              "the same field. Not patched here.")
    print(f"\n{'SELF-TEST PASSED' if not failures else str(failures) + ' FAILURES'}")
    print(f"substitution probes: S1 {'blocked' if blocked1 else 'NOT blocked'}, "
          f"S2 {'blocked' if blocked2 else 'NOT blocked'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
