"""Consistency check run before freezing protocol v2.

Checks claims the protocol makes about itself, and cross-document agreement with
the sensitivity analysis it cites. Textual where the claim is textual; structural
where the claim is structural. Exit non-zero on any failure.
"""

from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path

D = Path("docs/preregistration")
V1 = (D / "2026-08-25_instrument_validation_protocol.md").read_text()
V2 = (D / "2026-08-25_instrument_validation_protocol_v2.md").read_text()
SENS = (D / "round2_sample_size_sensitivity.md").read_text()

fails: list[str] = []
notes: list[str] = []


def check(ok: bool, msg: str) -> None:
    (notes if ok else fails).append(msg)


# 1. v2 claims Definition D's operative wording is unchanged. It inherits D by
#    reference rather than restating it, so the claim holds iff v2 contains no
#    competing definition. Both halves are checked.
DEFN = r"\*S\* \*\*determines\*\* \*b\* at \*i\* iff(.*?)identifiable sentence of \*S\*"


def defn_d(text: str) -> str:
    m = re.search(DEFN, text, re.S)
    return re.sub(r"[\s*`>]+", " ", m.group(1)).strip() if m else ""


check(bool(defn_d(V1)), "Definition D located in v1")
check(not defn_d(V2),
      "v2 does not restate Definition D, so its 'operative wording unchanged' claim cannot conflict")
check("Definition D and its two requirements" in V2,
      "v2 lists Definition D among the clauses carried over unchanged")

# 2. The C3 classification table must cover every reachable combination.
rows = re.findall(r"^\| (yes|no) \| (yes|no|—) \| (yes|no|—) \| \*\*([A-Z -]+)\*\*", V2, re.M)
covered = {(a, b, c) for a, b, c, _ in rows}


def matches(combo, pattern):
    return all(p == "—" or p == v for v, p in zip(combo, pattern))


uncovered = [
    c for c in itertools.product(("yes", "no"), repeat=3)
    if not any(matches(c, p) for p in (r[:3] for r in rows))
]
check(len(rows) == 5, f"C3 table has 5 rows (found {len(rows)})")
check(not uncovered, f"C3 table covers every J1/J1/J3 combination (uncovered: {uncovered})")

# 3. Sample size is stated as fixed. "minimum"/"floor" may appear only inside an
#    explicit negation of it, so each occurrence is checked in context.
def unnegated(txt: str, pattern: str, window: int = 40) -> list[str]:
    out = []
    for m in re.finditer(pattern, txt, re.I):
        before = txt[max(0, m.start() - window):m.start()].lower()
        if not re.search(r"\bnot?\b|\bnever\b|forbid", before):
            out.append(txt[max(0, m.start() - window):m.end()].replace("\n", " "))
    return out


for name, txt in (("v2", V2), ("sensitivity", SENS)):
    bad = unnegated(txt, r"at least 90|minimum|\bfloor\b")
    check(not bad, f"{name}: 'minimum/floor' appears only inside a negation (offending: {bad})")
check("No augmentation" in V2 and "forbids augmentation" in SENS,
      "both documents state that augmentation is forbidden")

# 4. No pass/fail threshold language survives.
THRESH = r"pass/fail threshold|clears? (?:the|that) threshold|fails the substantial|substantial-agreement threshold|the threshold the round"
for name, txt in (("v2", V2), ("sensitivity", SENS)):
    hits = unnegated(txt, THRESH, window=60)
    check(not hits, f"{name}: threshold framing appears only inside a negation (offending: {hits})")
check("planning reference value" in V2 and "planning reference value" in SENS,
      "both documents label κ=0.60 a planning reference value")

# 5. C8: pooled κ must be scoped to the DGP, never claimed as a general upper bound.
check("upper bound" not in V2, "v2: the general 'upper bound' claim for pooled κ is gone")
check("descriptive sensitivity statistic" in V2, "v2: pooled κ is a descriptive sensitivity statistic")
check("prespecified simulation DGP" in V2 or "under this DGP" in V2.lower(),
      "v2: the bias observation is scoped to the simulation DGP")
check("task-cluster-aware" in V2 and "cluster bootstrap" in V2,
      "v2: primary inference is cluster-aware with a task-level cluster bootstrap")

# 6. C9: the reliability metric set is complete, and AC1 is fenced off from κ's scales.
for term in ("Gwet's AC1", "raw agreement", "quote / evidence concordance", "tie-break rate"):
    check(term in V2, f"v2: C9 names {term}")
check("not interpreted against Cohen" in V2, "v2: AC1 is fenced off from Cohen κ's verbal thresholds")

# 7. Numbers agree across documents.
for n in ("88", "90", "840", "10.7%", "0.10"):
    check(n in V2 and n in SENS, f"figure {n} appears in both documents")

# 8. Retained items from the previous revision.
check("STRUCTURALLY CARRIED" in V2 and "INSEPARABLE" in V2, "both structural classes retained")
check("independent blinded coding runs" in V2, "C5 independence wording retained")
for c in range(1, 10):
    check(f"### C{c} —" in V2, f"clause C{c} present")

# 9. Status must be exactly one of draft or frozen, never ambiguous. Both states
#    are valid; the check exists so the document cannot be silently promoted.
draft, frozen = "Status: **DRAFT.**" in V2, "Status: **FROZEN" in V2
check(draft ^ frozen, f"status is unambiguous (draft={draft}, frozen={frozen})")
if frozen:
    notes.append("v2 is frozen; re-running this check verifies the frozen text still holds together")

for n in notes:
    print(f"  ok   {n}")
for f in fails:
    print(f"  FAIL {f}")
print(f"\n{len(notes)} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
