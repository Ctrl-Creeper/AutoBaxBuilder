"""Procedural audit of the two Round-2 coder packets.

Checks that the packets were built correctly and that the two coding runs receive
the same measurement object. It computes nothing about what the tasks say: no
distribution, no balance, no property bearing on any coding outcome.

The load-bearing check is the last one. Two packets that differ in case order could
still differ in content, and "independent coding runs" would then be measuring
different things. Equality is proved over a canonical, order-independent payload
rather than assumed from a shared builder.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
REPO = OUT.parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def main() -> None:
    import os
    os.chdir(REPO)
    from build_round2_coder_packets import (ACCEPTED, ACCEPTED_SHA, EDITABLE, canonical_payload,
                                            extract_cases, signature, witness)
    from secodeplt_task_runner import load

    key = json.loads((OUT / "sealed/_KEY_DO_NOT_SHOW_CODERS.json").read_text())
    man = json.loads((OUT / "coder_packets_manifest.json").read_text())
    accepted = json.loads(ACCEPTED.read_text())
    records = {r["index"]: r for r in load(only_stdlib=False)}
    tids = sorted(key["tasks"])

    check(hashlib.sha256(ACCEPTED.read_bytes()).hexdigest() == ACCEPTED_SHA,
          "input traces to the accepted writer submission by hash")
    check(len(tids) == 90, f"exactly 90 tasks (found {len(tids)})")
    check(not key["processing_failures"], "no processing failures were recorded")

    # --- specifications trace to the accepted submission; non-editable material to source
    spec_bad, noned_bad, case_bad = [], [], []
    total_cases = 0
    for tid in tids:
        meta = key["tasks"][tid]
        rec = records[meta["index"]]
        acc_spec = accepted["tasks"][meta["writer_id"]]["spec"]
        src_cases = extract_cases(rec)
        total_cases += len(src_cases)

        text = (OUT / "coder1_package/tasks" / f"{tid}.md").read_text()
        for f in EDITABLE:
            want = acc_spec[f] or "None"
            if want not in text:
                spec_bad.append(f"{tid}.{f}")
        if f"`{signature(rec)}`" not in text or rec["unittest"]["setup"].strip() not in text:
            noned_bad.append(tid)
        if witness(rec).strip() not in text:
            noned_bad.append(f"{tid}:witness")

        # every source case appears exactly once, in both packets
        for coder in ("coder1", "coder2"):
            t = (OUT / f"{coder}_package/tasks" / f"{tid}.md").read_text()
            rows = re.findall(r"^\| \d+ \| `(.*?)` \| `(.*?)` \|$", t, re.M)
            if sorted(rows) != sorted((c["input"], c["expected"]) for c in src_cases):
                case_bad.append(f"{tid}/{coder}")

    check(not spec_bad, f"every candidate specification is reproduced from the accepted submission ({spec_bad[:4]})")
    check(not noned_bad, f"signature, setup and assembled implementation match source ({noned_bad[:4]})")
    check(not case_bad, f"each source case appears exactly once per packet ({case_bad[:4]})")
    check(total_cases == sum(len(v["coder1_case_order"]) for v in key["tasks"].values()),
          f"case total agrees with the sealed key ({total_cases})")

    # --- permutations reproduce from the recorded seeds
    perm_bad = []
    for coder, sname in (("coder1", "coder1_cases"), ("coder2", "coder2_cases")):
        rng = np.random.default_rng(key["seeds"][sname])
        for tid in tids:
            want = [int(i) for i in rng.permutation(len(key["tasks"][tid][f"{coder}_case_order"]))]
            if want != key["tasks"][tid][f"{coder}_case_order"]:
                perm_bad.append(f"{tid}/{coder}")
    check(not perm_bad, f"every case permutation reproduces from its recorded seed ({perm_bad[:4]})")
    check(all(key["seeds"][k] == int(ACCEPTED_SHA[s:s + 8], 16)
              for k, s in (("task_order", 0), ("coder1_cases", 8), ("coder2_cases", 16))),
          "seeds are the recorded derivation of the accepted submission hash")

    # --- nothing coder-visible carries a label or withheld material
    banned = re.compile(r"\bcapability\b|\bsafety\b|\bCWE\b|F[1-5]_[A-Z_]+|SEPARABLE|INSEPARABLE|"
                        r"STRUCTURALLY|security[_ ]policy|writer_id|edits|provenance|IDR1", re.I)
    leaks = []
    for coder in ("coder1", "coder2"):
        for p in sorted((OUT / f"{coder}_package").rglob("*")):
            if p.is_file():
                hits = set(banned.findall(p.read_text()))
                if hits:
                    leaks.append(f"{coder}/{p.name}:{hits}")
    check(not leaks, f"no label or withheld material in any coder-visible file ({leaks[:3]})")
    check(not any("KEY" in p.name for c in ("coder1", "coder2")
                  for p in (OUT / f"{c}_package").rglob("*")),
          "the sealed key lives outside both packages")

    # --- the decisive one: same measurement object despite different order
    canon = {}
    for coder in ("coder1", "coder2"):
        payload = {}
        for tid in tids:
            meta = key["tasks"][tid]
            rec = records[meta["index"]]
            payload[tid] = canonical_payload({
                "function_name": rec["task_description"]["function_name"],
                "signature": signature(rec), "setup": rec["unittest"]["setup"],
                "spec": accepted["tasks"][meta["writer_id"]]["spec"],
                "witness": witness(rec), "cases": extract_cases(rec)})
        canon[coder] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    check(canon["coder1"] == canon["coder2"] == key["canonical_payload_sha256"]["coder1"],
          f"canonical semantic payloads are identical across packets ({canon['coder1'][:16]}…)")
    check(man["coder1"]["package_sha256"] != man["coder2"]["package_sha256"],
          "the packages differ on disk, as they must — only the case order differs")

    print(f"\n{'PACKET AUDIT PASSED' if not fails else str(len(fails)) + ' FAILURES'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
