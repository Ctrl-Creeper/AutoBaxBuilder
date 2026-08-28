"""Freeze-time mechanical consistency check for the Study-3 protocol.

Implements the 15 locked items of the freeze-approval message plus the frozen consistency
checklist (2026-08-28_study3_consistency_checklist.md). Text checks run over
whitespace-normalized, emphasis-stripped text so hard line-wraps don't defeat phrase matching;
negation-aware where a banned concept legitimately appears inside its own prohibition. Frame
checks recompute the exclusion arithmetic from the frozen manifests rather than trusting the
built artifact.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "docs/preregistration/2026-08-28_study3_protocol_DRAFT.md"
if not PROTO.exists():  # post-freeze name
    PROTO = ROOT / "docs/preregistration/2026-08-28_study3_constructive_separability_protocol.md"
FRAME = ROOT / "docs/preregistration/2026-08-28_study3_frame.json"
SEL_DIR = ROOT / "docs/preregistration/2026-08-25_round2_selection"
FEAS = ROOT / "docs/preregistration/2026-08-24_instrument_feasibility/selection.json"

text = PROTO.read_text()
# collapse hard line-wraps and markdown emphasis so phrase checks see logical sentences
low = re.sub(r"\s+", " ", text.lower().replace("**", ""))
failures = []


def check(name: str, ok: bool, detail: str = ""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def has(*frags: str) -> bool:
    return all(f.lower() in low for f in frags)


def occurrences_all_negated(term: str, markers: tuple) -> bool:
    """Every occurrence of `term` must sit in a window containing a rejection/prohibition marker."""
    ok = True
    for m in re.finditer(re.escape(term.lower()), low):
        window = low[max(0, m.start() - 400): m.end() + 400]
        if not any(k in window for k in markers):
            ok = False
    return ok


NEG = ("never", "not ", "no ", "barred", "rejected", "superseded", "retired", "prohibi",
       "excluded", "does not", "is not")

# ---- item 1: CR-1 sampling ruling ----
check("1a N=90 resource-fixed, not power/precision-derived",
      has("n = 90", "resource budget", "not described as power-derived or precision-derived"))
check("1b one SRSWOR draw; no supplemental/redraw/extended recruitment",
      has("one srswor draw", "no supplemental draw, no redraw, no extended recruitment"))
check("1c Study-1 outcomes barred from selection/sample-size/eligibility/stopping",
      has("barred", "selection, sample-size, eligibility, and stopping"))
check("1d no outcome-dependent supplemental sampling",
      has("outcome-dependent supplemental sampling is barred"))

# ---- item 2: mechanical prior-exposure exclusion ----
check("2a all four exclusion sets named in frame rule",
      has("90 round-2/study-1 tasks", "reserve", "idr1", "feasibility"))
check("2b no substitution from remaining frame content or outcomes",
      has("no task is substituted, restored, or removed in response"))
frame_ok = False
try:
    fdoc = json.loads(FRAME.read_text())
    sel = json.loads((SEL_DIR / "round2_selection.json").read_text())
    exl = json.loads((SEL_DIR / "round2_exclusion_log.json").read_text())
    feas = json.loads(FEAS.read_text())
    frame864 = set(json.loads((SEL_DIR / "round2_sampling_frame.json").read_text())["frame"])
    s90, r10 = set(sel["selection"]), set(sel["reserve_ordered"])
    idr1 = {e["index"] for e in exl if "Instrument Development Round 1" in e["reason"]}
    fset = {s["index"] for s in feas["selection"]}
    expect = sorted(frame864 - s90 - r10 - idr1 - fset)
    got = fdoc["frame"]
    frame_ok = (got == expect and len(got) == 764
                and sorted(s90 | r10 | idr1 | fset) == fdoc["exclusion_list"]
                and not (set(got) & (s90 | r10 | idr1 | fset)))
except Exception as e:  # noqa: BLE001
    frame_ok = False
    print(f"      frame recompute error: {e}")
check("2c frozen frame artifact matches independent recompute (764; no excluded index inside)",
      frame_ok)

# ---- item 3: eligibility ----
check("3a verbatim eligibility rule fixed a priori",
      has("at least one safety case determined in both runs", "fixed a priori"))
check("3b measured eligibility named; m a result not a target; m=0 branch written",
      has("measured eligibility", "a result, never a design target", "if m = 0"))

# ---- item 4: constraints C and information boundaries ----
check("4a immutable set enumerated",
      has("setup/preamble block", "function name", "closing instruction", "every case",
          "field schema"))
check("4b editable set enumerated (five prose fields + security_policy removable)",
      has("security_policy", "complete removal", "`description`", "`raise`"))
check("4c parameter mentions preserved, mechanically checkable",
      has("every parameter of the original must remain mentioned"))
check("4d writer sees labels; coders never learn derivation/baseline/case kinds",
      has("never learn s′ is derived", "sees the original spec with case-kind labels"))
check("4e baseline and witness stages disjoint sessions",
      has("disjoint fresh coding sessions"))
check("4f VO-DEFECT verifier sees certificate + immutable materials only, never J1 runs",
      has("sees only the certificate and the immutable materials, never the j1 runs"))
check("4g validator scope excludes semantic adequacy",
      has("adequacy is never judged by the writer or the validator"))

# ---- item 5: DS by witness + frozen two-run criterion ----
check("5a DS requires both blinded runs: all capability determined, no safety determined",
      has("both independent blinded j1 runs", "every capability case is determined",
          "no safety case is determined"))
check("5b writer success/failure never DS",
      has("writer output alone", "is never ds"))

# ---- item 6: VO certificate classes only ----
check("6a VO restricted to enumerated certificates; nonexistence standard",
      has("vo requires a certificate that excludes every c-conforming"))
check("6b writer failure never VO; coupling/no-witness route to UR",
      has("writer failure codes alone are never vo", "coupling claims", "lands ur",
          "what cannot prove nonexistence is ur"))

# ---- item 7: DS∧VO halt ----
check("7 DS∧VO = instrument-defect halt, no self-adjudication",
      has("instrument-defect halt", "nothing is reconciled silently"))

# ---- item 8: Round-2 J3 quarantine (negation-aware) ----
j3_ok = has("round-2 j3 values do not appear anywhere in this pipeline") and \
    occurrences_all_negated("j3", NEG + ("instrument-development", "development evidence",
                                         "development rationale", "retired"))
check("8 J3 only as instrument-development rationale; never outcome/eligibility/inference", j3_ok)

# ---- item 9: primary result naming ----
check("9 'sample identification region' named",
      has("sample identification region"))
check("9b explicit non-CI disclaimer",
      has("never called, formatted, or interpreted as a confidence interval")
      and has("not a confidence interval"))

# ---- item 10: L1 = CP only; bootstrap/IM/combined banned (negation-aware) ----
check("10a per-endpoint Clopper–Pearson conditional on realized m",
      has("clopper–pearson", "conditional on the realized m"))
check("10b percentile bootstrap appears only as rejected",
      occurrences_all_negated("percentile bootstrap", ("rejected", "no percentile-bootstrap")))
check("10c Imbens–Manski appears only as rejected/superseded",
      occurrences_all_negated("imbens–manski", ("rejected", "superseded", "no imbens–manski")))
check("10d no combined/composite overall interval",
      has("no composite/combined overall interval of any kind")
      and has("no combined overall interval"))

# ---- item 11: L2 separate, either-run never confirmatory ----
check("11 L2 named apart; either-run profile never a confirmatory classification",
      has("l2 measurement sensitivity",
          "either-run profile is never substituted for, or reported as, a confirmatory "
          "classification"))

# ---- item 12: simulation validates procedure, not assumptions ----
check("12 sim = estimator/procedure validation; A-DS/A-VO substantive",
      has("validates estimator and procedure properties only",
          "does not and cannot establish the identification assumptions",
          "a-ds and a-vo are the substantive conditions"))

# ---- item 13: procedure-inclusive targets, FPC, conditioning population ----
check("13 procedure-inclusive π targets; FPC ignored conservative; eligible-subpopulation "
      "conditioning",
      has("procedure-inclusive", "finite-population correction is ignored, which is conservative",
          "over the eligible subpopulation"))

# ---- item 14: Study 4 closed; no model API evaluation outcome ----
check("14 Study 4 closed; no API evaluation as Study-3 outcome",
      has("study 4 remains closed", "no model api evaluation is a study-3 outcome"))

# ---- item 15: no TBD / open decisions / adaptive branches ----
open_markers = ["to be decided", "left undecided", "cannot be frozen", "left open",
                "pending decision", "not yet ruled"]
found = [m for m in open_markers if m in low]
found += [f"tbd@{m.start()}" for m in re.finditer(r"(?<!no )tbd", low)]
check("15 no TBD/open decision/adaptive interface", not found, f"found: {found}")
check("15b all CR entries closed",
      "closed" in low and not re.search(r"cr-\d+ \((?!closed)", low))

# ---- checklist extras ----
check("x1 seed rule = protocol-hash-derived, single draw",
      has("int(sha256(frozen protocol file)[0:8], 16)", "single draw, no reroll"))
check("x2 no verifier faces an existential question",
      has("no verifier ever faces an existential question"))
check("x3 identified set + sharpness + A-DS/A-VO printed",
      has("[p(ds), 1−p(vo)]", "sharp", "a-ds", "a-vo"))
check("x4 DS witnesses released as artifact",
      has("released as the artifact deliverable"))
check("x5 three named layers, no merging",
      has("one table, three named layers, no merging"))
check("x6 the 90 development tasks listed under 'never does' for the analysis set",
      has("reuses the 90 development tasks in the analysis set"))
check("x7 frozen status header present",
      has("status. frozen protocol"))

print(f"\n{len(failures)} failure(s)" if failures else "\nALL CHECKS PASS")
sys.exit(1 if failures else 0)
