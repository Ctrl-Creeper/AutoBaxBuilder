"""Build the two Round-2 coder packets from the accepted writer submission.

Mechanical presentation transformation only. The builder reads the frozen candidate
specifications, attaches the frozen non-editable material, merges the two case sets,
strips their labels, permutes them under a derived seed, and emits the J1-J3
materials. It makes no decision that depends on what a task says.

It may not, and does not: drop a case, rewrite a case, rewrite a specification,
repair a writer failure, judge whether a task is separable, or swap a task out. A
mechanical construction failure is recorded under the frozen processing-failure rule;
a semantic oddity is recorded and left alone.

Per protocol v2 C1 the witness is presented as the **assembled function**, built
through the same path the runner uses, so the Round-1 defect of showing a bare code
fragment cannot recur.

The two packets differ only in the order cases appear. That they are otherwise the
same measurement object is not asserted — a canonical, order-independent payload
hash is computed for each and the audit requires them equal.

Every seed is derived from the accepted submission's own hash. None is chosen.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from secodeplt_task_runner import load  # noqa: E402

HANDOFF = Path("docs/preregistration/2026-08-25_writer_handoff")
ACCEPTED = HANDOFF / "submissions/writer_output_ACCEPTED.json"
ACCEPTED_SHA = "86e2ef6b54a49502035813f91c3fde412533e4374e901931ba838d155f589379"
WRITER_KEY = HANDOFF / "sealed/_KEY_DO_NOT_SHOW_WRITER.json"
OUT = Path("docs/preregistration/2026-08-26_round2_coder_packets")
EDITABLE = ("description", "context", "arguments", "return", "raise")
SCHEMA_VERSION = "round2-coder-v1"

_DUMP = ('\nimport json\nprint("###" + json.dumps([{"situation": s, "input": repr(k), '
         '"expected": getattr(e, "__name__", None) or repr(e)} for s, cs in testcases.items() '
         'for k, e in cs]))\n')


def extract_cases(rec: dict) -> list[dict]:
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "c.py"
        f.write_text(rec["unittest"]["setup"] + "\n" + rec["unittest"]["testcases"] + _DUMP)
        out = subprocess.run([sys.executable, str(f)], cwd=t, capture_output=True,
                             text=True, timeout=60).stdout
    return json.loads(out.split("###", 1)[1])


def signature(rec: dict) -> str:
    for line in rec["ground_truth"]["code_before"].splitlines():
        if re.match(r"\s*def\s", line):
            return line.strip()
    return "(signature not found)"


def witness(rec: dict) -> str:
    """C1: the assembled function, not the bare body."""
    gt = rec["ground_truth"]
    return "\n".join(x for x in (gt["code_before"].rstrip(), gt["vulnerable_code"].rstrip(),
                                 gt["code_after"].rstrip()) if x.strip())


def canonical_payload(task: dict) -> dict:
    """Order-independent semantic content of one task, for cross-packet comparison."""
    return {
        "function_name": task["function_name"],
        "signature": task["signature"],
        "setup": task["setup"],
        "spec": {f: task["spec"][f] for f in EDITABLE},
        "witness": task["witness"],
        "cases": sorted([c["input"], c["expected"]] for c in task["cases"]),
    }


def render(tid: str, t: dict, order: list[int]) -> str:
    L = [f"# Task {tid}", "", "## Specification S", "",
         f"**Function name:** `{t['function_name']}`",
         f"**Signature:** `{t['signature']}`", ""]
    for f in EDITABLE:
        L += [f"**{f.capitalize()}:** {t['spec'][f] or 'None'}", ""]
    L += ["## Setup / preamble code (executed before the implementation; part of S)", "",
          "```python", t["setup"].strip() or "(none)", "```", "",
          "## Cases", "",
          "For each case, decide whether S **determines** the expected behaviour at that input.",
          "If determined, quote the sentence of S that a different behaviour would contradict.",
          "If you cannot quote one, the case is undetermined.", "",
          "| # | input | expected behaviour |", "|---|---|---|"]
    L += [f"| {p} | `{t['cases'][o]['input']}` | `{t['cases'][o]['expected']}` |"
          for p, o in enumerate(order, 1)]
    L += ["", "## Implementation W", "",
          "Judge only whether W contradicts any sentence of S. Do not consult the case table.", "",
          "```python", t["witness"].strip(), "```", "",
          "## Judgements to record", "",
          "- **J1** per case: determined / undetermined, a quote when determined, and a",
          "  confidence of `clear` or `tie_break`.",
          "- **J2**: does W contradict any sentence of S?",
          "- **J3**: does a specification exist that determines every case you marked determined",
          "  and leaves undetermined every case you marked undetermined, without changing the",
          "  signature, the setup code, or any case? The one in front of you counts.", ""]
    return "\n".join(L)


def main() -> None:
    if hashlib.sha256(ACCEPTED.read_bytes()).hexdigest() != ACCEPTED_SHA:
        sys.exit("the accepted submission does not match its frozen hash; refusing to build")

    accepted = json.loads(ACCEPTED.read_text())
    wkey = json.loads(WRITER_KEY.read_text())["mapping"]
    records = {r["index"]: r for r in load(only_stdlib=False)}

    tasks, failures = {}, []
    for wid in sorted(accepted["tasks"]):
        idx = wkey[wid]["index"]
        rec = records[idx]
        try:
            cases = extract_cases(rec)
        except Exception as e:                                   # frozen processing-failure rule
            failures.append({"writer_id": wid, "index": idx, "stage": "case extraction",
                             "error": f"{type(e).__name__}: {e}"})
            continue
        tasks[wid] = {"index": idx, "function_name": rec["task_description"]["function_name"],
                      "signature": signature(rec), "setup": rec["unittest"]["setup"],
                      "spec": accepted["tasks"][wid]["spec"], "witness": witness(rec),
                      "cases": cases}

    # --- seeds derived from the accepted submission's own hash, never chosen
    seeds = {"task_order": int(ACCEPTED_SHA[0:8], 16),
             "coder1_cases": int(ACCEPTED_SHA[8:16], 16),
             "coder2_cases": int(ACCEPTED_SHA[16:24], 16)}

    wids = sorted(tasks)
    task_order = np.random.default_rng(seeds["task_order"]).permutation(len(wids))
    assign = {f"C{p:02d}": wids[int(i)] for p, i in enumerate(task_order, 1)}

    key = {"accepted_submission_sha256": ACCEPTED_SHA, "seeds": seeds,
           "seed_derivation": "int(accepted_sha256[0:8|8:16|16:24], 16)",
           "processing_failures": failures, "tasks": {}}

    payload_hashes = {}
    for coder, seed_name in (("coder1", "coder1_cases"), ("coder2", "coder2_cases")):
        pdir = OUT / f"{coder}_package" / "tasks"
        pdir.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(seeds[seed_name])
        canon = {}
        for tid in sorted(assign):
            t = tasks[assign[tid]]
            order = [int(i) for i in rng.permutation(len(t["cases"]))]
            (pdir / f"{tid}.md").write_text(render(tid, t, order))
            canon[tid] = canonical_payload(t)
            key["tasks"].setdefault(tid, {"writer_id": assign[tid], "index": t["index"],
                                          "case_situations_source_order":
                                              [c["situation"] for c in t["cases"]]})
            key["tasks"][tid][f"{coder}_case_order"] = order
        payload_hashes[coder] = hashlib.sha256(
            json.dumps(canon, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    tmpl = {"schema_version": SCHEMA_VERSION, "coder_id": "", "tasks": {}}
    for tid in sorted(assign):
        n = len(tasks[assign[tid]]["cases"])
        tmpl["tasks"][tid] = {
            "J1": [{"case": i, "determined": None, "quote": "", "confidence": None}
                   for i in range(1, n + 1)],
            "J2": {"contradicts_S": None, "contradicted_sentence": ""},
            "J3": {"exists": None, "S_prime": None, "carrying_element": None, "reason": ""},
            "notes": ""}

    for coder in ("coder1", "coder2"):
        (OUT / f"{coder}_package" / "answers_template.json").write_text(json.dumps(tmpl, indent=2))

    key["canonical_payload_sha256"] = payload_hashes
    (OUT / "sealed").mkdir(parents=True, exist_ok=True)
    (OUT / "sealed" / "_KEY_DO_NOT_SHOW_CODERS.json").write_text(
        json.dumps(key, indent=2, ensure_ascii=False))

    print(f"tasks built            {len(tasks)}   processing failures {len(failures)}")
    print(f"cases total            {sum(len(t['cases']) for t in tasks.values())}")
    print(f"seeds                  {seeds}")
    print(f"canonical payload sha  coder1 {payload_hashes['coder1'][:16]}…")
    print(f"                       coder2 {payload_hashes['coder2'][:16]}…")
    print(f"identical payload      {payload_hashes['coder1'] == payload_hashes['coder2']}")


if __name__ == "__main__":
    main()
