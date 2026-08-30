"""Amendment 3 clause-7 adversarial fixtures for the Study-3 native resubmission gate.

Everything below is synthetic; no formal artifact is read or written. Each fixture is one
of the behaviours the ruling requires the gate to prove, plus the binding/refusal edges.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys

from resubmission_gate_study3 import gate

n_ok = n_fail = 0


def check(name: str, ok: bool) -> None:
    global n_ok, n_fail
    print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    n_ok, n_fail = n_ok + ok, n_fail + (not ok)


def mk_task(desc: str = "Reads one configuration value from the mapping.",
            policy: str | None = "Never read outside the given mapping.",
            failure: dict | None = None, edits: list | None = None) -> dict:
    return {"spec": {"description": desc, "context": "Used by the loader.",
                     "arguments": "cfg — the mapping; name — the key to read.",
                     "return": "The stored value.", "raise": "KeyError when absent.",
                     "security_policy": policy},
            "edits": edits if edits is not None else [],
            "sufficiency_evidence": [{"case": "A1", "sentence": "The stored value."}],
            "failure": failure, "notes": ""}


BASE = {"schema_version": "study3-writer-v1", "writer_id": "writer-1",
        "tasks": {"W01": mk_task(),
                  "W02": mk_task(failure={"code": "F1_LIST_COUPLING", "at_case": "B1",
                                          "detail": "every phrasing couples",
                                          "quotes": ["the mapping"]})}}


def raw(obj: dict) -> bytes:
    return json.dumps(obj, indent=1, ensure_ascii=False).encode()


def rep(anchor: bytes, *flags: tuple) -> dict:
    return {"submission_sha256": hashlib.sha256(anchor).hexdigest(),
            "issues": [{"code": c, "task": t, "message": ""} for c, t in flags]}


def main() -> None:
    # ---- accepted repairs (clause 7 items 1–3 + 11) --------------------------------
    fenced = b"```json\n" + raw(BASE) + b"\n```"
    r = gate(fenced, rep(fenced, ("INVALID_SERIALIZATION", None)), raw(BASE))
    check("pure serialization repair accepted", r["verdict"] == "ACCEPT_REPAIRED")
    check("repaired substantive hashes identical to first anchor (serialization)",
          all(v["substantive_hash_resub"] == v["substantive_hash_anchor"]
              and v["candidate_hash_resub"] == v["candidate_hash_anchor"]
              for v in r["per_task"].values()))

    a2 = copy.deepcopy(BASE)
    a2["writer_id"] = ""
    a2_raw = raw(a2)
    r = gate(a2_raw, rep(a2_raw, ("MISSING_REQUIRED_METADATA", None)), raw(BASE))
    check("legal metadata completion accepted", r["verdict"] == "ACCEPT_REPAIRED")
    check("untouched tasks stay ACCEPT_FIRST under metadata repair",
          all(v["outcome"] == "ACCEPT_FIRST" for v in r["per_task"].values()))

    a3 = copy.deepcopy(BASE)
    a3["tasks"]["W01"]["edits"] = [{"Field": "description", "original": "old clause",
                                    "action": "removed", "replacement": "", "why": "opens B1"}]
    b3 = copy.deepcopy(a3)
    b3["tasks"]["W01"]["edits"][0] = {"field": "description", "original": "old clause",
                                      "action": "removed", "replacement": "", "why": "opens B1"}
    a3_raw = raw(a3)
    r = gate(a3_raw, rep(a3_raw, ("PROVENANCE_SHAPE_ERROR", "W01")), raw(b3))
    check("legal provenance bookkeeping repair accepted", r["verdict"] == "ACCEPT_REPAIRED")
    check("repaired task marked ACCEPT_REPAIRED, substance identical",
          r["per_task"]["W01"]["outcome"] == "ACCEPT_REPAIRED"
          and r["per_task"]["W01"]["substantive_hash_resub"]
          == r["per_task"]["W01"]["substantive_hash_anchor"])

    # ---- substantive rejections (items 4–9) ----------------------------------------
    def rejected(mutate, name):
        m = copy.deepcopy(BASE)
        mutate(m)
        r = gate(fenced, rep(fenced, ("INVALID_SERIALIZATION", None)), raw(m))
        check(name, r["verdict"] == "REJECTED_RESUBMISSION" and not r["accepted"])

    rejected(lambda m: m["tasks"]["W01"]["spec"].__setitem__(
        "description", m["tasks"]["W01"]["spec"]["description"] + "x"),
        "one-character description change rejected")
    rejected(lambda m: m["tasks"]["W01"]["spec"].__setitem__("security_policy", None),
             "security_policy string->null rejected")
    nullpol = copy.deepcopy(BASE)
    nullpol["tasks"]["W01"]["spec"]["security_policy"] = None
    np_raw = b"```json\n" + raw(nullpol) + b"\n```"
    r = gate(np_raw, rep(np_raw, ("INVALID_SERIALIZATION", None)), raw(BASE))
    check("security_policy null->string rejected", r["verdict"] == "REJECTED_RESUBMISSION")
    rejected(lambda m: m["tasks"]["W01"].__setitem__(
        "failure", {"code": "F3_PREAMBLE_CARRIER", "at_case": "B1", "detail": "d",
                    "quotes": ["the mapping"]}),
        "obstruction none->F* rejected")
    rejected(lambda m: m["tasks"]["W02"]["failure"]["quotes"].__setitem__(0, "a new quote"),
             "quoted evidence change rejected")
    rejected(lambda m: m["tasks"]["W02"]["failure"].__setitem__("detail", "new rationale"),
             "rationale change rejected")
    rejected(lambda m: m["tasks"]["W02"].__setitem__("failure", None),
             "writer success/failure declaration change rejected")
    rejected(lambda m: m["tasks"].pop("W02"), "task removal rejected")
    rejected(lambda m: m["tasks"].__setitem__("W03", mk_task()), "task addition rejected")

    # ---- no unfrozen repair class, ever (item 10) ----------------------------------
    clean = raw(BASE)
    r = gate(clean, rep(clean, ("QUOTE_NOT_LOCATABLE", "W02")), raw(BASE))
    check("unrepairable flag ends the pathway (no A4 invented)",
          r["verdict"] == "UNREPAIRABLE_FIRST_SUBMISSION" and not r["accepted"])
    r = gate(clean, rep(clean, ("SOME_FUTURE_CODE", "W01")), raw(BASE))
    check("unknown validator code is unrepairable, never a new class",
          r["verdict"] == "UNREPAIRABLE_FIRST_SUBMISSION")
    r = gate(fenced, rep(fenced, ("MISSING_REQUIRED_METADATA", None)), raw(BASE))
    check("repair class used without its licensing flag rejected",
          r["verdict"] == "REJECTED_RESUBMISSION"
          and any("without a licensing" in h for h in r["hard_failures"]))

    # ---- binding and refusal edges ---------------------------------------------------
    r = gate(clean, {"submission_sha256": "0" * 64, "issues": []}, raw(BASE))
    check("report not bound to anchor refused", r["verdict"] == "REJECTED_RESUBMISSION")
    r = gate(clean, rep(clean), raw(BASE))
    check("zero flags: ACCEPT_FIRST, resubmission refused",
          r["verdict"] == "ACCEPT_FIRST" and not r["accepted"])
    garbage = b"not json at all, no braces"
    r = gate(garbage, rep(garbage, ("INVALID_SERIALIZATION", None)), raw(BASE))
    check("unrecoverable anchor is UNREPAIRABLE, never re-authored",
          r["verdict"] == "UNREPAIRABLE_FIRST_SUBMISSION")
    r = gate(clean, rep(clean, ("MISSING_REQUIRED_METADATA", None)),
             raw({**BASE, "writer_id": "writer-2"}))
    check("non-empty writer_id mutation rejected (completion-only)",
          r["verdict"] == "REJECTED_RESUBMISSION")

    print(f"\n{n_ok} ok, {n_fail} failed")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
