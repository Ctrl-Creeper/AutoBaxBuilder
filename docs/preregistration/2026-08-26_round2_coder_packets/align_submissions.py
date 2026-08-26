"""Step 1 — reveal the sealed key and align the two submissions case by case.

Alignment is by identifier only. Each packet presented the same source cases in a
different order, both permutations recorded at build time, so a presented position
maps back to its source index arithmetically. Nothing here reads a judgement, a
quote, or a case's content; the audit that follows checks counts and identities and
stops there.

Output: alignment.json — one row per source case, carrying the source index, the
situation label revealed from the key, and each run's presented position and its
J1 record.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
KEY = OUT / "sealed/_KEY_DO_NOT_SHOW_CODERS.json"
SUBS = {"coder1": OUT / "submissions/coder1_answers_FROZEN.json",
        "coder2": OUT / "submissions/coder2_answers_FROZEN.json"}
FROZEN_SHA = {"coder1": "35916e1c02b4466b9f45f232d98e4e6c6f5f1a5109819ebfd62cce932eda64d6",
              "coder2": "1f254579d2d4c36f28e3f3e86a45ea2c492460071d05759a6b3c653edc5f6789"}

fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def main() -> None:
    for c, p in SUBS.items():
        check(hashlib.sha256(p.read_bytes()).hexdigest() == FROZEN_SHA[c],
              f"{c} submission matches its frozen hash")

    key = json.loads(KEY.read_text())
    sub = {c: json.loads(p.read_text()) for c, p in SUBS.items()}
    tids = sorted(key["tasks"])

    rows, per_task = [], {}
    for tid in tids:
        meta = key["tasks"][tid]
        situations = meta["case_situations_source_order"]
        n = len(situations)
        orders = {c: meta[f"{c}_case_order"] for c in SUBS}

        for c, o in orders.items():
            if sorted(o) != list(range(n)):
                fails.append(f"{tid}: {c} permutation is not a permutation of 0..{n-1}")

        j1 = {c: {e["case"]: e for e in sub[c]["tasks"][tid]["J1"]} for c in SUBS}
        for c in SUBS:
            if sorted(j1[c]) != list(range(1, n + 1)):
                fails.append(f"{tid}: {c} J1 case numbers are not 1..{n}")

        for s in range(n):
            row = {"task": tid, "source_index": s, "situation": situations[s]}
            for c in SUBS:
                pos = orders[c].index(s) + 1                      # presented position, 1-based
                e = j1[c].get(pos)
                row[f"{c}_position"] = pos
                row[f"{c}_determined"] = None if e is None else bool(e["determined"])
                row[f"{c}_quote"] = "" if e is None else (e.get("quote") or "")
                row[f"{c}_confidence"] = None if e is None else e.get("confidence")
            rows.append(row)
        per_task[tid] = n

    # --- audit: every source case judged exactly once by each run
    seen = Counter((r["task"], r["source_index"]) for r in rows)
    check(all(v == 1 for v in seen.values()), "every source case appears exactly once in the alignment")
    check(len(rows) == sum(per_task.values()) == 442,
          f"alignment covers all 442 source cases (found {len(rows)})")
    check(all(r["coder1_determined"] is not None and r["coder2_determined"] is not None for r in rows),
          "every aligned case carries a judgement from both runs")
    for c in SUBS:
        pos_used = Counter((r["task"], r[f"{c}_position"]) for r in rows)
        check(all(v == 1 for v in pos_used.values()),
              f"{c}: each presented position is consumed exactly once")
        recorded = sum(len(sub[c]["tasks"][t]["J1"]) for t in tids)
        check(recorded == len(rows), f"{c}: {recorded} recorded judgements match 442 aligned cases")
    check(len(tids) == 90, f"90 tasks aligned (found {len(tids)})")

    art = {"key_sha256": hashlib.sha256(KEY.read_bytes()).hexdigest(),
           "submission_sha256": FROZEN_SHA,
           "n_tasks": len(tids), "n_cases": len(rows),
           "cases_per_task": per_task, "rows": rows}
    (OUT / "alignment.json").write_text(json.dumps(art, indent=2, ensure_ascii=False))
    print(f"\nwrote alignment.json — {len(tids)} tasks, {len(rows)} cases")
    print(f"{'ALIGNMENT AUDIT PASSED' if not fails else str(len(fails)) + ' FAILURES'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
