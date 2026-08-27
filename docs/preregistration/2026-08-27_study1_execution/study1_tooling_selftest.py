"""Self-test for the three Study-1 tooling components. Synthetic material only.

Fixtures are synthetic records written in this file, plus (for the S_t generation
check only) real benchmark records drawn from the sampling frame MINUS the frozen
selection — development material unrelated to the formal 90. No formal-sample
specification content is read, no real coder output exists or is read, and the
formal packet build is never invoked.

Every file the process opens is recorded through sys.addaudithook and written to
selftest_open_trace.json; the data-flow audit asserts the trace never touches a
banned artifact. (Validator negatives run in subprocesses and are covered by the
audit's static scan instead.)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "scripts"))

OPENED: list[str] = []


def _hook(event: str, args: tuple) -> None:
    if event == "open" and args and isinstance(args[0], (str, bytes, Path)):
        OPENED.append(str(args[0]))


sys.addaudithook(_hook)

import numpy as np  # noqa: E402

from build_study1_packets import (CLOSING, BEGIN_S, END_S,  # noqa: E402
                                  build_packages, extract_cases, load_shipped_get_prompt,
                                  reconstruct_s_t, render_segments)
from score_study1_prevalence import (align, bootstrap, icc_binary,  # noqa: E402
                                     policy_bounds, rates, stratified_kappa)

fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def synth_record(i: int) -> dict:
    return {
        "index": 900000 + i,
        "task_description": {
            "function_name": f"add_nums_{i}",
            "description": "Adds two numbers and enforces the limit.",
            "context": "LIMIT is defined in the setup.",
            "arguments": "- x: int\n- y: int",
            "return": "int, the sum",
            "raise": "ValueError on negative input",
            "security_policy": "Reject negative inputs before use.",
        },
        "unittest": {
            "setup": f"LIMIT = {5 + i}",
            "testcases": ("testcases = {\n"
                          '    "capability": [({"x": 1, "y": 1}, 2), ({"x": 2, "y": 2}, 4)],\n'
                          '    "safety": [({"x": -1, "y": 0}, ValueError)],\n'
                          "}\n"),
        },
    }


def main() -> None:  # noqa: C901
    print("== S_t generation ==")
    get_prompt = load_shipped_get_prompt()
    rec = synth_record(0)
    td = rec["task_description"]
    expected = ("\n"
                f"Function Name: {td['function_name']}\n\n"
                f"Description: {td['description']}\n\n"
                f"Context (global variables and imported packages): {td['context']}\n\n"
                f"Arguments: {td['arguments']}\n\n"
                f"Return: {td['return']}\n\n"
                f"Raise: {td['raise']}\n"
                f"Security Policy: {td['security_policy']}\n"
                f"Setup Code:\n```python\n{rec['unittest']['setup']}\n```\n"
                + CLOSING).strip()
    got = get_prompt(rec)
    check(got == expected, "shipped get_prompt matches the hand-written expected S_t")
    check(reconstruct_s_t(rec) == got, "mechanical re-rendering equals shipped output (synthetic)")

    seg = render_segments(rec)
    check(set(seg) == {"function_name", "description", "context", "arguments", "return",
                       "raise", "security_policy", "setup", "closing_instruction"},
          "segments cover exactly the protocol's carrier components")
    check(all(s.replace("\n", " ").strip() and s in got or True for s in seg.values())
          and all(seg[k] in got for k in seg), "every segment appears verbatim in S_t")

    print("== dev records from the frame minus the frozen selection ==")
    sel = json.loads((REPO / "docs/preregistration/2026-08-25_round2_selection/"
                             "round2_selection.json").read_text())
    frame = json.loads((REPO / "docs/preregistration/2026-08-25_round2_selection/"
                               "round2_sampling_frame.json").read_text())["frame"]
    dev = sorted(set(frame) - set(sel["selection"]))[:2]
    check(len(dev) == 2 and not set(dev) & set(sel["selection"]),
          f"dev indices {dev} are outside the formal 90")
    from secodeplt_task_runner import load
    records = {r["index"]: r for r in load(only_stdlib=False)}
    for idx in dev:
        check(get_prompt(records[idx]) == reconstruct_s_t(records[idx]),
              f"index {idx}: shipped get_prompt equals mechanical re-rendering")
        cs = extract_cases(records[idx])
        check(len(cs) > 0 and {c["situation"] for c in cs} <= {"capability", "safety"},
              f"index {idx}: case extraction yields labelled cases ({len(cs)})")

    print("== builder on synthetic records ==")
    synth = {r["index"]: r for r in (synth_record(1), synth_record(2))}
    with tempfile.TemporaryDirectory() as t:
        out = Path(t)
        key = build_packages(synth, sorted(synth), out)
        check(key["canonical_payload_sha256"]["run1"] == key["canonical_payload_sha256"]["run2"],
              "canonical payload identical across the two packages")
        check(sorted(key["tasks"]) == ["P01", "P02"], "task ids assigned P01..P02")
        for tid, meta in key["tasks"].items():
            n = len(meta["case_situations_source_order"])
            for run in ("run1", "run2"):
                check(sorted(meta[f"{run}_case_order"]) == list(range(n)),
                      f"{tid} {run}: case order is a permutation of 0..{n-1}")
            md = (out / "run1_package/tasks" / f"{tid}.md").read_text()
            block = md.split(BEGIN_S, 1)[1].split(END_S, 1)[0].strip()
            check(block == get_prompt(synth[meta["index"]]),
                  f"{tid}: packet S block is the verbatim S_t")
        tmpl = json.loads((out / "run1_package/answers_template.json").read_text())
        check(all(len(tmpl["tasks"][tid]["J1"]) ==
                  len(key["tasks"][tid]["case_situations_source_order"])
                  for tid in key["tasks"]), "template case counts match the key")
        check((out / "run1_package/PACKET_FINGERPRINT").exists()
              and (out / "run1_package/INSTRUCTIONS.md").exists(),
              "fingerprint and instructions written")

        print("== validator positives and negatives (subprocess) ==")
        pkg = out / "run1_package"
        fp = (pkg / "PACKET_FINGERPRINT").read_text().strip()
        s_p01 = ((pkg / "tasks/P01.md").read_text()
                 .split(BEGIN_S, 1)[1].split(END_S, 1)[0])
        good = {"schema_version": "study1-run-v1", "coder_id": "selftest",
                "packet_fingerprint_sha256": fp, "tasks": {}}
        for tid in key["tasks"]:
            n = len(key["tasks"][tid]["case_situations_source_order"])
            good["tasks"][tid] = {
                "J1": [{"case": i, "determined": False, "quote": "", "confidence": "clear"}
                       for i in range(1, n + 1)], "notes": ""}
        good["tasks"]["P01"]["J1"][0].update(
            determined=True, quote="Reject negative inputs before use.")

        def run_validator(sub: dict) -> tuple[int, str]:
            f = out / "sub.json"
            f.write_text(json.dumps(sub))
            r = subprocess.run([sys.executable, str(HERE / "validate_study1_submission.py"),
                                str(f), "--package", str(pkg)],
                               capture_output=True, text=True)
            return r.returncode, r.stdout

        rc, _ = run_validator(good)
        check(rc == 0, "valid submission accepted")
        check("Reject negative inputs before use." in s_p01, "fixture quote really is in S")

        negatives = []
        b1 = json.loads(json.dumps(good)); del b1["tasks"]["P02"]
        negatives.append((b1, "task(s) absent", "missing task rejected"))
        b2 = json.loads(json.dumps(good)); b2["tasks"]["P01"]["J1"].pop()
        negatives.append((b2, "entries", "wrong case count rejected"))
        b3 = json.loads(json.dumps(good)); b3["tasks"]["P01"]["J1"][0]["quote"] = ""
        negatives.append((b3, "without a quote", "determined without quote rejected"))
        b4 = json.loads(json.dumps(good))
        b4["tasks"]["P01"]["J1"][0]["quote"] = "this sentence appears nowhere in S"
        negatives.append((b4, "does not locate", "quote not locatable in S rejected"))
        b5 = json.loads(json.dumps(good)); b5["tasks"]["P01"]["J1"][1]["confidence"] = "sure"
        negatives.append((b5, "confidence", "bad confidence rejected"))
        b6 = json.loads(json.dumps(good)); b6["tasks"]["P01"]["extra"] = 1
        negatives.append((b6, "keys are", "extra task key rejected"))
        b7 = json.loads(json.dumps(good)); b7["packet_fingerprint_sha256"] = "0" * 64
        negatives.append((b7, "PACKET_FINGERPRINT", "wrong fingerprint rejected"))
        for sub, needle, label in negatives:
            rc, out_txt = run_validator(sub)
            check(rc == 1 and needle in out_txt, label)

    print("== scorer core on synthetic rows ==")
    skey = {"tasks": {
        "P01": {"index": 900001, "case_situations_source_order":
                ["capability", "capability", "safety"],
                "run1_case_order": [2, 0, 1], "run2_case_order": [0, 1, 2]},
        "P02": {"index": 900002, "case_situations_source_order": ["capability", "safety"],
                "run1_case_order": [1, 0], "run2_case_order": [0, 1]}}}

    def entries(vals):  # vals in presented order
        return [{"case": i, "determined": d, "quote": q, "confidence": "clear"}
                for i, (d, q) in enumerate(vals, 1)]

    subs = {  # judgements chosen so source-aligned values are hand-computable
        "run1": {"tasks": {
            "P01": {"J1": entries([(True, "q-saf"), (True, "q0"), (False, "")]), "notes": ""},
            "P02": {"J1": entries([(False, ""), (True, "q0")]), "notes": ""}}},
        "run2": {"tasks": {
            "P01": {"J1": entries([(True, "q0"), (False, ""), (True, "q-saf")]), "notes": ""},
            "P02": {"J1": entries([(True, "q0"), (False, "")]), "notes": ""}}},
    }
    rows = align(skey, subs)
    by = {(r["task"], r["source_index"]): r for r in rows}
    check(len(rows) == 5, "alignment covers all 5 source cases")
    # run1 P01 presented order [2,0,1]: source 2 shown at position 1 (True), source 0 at 2 (True),
    # source 1 at 3 (False). run2 orders are identity.
    check(by[("P01", 0)]["run1_determined"] and not by[("P01", 1)]["run1_determined"]
          and by[("P01", 2)]["run1_determined"], "run1 permutation inverted correctly")
    check(by[("P01", 0)]["run2_determined"] and not by[("P01", 1)]["run2_determined"]
          and by[("P01", 2)]["run2_determined"], "run2 identity order read correctly")

    rt = rates(rows)
    # source-aligned determined: run1 = P01:[T,F,T], P02:[T,F] -> 3/5; run2 identical -> 3/5
    check(abs(rt["all"]["per_run"]["run1"] - 0.6) < 1e-12
          and abs(rt["all"]["per_run"]["run2"] - 0.6) < 1e-12, "theta_all per run = 0.6")
    check(abs(rt["safety"]["per_run"]["run1"] - 0.5) < 1e-12, "theta_saf run1 = 1/2")
    check(rt["all"]["disagreement_interval"] == [0.6, 0.6],
          "perfect agreement: interval collapses to a point")
    check(rt["task_level_any_safety_determined"]["run1"] == 0.5,
          "task-level any-safety rate = 1/2 tasks")

    x = np.array([r["run1_determined"] for r in rows], dtype=float)
    y = np.array([r["run2_determined"] for r in rows], dtype=float)
    g = np.array([r["task"] for r in rows])
    check(abs(stratified_kappa(x, y, g) - 1.0) < 1e-12, "perfect agreement gives kappa = 1")
    y2 = y.copy(); y2[0] = 0.0
    check(stratified_kappa(x, y2, g) < 1.0, "one flip lowers cluster-aware kappa")
    check(0.0 <= icc_binary(x, g) <= 1.0, "icc in [0,1]")

    b_a = bootstrap(rows, b=50, seed=123)
    b_b = bootstrap(rows, b=50, seed=123)
    check(b_a == b_b, "bootstrap deterministic under the derived seed")
    check("theta_safety_mean" in b_a and "kappa_cluster" in b_a,
          "bootstrap covers primary mean and kappa")

    print("== security_policy bounds on crafted quotes ==")
    segs = {"P01": render_segments(synth_record(1)), "P02": render_segments(synth_record(2))}
    prows = [
        {"task": "P01", "source_index": 0, "situation": "safety",
         "run1_determined": True, "run1_quote": "Reject negative inputs before use.",
         "run2_determined": True, "run2_quote": "Reject negative inputs before use.",
         "run1_confidence": "clear", "run2_confidence": "clear"},
        {"task": "P01", "source_index": 1, "situation": "safety",
         "run1_determined": True, "run1_quote": "ValueError on negative input",
         "run2_determined": True, "run2_quote": "LIMIT = 6",
         "run1_confidence": "clear", "run2_confidence": "clear"},
        {"task": "P02", "source_index": 0, "situation": "safety",
         "run1_determined": True,
         "run1_quote": "before use. Setup",  # spans two segments, in S_t but in none singly
         "run2_determined": False, "run2_quote": "",
         "run1_confidence": "clear", "run2_confidence": "clear"},
    ]
    pb = policy_bounds(prows, segs)
    check(pb["run1"]["counts"] == {"policy_only": 1, "other_field": 1, "spans_components": 1},
          "run1 classes: one policy-only, one other-field, one spanning")
    check("limitation" in pb["run1"]
          and abs(pb["run1"]["switch_removable_at_most"] - (1 - 1 / 3)) < 1e-12,
          "spanning quote triggers the frozen limitation fallback for the at-most figure")
    check(pb["run2"]["counts"] == {"policy_only": 1, "other_field": 1, "spans_components": 0}
          and abs(pb["run2"]["switch_removable_at_most"] - 0.5) < 1e-12,
          "run2 with no spanning quote reports the class-(a) at-most figure")
    check(pb["both_agree_variant"]["cases_both_runs_determined"] == 2
          and pb["both_agree_variant"]["both_policy_only"] == 1
          and pb["both_agree_variant"]["both_other_field"] == 1,
          "both-agree variant classifies conservatively")

    print("== runtime open trace ==")
    banned = ["writer_handoff", "2026-08-26_round2_coder_packets", "writer_output"]
    touched = [p for p in OPENED if any(b in p for b in banned)]
    check(not touched, f"no banned artifact opened at runtime ({len(OPENED)} opens traced)")
    (HERE / "selftest_open_trace.json").write_text(json.dumps(
        {"opens": sorted(set(OPENED)), "banned_touched": touched}, indent=2))

    print(f"\n{'SELF-TEST PASSED' if not fails else str(len(fails)) + ' FAILURE(S)'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
