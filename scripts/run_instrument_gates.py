"""Run the two feasibility gates over the 12 selected SeCodePLT tasks.

Gate 1 (functional sufficiency) — mechanical half: every capability case must
still be satisfied by an implementation that reads only the candidate U-N spec.
We test the necessary condition the runner can decide: the benchmark's own
patched_code still passes capability, and the witness also passes capability.
If a witness that ignores the security rule still passes capability, then the
removed clause was not needed for ordinary functionality.

Gate 2 (security underdetermination) — constructive: exhibit W with
Capability(W)=PASS and Security(W)=FAIL. W must comply with the U-N spec; that
compliance is a human judgement recorded in candidate_un_specs.py, not something
this script can decide.

Tasks with spec=None are recorded as INSEPARABLE under the frozen transformation
protocol — a result, not an exclusion.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "docs/preregistration/2026-08-24_instrument_feasibility"))

from candidate_un_specs import UN_SPECS  # noqa: E402
from secodeplt_task_runner import build_program, load, run, verdict  # noqa: E402

OUT = Path("docs/preregistration/2026-08-24_instrument_feasibility")


def main() -> None:
    records = {r["index"]: r for r in load()}
    sel = json.loads((OUT / "selection.json").read_text())["selection"]
    rows = []

    for entry in sel:
        idx = entry["index"]
        rec = records[idx]
        spec = UN_SPECS[idx]
        row = {
            "index": idx,
            "stratum": entry["stratum"],
            "CWE_ID": rec["CWE_ID"],
            "function_name": entry["function_name"],
            "removed": [{"field": f, "clause": c} for f, c in spec["removed"]],
            "coherence_flag": spec["coherence_flag"],
        }

        if spec["spec"] is None:
            row.update(classification="INSEPARABLE", gate1=None, gate2=None,
                       witness_file=None, witness_capability=None, witness_security=None)
            rows.append(row)
            continue

        body = rec["ground_truth"]["vulnerable_code"] if spec["witness"] == "vulnerable_code" else spec["witness"]
        w = run(rec, body)
        p = run(rec, rec["ground_truth"]["patched_code"])

        wc, ws = verdict(w.get("capability")) if not isinstance(w, str) else w, \
                  verdict(w.get("safety")) if not isinstance(w, str) else w
        pc = verdict(p.get("capability")) if not isinstance(p, str) else p

        gate1 = pc == "PASS" and wc == "PASS"      # removed clause not needed for ordinary functionality
        gate2 = wc == "PASS" and ws == "FAIL"      # constructive underdetermination

        wf = None
        if gate2:
            wf = f"witnesses/idx_{idx}.py"
            (OUT / wf).write_text(
                f'"""Gate-2 witness for SeCodePLT task index {idx} (CWE-{rec["CWE_ID"]}).\n\n'
                f'Complies with the candidate U-N specification; passes the capability suite\n'
                f'and fails the security oracle. Body taken from the benchmark\'s own\n'
                f'vulnerable_code, so the witness is not of our authorship.\n'
                f'Run directly with UNITTEST_RESULTS_PATH set.\n"""\n\n'
                + build_program(rec, body)
            )

        row.update(classification="SEPARABLE" if (gate1 and gate2) else "FAILED_GATES",
                   gate1="PASS" if gate1 else "FAIL", gate2="PASS" if gate2 else "FAIL",
                   witness_file=wf, witness_capability=wc, witness_security=ws)
        rows.append(row)

    (OUT / "feasibility_table.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))

    print(f"{'idx':>5} {'stratum':20s} {'CWE':7s} {'gate1':6s} {'gate2':6s} {'W.cap':6s} {'W.sec':6s} classification")
    for r in rows:
        print(f"{r['index']:>5} {r['stratum']:20s} {r['CWE_ID']:7s} "
              f"{str(r['gate1'] or '-'):6s} {str(r['gate2'] or '-'):6s} "
              f"{str(r['witness_capability'] or '-'):6s} {str(r['witness_security'] or '-'):6s} {r['classification']}")
    from collections import Counter
    print("\n", dict(Counter(r["classification"] for r in rows)))
    print(f"coherence-flagged: {[r['index'] for r in rows if r['coherence_flag'] and r['classification']=='SEPARABLE']}")


if __name__ == "__main__":
    main()
