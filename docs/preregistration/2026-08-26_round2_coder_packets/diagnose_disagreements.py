"""Diagnostic disagreement analysis — how the disagreements arose, not who was right.

Nothing here adjudicates. No disagreement is resolved, neither run is recorded as
correct, and the frozen protocol is not touched. Every stratification is mechanical:
a quote is attributed to a carrier by locating it inside the frozen specification,
never by reading what it means.

Quote divergence is classified by mechanism only. No semantic similarity score is
invented; where two quotes cannot be placed, that is counted rather than guessed at.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import os                                                          # noqa: E402
os.chdir(REPO)
from build_round2_coder_packets import EDITABLE, signature          # noqa: E402
from secodeplt_task_runner import load                             # noqa: E402

ACCEPTED = Path("docs/preregistration/2026-08-25_writer_handoff/submissions/writer_output_ACCEPTED.json")
PROSE = set(EDITABLE)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def carriers_of(quote: str, comp: dict[str, str]) -> set[str]:
    """Which components of S contain this quote verbatim, after normalisation."""
    q = norm(quote)
    return {name for name, text in comp.items() if q and q in norm(text)} if q else set()


def kind(cs: set[str]) -> str:
    if not cs:
        return "no citable evidence"
    if cs <= PROSE:
        return "prose" if len(cs) == 1 else "multiple prose fields"
    if cs <= {"signature", "setup"}:
        return "structural carrier"
    return "prose and structural carrier"


def divergence_kind(c1: set[str], q1: str, c2: set[str], q2: str) -> str:
    if not c1 or not c2:
        return "at least one quote not locatable in S"
    a, b = norm(q1), norm(q2)
    if c1 == c2:
        return "different extent of the same passage" if (a in b or b in a) \
            else "different sentences in the same component"
    if (c1 <= PROSE) != (c2 <= PROSE):
        return "prose versus structural carrier"
    if not (c1 & c2):
        return "different components"
    return "overlapping component sets"


def main() -> None:
    align = json.loads((OUT / "alignment.json").read_text())
    rows = align["rows"]
    sub = {c: json.loads((OUT / f"submissions/{c}_answers_FROZEN.json").read_text())
           for c in ("coder1", "coder2")}
    res_pre = json.loads((OUT / "results_pre_adjudication.json").read_text())
    accepted = json.loads(ACCEPTED.read_text())
    wkey = json.loads(Path("docs/preregistration/2026-08-25_writer_handoff/sealed/"
                           "_KEY_DO_NOT_SHOW_WRITER.json").read_text())["mapping"]
    ckey = json.loads((OUT / "sealed/_KEY_DO_NOT_SHOW_CODERS.json").read_text())["tasks"]
    records = {r["index"]: r for r in load(only_stdlib=False)}

    comp = {}
    for tid, meta in ckey.items():
        rec = records[meta["index"]]
        spec = accepted["tasks"][meta["writer_id"]]["spec"]
        comp[tid] = {**{f: spec[f] for f in EDITABLE},
                     "signature": signature(rec), "setup": rec["unittest"]["setup"]}

    out: dict = {"note": "Diagnostic only. Nothing is adjudicated and no run is recorded as correct."}

    # --- 1 directionality
    dis = [r for r in rows if r["coder1_determined"] != r["coder2_determined"]]
    d1 = [r for r in dis if r["coder1_determined"]]
    d2 = [r for r in dis if r["coder2_determined"]]
    out["directionality"] = {
        "coder1_only_determined": len(d1), "coder2_only_determined": len(d2),
        "by_situation": {"coder1_only": dict(Counter(r["situation"] for r in d1)),
                         "coder2_only": dict(Counter(r["situation"] for r in d2))},
        "base_rates_by_situation": {
            c: {s: round(sum(1 for r in rows if r["situation"] == s and r[f"{c}_determined"])
                         / max(1, sum(1 for r in rows if r["situation"] == s)), 3)
                for s in ("capability", "safety")} for c in ("coder1", "coder2")},
        "carrier_cited_by_the_determining_run": {
            "coder1_only": dict(Counter(kind(carriers_of(r["coder1_quote"], comp[r["task"]])) for r in d1)),
            "coder2_only": dict(Counter(kind(carriers_of(r["coder2_quote"], comp[r["task"]])) for r in d2))},
    }

    # --- 2 confidence
    pairs = Counter((r["coder1_confidence"], r["coder2_confidence"]) for r in dis)
    out["confidence_of_disagreements"] = {f"{a} vs {b}": n for (a, b), n in sorted(pairs.items())}
    out["confidence_of_agreements"] = {
        f"{a} vs {b}": n for (a, b), n in sorted(Counter(
            (r["coder1_confidence"], r["coder2_confidence"])
            for r in rows if r["coder1_determined"] == r["coder2_determined"]).items())}

    # --- 3 evidence mechanism, per disagreeing case
    mech = []
    for r in dis:
        c = comp[r["task"]]
        det, oth = ("coder1", "coder2") if r["coder1_determined"] else ("coder2", "coder1")
        cs = carriers_of(r[f"{det}_quote"], c)
        mech.append({"task": r["task"], "source_index": r["source_index"], "situation": r["situation"],
                     "determining_run": det, "carrier": kind(cs), "carriers": sorted(cs),
                     "determining_confidence": r[f"{det}_confidence"],
                     "abstaining_confidence": r[f"{oth}_confidence"]})
    out["evidence_mechanism"] = {"per_case": mech,
                                 "carrier_counts": dict(Counter(m["carrier"] for m in mech))}

    # --- 4 quote divergence where both determined but quotes differ
    both = [r for r in rows if r["coder1_determined"] and r["coder2_determined"]]
    div = [r for r in both if norm(r["coder1_quote"]) != norm(r["coder2_quote"])]
    dk = []
    for r in div:
        c = comp[r["task"]]
        c1, c2 = carriers_of(r["coder1_quote"], c), carriers_of(r["coder2_quote"], c)
        dk.append({"task": r["task"], "source_index": r["source_index"],
                   "mechanism": divergence_kind(c1, r["coder1_quote"], c2, r["coder2_quote"]),
                   "coder1_carriers": sorted(c1), "coder2_carriers": sorted(c2)})
    out["quote_divergence"] = {"cases_both_determined": len(both), "quotes_differing": len(div),
                               "mechanism_counts": dict(Counter(d["mechanism"] for d in dk)),
                               "per_case": dk,
                               "note": "mechanism only; no semantic similarity was computed"}

    # --- 5 task concentration
    per_task = Counter(r["task"] for r in dis)
    counts = sorted(per_task.values(), reverse=True)
    out["task_concentration"] = {
        "tasks_with_disagreement": len(per_task), "n_tasks": align["n_tasks"],
        "disagreements_per_task": dict(sorted(per_task.items())),
        "distribution": dict(Counter(counts)),
        "share_from_top_3_tasks": round(sum(counts[:3]) / len(dis), 3) if dis else None,
        "share_from_top_5_tasks": round(sum(counts[:5]) / len(dis), 3) if dis else None,
        "cases_per_task_for_disagreeing": {t: align["cases_per_task"][t] for t in sorted(per_task)},
    }

    # --- 6 J2 / J3 aggregate mechanism
    tids = sorted(ckey)
    j3 = {c: Counter(bool(sub[c]["tasks"][t]["J3"]["exists"]) for t in tids) for c in sub}
    j2 = {c: Counter(bool(sub[c]["tasks"][t]["J2"]["contradicts_S"]) for t in tids) for c in sub}
    out["j2_j3"] = {
        "j3_marginals": {c: {"exists_true": j3[c][True], "exists_false": j3[c][False]} for c in sub},
        "j3_disagreements": sum(1 for t in tids
                                if bool(sub["coder1"]["tasks"][t]["J3"]["exists"])
                                != bool(sub["coder2"]["tasks"][t]["J3"]["exists"])),
        "j2_marginals": {c: {"contradicts_true": j2[c][True], "contradicts_false": j2[c][False]} for c in sub},
        "j2_disagreements": sum(1 for t in tids
                                if bool(sub["coder1"]["tasks"][t]["J2"]["contradicts_S"])
                                != bool(sub["coder2"]["tasks"][t]["J2"]["contradicts_S"])),
        "granularity_note": ("J3 is one binary per task against a median of five per task for J1, so "
                             "it has far fewer opportunities to diverge. Zero disagreement is "
                             "consistent with a coarse and near-degenerate marginal and is not "
                             "evidence that J3 is reliable."),
    }

    # --- 7 which input drove each class disagreement
    tbl = {r["task"]: r for r in res_pre["derived_class_table"]}
    drivers = []
    for t in sorted(tbl):
        if tbl[t]["agree"]:
            continue
        n_j1 = sum(1 for r in rows if r["task"] == t
                   and r["coder1_determined"] != r["coder2_determined"])
        j2d = bool(sub["coder1"]["tasks"][t]["J2"]["contradicts_S"]) != \
            bool(sub["coder2"]["tasks"][t]["J2"]["contradicts_S"])
        j3d = bool(sub["coder1"]["tasks"][t]["J3"]["exists"]) != \
            bool(sub["coder2"]["tasks"][t]["J3"]["exists"])
        driver = ("a single J1 case" if n_j1 == 1 and not (j2d or j3d)
                  else "multiple J1 cases" if n_j1 > 1 and not (j2d or j3d)
                  else "J2 only" if n_j1 == 0 and j2d and not j3d
                  else "J3 only" if n_j1 == 0 and j3d and not j2d
                  else "no differing input — check the derivation" if n_j1 == 0 and not (j2d or j3d)
                  else "mixed inputs")
        drivers.append({"task": t, "coder1": tbl[t]["coder1"], "coder2": tbl[t]["coder2"],
                        "j1_case_disagreements": n_j1, "j2_differs": j2d, "j3_differs": j3d,
                        "driver": driver})
    out["class_disagreement_drivers"] = {
        "n_disagreeing_tasks": len(drivers), "per_task": drivers,
        "driver_counts": dict(Counter(d["driver"] for d in drivers))}

    (OUT / "diagnostic_disagreement_analysis.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False))

    show = {k: v for k, v in out.items() if k != "note"}
    for k in ("evidence_mechanism", "quote_divergence", "class_disagreement_drivers",
              "task_concentration"):
        show[k] = {kk: vv for kk, vv in show[k].items()
                   if kk not in ("per_case", "per_task", "disagreements_per_task",
                                 "cases_per_task_for_disagreeing")}
    print(json.dumps(show, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
