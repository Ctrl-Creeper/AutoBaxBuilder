"""Study 3 — shared blinded-packet construction, reusing the Study-1 machinery verbatim.

The protocol (§3, §5) mandates that both the baseline packets (original S_t) and the S′
verification packets are built by the Study-1 builder machinery: presentation permutations,
sentinel markers, canonical payload fingerprints, the same coder INSTRUCTIONS, the same
answers template shape. This module imports those primitives from the frozen Study-1 module
(code only; no Study-1 data artifact is read) and parameterises exactly what Study 3 must:
which records, which schema version, which seed slices, and what provenance goes in the key.

Coders receive nothing beyond the packet: no labels, no derivation status, no baseline
existence, no provenance — all of that lives only in the sealed key.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

from study3_pins import PROTOCOL_SHA, RUNS, seed_from_protocol

from build_study1_packets import (BEGIN_S, END_S, INSTRUCTIONS,  # noqa: F401  (frozen Study-1 machinery, code only)
                                  extract_cases, load_shipped_get_prompt,
                                  reconstruct_s_t, render_segments, render_task)


def build_packages(records: dict[int, dict], indices: list[int], out: Path,
                   schema_version: str, task_seed_name: str, run_seed_names: dict[str, str],
                   key_extra: dict, id_prefix: str = "P") -> dict:
    """Mechanical package construction for one stage (baseline or S′). Returns the key.

    S_t for every record is produced by the benchmark's own shipped get_prompt and byte-
    checked against the mechanical re-rendering — for S′ records this doubles as the proof
    that the render carries exactly the candidate prose plus the untouched frozen components.
    """
    get_prompt = load_shipped_get_prompt()

    tasks = {}
    for idx in indices:
        rec = records[idx]
        s_t = get_prompt(rec)
        if s_t != reconstruct_s_t(rec):
            sys.exit(f"index {idx}: shipped get_prompt and mechanical re-rendering disagree; "
                     "refusing to build")
        seg = render_segments(rec)
        joined = "\n".join(seg.values())
        for name, text in seg.items():
            if re.sub(r"\s+", " ", text).strip() not in re.sub(r"\s+", " ", joined):
                sys.exit(f"index {idx}: segment {name} lost in normalisation")
        tasks[idx] = {"s_t": s_t, "segments": seg, "cases": extract_cases(rec)}

    seeds = {"task_order": seed_from_protocol(task_seed_name),
             **{run: seed_from_protocol(n) for run, n in run_seed_names.items()}}

    order = np.random.default_rng(seeds["task_order"]).permutation(len(indices))
    assign = {f"{id_prefix}{p:02d}": indices[int(i)] for p, i in enumerate(order, 1)}

    key = {"protocol_sha256": PROTOCOL_SHA,
           "schema_version": schema_version,
           "seeds": seeds,
           "seed_derivation": "int(study3_protocol_sha256[slice], 16); slices per "
                              "study3_pins.SEED_SLICES",
           **key_extra,
           "tasks": {}}

    tmpl = {"schema_version": schema_version, "coder_id": "",
            "packet_fingerprint_sha256": "", "tasks": {}}
    payload_hashes = {}
    for run in RUNS:
        pdir = out / f"{run}_package" / "tasks"
        pdir.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(seeds[run])
        canon = {}
        for tid in sorted(assign):
            t = tasks[assign[tid]]
            case_order = [int(i) for i in rng.permutation(len(t["cases"]))]
            (pdir / f"{tid}.md").write_text(render_task(tid, t["s_t"], t["cases"], case_order))
            canon[tid] = {"s_t": t["s_t"],
                          "cases": sorted([c["input"], c["expected"]] for c in t["cases"])}
            key["tasks"].setdefault(tid, {"index": assign[tid],
                                          "case_situations_source_order":
                                              [c["situation"] for c in t["cases"]]})
            key["tasks"][tid][f"{run}_case_order"] = case_order
        payload_hashes[run] = hashlib.sha256(
            json.dumps(canon, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    if payload_hashes["run1"] != payload_hashes["run2"]:
        sys.exit("the two packages are not the same measurement object; refusing to build")

    for tid in sorted(assign):
        n = len(tasks[assign[tid]]["cases"])
        tmpl["tasks"][tid] = {
            "J1": [{"case": i, "determined": None, "quote": "", "confidence": None}
                   for i in range(1, n + 1)],
            "notes": ""}

    for run in RUNS:
        pkg = out / f"{run}_package"
        (pkg / "answers_template.json").write_text(json.dumps(tmpl, indent=2))
        (pkg / "INSTRUCTIONS.md").write_text(INSTRUCTIONS)
        (pkg / "PACKET_FINGERPRINT").write_text(payload_hashes[run] + "\n")

    key["canonical_payload_sha256"] = payload_hashes
    (out / "sealed").mkdir(parents=True, exist_ok=True)
    (out / "sealed" / "_KEY_DO_NOT_SHOW_CODERS.json").write_text(
        json.dumps(key, indent=2, ensure_ascii=False))
    return key
