"""Study 3 — tooling self-test on synthetic fixtures only.

No formal-sample content, no real coder output, no formal draw: every record, frame,
submission, certificate and candidate below is synthetic. The only real files touched are
the frozen protocol/frame (hash pins), the benchmark's shipped instruct.py (the byte-
verified S_t generator), and this tooling's own source. A sys.addaudithook open-trace is
recorded to selftest_open_trace.json for the data-flow audit.

Covers the freeze-approval list: SRSWOR reproducibility + formal-draw guards; packet
construction (payload equality, sentinels, templates); submission validation accept/reject;
eligibility both-agree/either-agree and m = 0; writer candidate invariants (param drop, new
field, failure-without-quotes, candidate-always-ships); S′ immutability by construction;
DS-only / VO-only / UR-heavy / DS∧VO hard stop; writer failure and coupling structurally
unable to become VO; invalid certificates → UR; CP boundary cases; banned-vocabulary guard.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

OPENED: list[str] = []


def _hook(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, Path)):
        OPENED.append(str(args[0]))


sys.addaudithook(_hook)

from study3_pins import (EDITABLE_FIELDS, RUNS, align_runs,  # noqa: E402
                         param_names, sprime_record)
from select_study3_sample import build_manifest, draw  # noqa: E402
from packet_build import BEGIN_S, END_S, build_packages  # noqa: E402
from build_study1_packets import reconstruct_s_t  # noqa: E402
from derive_eligibility import eligibility  # noqa: E402
from derive_ds import derive as derive_ds  # noqa: E402
from vo_certificates import derive as derive_vo, immutable_only, vo_struct  # noqa: E402
from validate_study3_candidate import check_task, problems as cand_problems  # noqa: E402
from build_study3_writer_handoff import render_writer_task  # noqa: E402
from score_study3 import (BANNED_OUTPUT, classify, cp_interval,  # noqa: E402
                          map_ds_to_baseline, score)

PASS = FAIL = 0


def check(name: str, ok: bool) -> None:
    global PASS, FAIL
    print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    PASS, FAIL = PASS + ok, FAIL + (not ok)


def synth_rec(idx: int) -> dict:
    return {
        "index": idx,
        "task_description": {
            "function_name": f"calc_total_{idx}",
            "description": f"Add x and y. Sums above CAP{idx} are clamped to CAP{idx}.",
            "context": f"- CAP{idx}: an integer cap defined in the setup code.",
            "arguments": "- x: int, the first addend.\n- y: int, the second addend.",
            "return": "The integer sum.",
            "raise": "ValueError if any input is negative.",
            "security_policy": "Reject negative inputs to prevent underflow.",
        },
        "unittest": {
            "setup": f"CAP{idx} = {idx * 10}",
            "testcases": ("testcases = {'capability': [({'x': 1, 'y': 2}, 3)], "
                          "'safety': [({'x': -1, 'y': 0}, ValueError)]}"),
        },
        "ground_truth": {"code_before": f"\ndef calc_total_{idx}(x, y):"},
    }


def synth_key_and_subs(spec: dict[str, dict[str, list[tuple[bool, bool]]]]):
    """spec: tid -> {situation: [(run1_det, run2_det), ...]}. Quotes are placeholders."""
    key = {"tasks": {}}
    subs = {r: {"tasks": {}} for r in RUNS}
    for tid, by_sit in spec.items():
        sits = [s for s, pairs in by_sit.items() for _ in pairs]
        flat = [p for pairs in by_sit.values() for p in pairs]
        n = len(flat)
        key["tasks"][tid] = {"index": int(tid[1:]),
                             "case_situations_source_order": sits,
                             "run1_case_order": list(range(n)),
                             "run2_case_order": list(range(n))}
        for ri, run in enumerate(RUNS):
            subs[run]["tasks"][tid] = {"J1": [
                {"case": i + 1, "determined": flat[i][ri],
                 "quote": "q" if flat[i][ri] else "", "confidence": "clear"}
                for i in range(n)], "notes": ""}
    return key, subs


def main() -> None:  # noqa: PLR0915
    tmp = Path(tempfile.mkdtemp(prefix="study3_selftest_"))

    # ---- 1. selection tool -------------------------------------------------
    proto = tmp / "synthetic_protocol.md"
    proto.write_text("synthetic protocol for the self-test\n")
    frame_p = tmp / "synthetic_frame.json"
    frame_p.write_text(json.dumps({"frame": list(range(1000, 1200))}))
    import hashlib
    sha = hashlib.sha256(proto.read_bytes()).hexdigest()
    d1 = draw(list(range(1000, 1200)), int(sha[:8], 16), 90)
    d2 = draw(list(range(1000, 1200)), int(sha[:8], 16), 90)
    check("SRSWOR reproducible from seed", d1 == d2)
    check("SRSWOR without replacement", len(set(d1)) == 90)
    check("SRSWOR draws only frame members", set(d1) <= set(range(1000, 1200)))
    m1 = build_manifest(proto, sha, frame_p, json.loads(frame_p.read_text()),
                        int(sha[:8], 16), 90)
    check("manifest records seed derivation and CR-1 sampling clause",
          "no supplemental draw" in m1["sampling"] and m1["seed"] == int(sha[:8], 16))
    r = subprocess.run([sys.executable, str(HERE / "select_study3_sample.py")],
                       capture_output=True, text=True)
    check("formal draw refused without approval flag",
          r.returncode != 0 and "not yet approved" in r.stderr + r.stdout)
    for guard_file in ("build_study3_baseline_packets.py", "build_study3_sprime_packets.py",
                       "build_study3_writer_handoff.py", "materialize_cases.py"):
        r = subprocess.run([sys.executable, str(HERE / guard_file)],
                           capture_output=True, text=True)
        check(f"{guard_file} refused without approval flag",
              r.returncode != 0 and "not yet approved" in r.stderr + r.stdout)

    # ---- 1b. case materialization (GAP-3 Amendment 2) on synthetic records --
    from materialize_cases import host_resources, materialize
    recs = {i: synth_rec(i) for i in (1, 2, 3)}
    m_tasks, m_public, m_fails = materialize(recs, [1, 2, 3])
    check("materializer: clean synthetic records materialize without failure",
          not m_fails and sorted(m_tasks) == ["1", "2", "3"])
    check("materializer: public artifact carries hashes/metadata, never raw case values",
          all(set(v) == {"case_count", "situations", "case_hashes", "host_resources_sha256"}
              for v in m_public.values())
          and all(len(h["input_sha256"]) == 64 for v in m_public.values()
                  for h in v["case_hashes"]))
    broken = {9: synth_rec(9)}
    broken[9]["unittest"]["testcases"] = "raise RuntimeError('no testcases')"
    b_tasks, _, b_fails = materialize(broken, [9])
    check("materializer: any task failure is reported and nothing is materialized for it "
          "(clause-11 hard-stop input)", not b_tasks and len(b_fails) == 1)
    hr_rec = synth_rec(4)
    hr_rec["unittest"]["testcases"] = ('testcases = {"capability": [({"p": "/etc/hosts"}, 1)],'
                                       ' "safety": []}')
    check("materializer: host-resource path literals are hashed for provenance",
          "/etc/hosts" in host_resources(hr_rec))
    cases_by_index = {i: m_tasks[str(i)]["cases"] for i in (1, 2, 3)}

    # ---- 2. packet construction on synthetic records + manifest cases -------
    pkg_dir = tmp / "packets"
    key = build_packages(recs, [1, 2, 3], pkg_dir, schema_version="study3-baseline-run-v1",
                         task_seed_name="baseline_task_order",
                         run_seed_names={"run1": "baseline_run1_cases",
                                         "run2": "baseline_run2_cases"},
                         key_extra={"stage": "selftest"},
                         cases_by_index=cases_by_index)
    try:
        build_packages(recs, [1, 2, 3], tmp / "p2", schema_version="study3-baseline-run-v1",
                       task_seed_name="baseline_task_order",
                       run_seed_names={"run1": "baseline_run1_cases",
                                       "run2": "baseline_run2_cases"},
                       key_extra={"stage": "selftest"}, cases_by_index={1: cases_by_index[1]})
        check("builder refuses a task missing from the case manifest (no re-extraction)",
              False)
    except SystemExit as e:
        check("builder refuses a task missing from the case manifest (no re-extraction)",
              "case manifest" in str(e))
    check("canonical payloads identical across runs",
          key["canonical_payload_sha256"]["run1"] == key["canonical_payload_sha256"]["run2"])
    t1 = (pkg_dir / "run1_package/tasks/P01.md").read_text()
    check("sentinel markers present", BEGIN_S in t1 and END_S in t1)
    check("packet shows no label, no provenance, no derivation status",
          all(w not in t1.lower() for w in ("capability", "safety", "baseline", "candidate",
                                            "writer", "derived", "study")))
    tmpl = json.loads((pkg_dir / "run1_package/answers_template.json").read_text())
    check("template covers all tasks with J1-only entries",
          set(tmpl["tasks"]) == {"P01", "P02", "P03"}
          and all(set(t) == {"J1", "notes"} for t in tmpl["tasks"].values()))

    # ---- 3. submission validator -------------------------------------------
    def fill(quote_ok: bool) -> dict:
        sub = json.loads(json.dumps(tmpl))
        sub["coder_id"] = "selftest"
        sub["packet_fingerprint_sha256"] = (pkg_dir / "run1_package/PACKET_FINGERPRINT"
                                            ).read_text().strip()
        for tid, t in sub["tasks"].items():
            s_t = (pkg_dir / f"run1_package/tasks/{tid}.md").read_text(
                ).split(BEGIN_S)[1].split(END_S)[0]
            good = s_t.strip().splitlines()[0].strip()
            for e in t["J1"]:
                e["determined"] = True
                e["quote"] = good if quote_ok else "this text is nowhere in S"
                e["confidence"] = "clear"
        return sub

    sub_p = tmp / "sub.json"
    sub_p.write_text(json.dumps(fill(True)))
    r = subprocess.run([sys.executable, str(HERE / "validate_study3_submission.py"),
                        str(sub_p), "--package", str(pkg_dir / "run1_package")],
                       capture_output=True, text=True)
    check("validator accepts a complete, quote-locating submission", r.returncode == 0)
    sub_p.write_text(json.dumps(fill(False)))
    r = subprocess.run([sys.executable, str(HERE / "validate_study3_submission.py"),
                        str(sub_p), "--package", str(pkg_dir / "run1_package")],
                       capture_output=True, text=True)
    check("validator rejects quotes that do not locate in S",
          r.returncode != 0 and "does not locate" in r.stdout)

    # ---- 4. eligibility: both-agree, either-agree, m = 0 -------------------
    key_e, subs_e = synth_key_and_subs({
        "P01": {"capability": [(True, True)], "safety": [(True, True)]},   # eligible
        "P02": {"capability": [(True, True)], "safety": [(True, False)]},  # either only
        "P03": {"capability": [(True, True)], "safety": [(False, False)]},  # blind
    })
    per = eligibility(align_runs(key_e, subs_e))
    check("both-agree eligibility requires the same case determined in both runs",
          per["P01"]["eligible_both_agree"] and not per["P02"]["eligible_both_agree"])
    check("either-agree recorded as sensitivity only",
          per["P02"]["eligible_either_agree_sensitivity_only"]
          and not per["P03"]["eligible_either_agree_sensitivity_only"])
    key_z, subs_z = synth_key_and_subs(
        {"P01": {"capability": [(True, True)], "safety": [(False, True)]}})
    per_z = eligibility(align_runs(key_z, subs_z))
    check("m = 0 fixture yields zero eligible",
          sum(v["eligible_both_agree"] for v in per_z.values()) == 0)

    # ---- 5. writer render + candidate invariants ---------------------------
    wmd = render_writer_task("W01", recs[1], [
        {"situation": "capability", "input": "{'x': 1, 'y': 2}", "expected": "3"},
        {"situation": "safety", "input": "{'x': -1, 'y': 0}", "expected": "ValueError"}])
    check("writer task shows labelled lists, signature, frozen setup",
          "List A" in wmd and "List B" in wmd and "def calc_total_1(x, y):" in wmd
          and "CAP1 = 10" in wmd)
    good_cand = {"spec": {**{f: f"rewritten {f}, mentioning x and y." for f in EDITABLE_FIELDS},
                          "security_policy": None},
                 "edits": [{"field": "security_policy", "original": "o", "action": "removed",
                            "replacement": "", "why": "w"}],
                 "sufficiency_evidence": [{"case": "A1", "sentence": "s"}],
                 "failure": None, "notes": ""}
    params = param_names(recs[1])
    check("param extraction follows the frozen Round-2 rule", params == ["x", "y"])

    def cand_problem_count(cand) -> int:
        cand_problems.clear()
        check_task("W01", json.loads(json.dumps(cand)), wmd, params)
        return len(cand_problems)

    check("valid candidate passes mechanical invariants", cand_problem_count(good_cand) == 0)
    bad = json.loads(json.dumps(good_cand))
    bad["spec"]["arguments"] = "- x: int, the only addend that matters."
    check("dropped parameter mention rejected (constraint C)", cand_problem_count(bad) > 0)
    bad = json.loads(json.dumps(good_cand))
    bad["spec"]["signature"] = "def other():"
    check("new spec field rejected (schema is frozen)", cand_problem_count(bad) > 0)
    bad = json.loads(json.dumps(good_cand))
    bad["failure"] = {"code": "F1_LIST_COUPLING", "at_case": "B1", "detail": "d", "quotes": []}
    check("failure declaration without quotations rejected", cand_problem_count(bad) > 0)
    bad = json.loads(json.dumps(good_cand))
    bad["spec"]["description"] = ""
    bad["failure"] = {"code": "F1_LIST_COUPLING", "at_case": "B1", "detail": "d",
                      "quotes": ["List A"]}
    check("failure never excuses a missing candidate (always ships)",
          cand_problem_count(bad) > 0)
    bad = json.loads(json.dumps(good_cand))
    bad["failure"] = {"code": "F9_MADE_UP", "at_case": "B1", "detail": "d", "quotes": ["List A"]}
    check("failure code outside the fixed taxonomy rejected", cand_problem_count(bad) > 0)

    # ---- 6. S′ immutability by construction --------------------------------
    sp = sprime_record(recs[1], good_cand)
    check("S′ record: setup, name, cases copied byte-identically from the original",
          sp["unittest"] == recs[1]["unittest"]
          and sp["task_description"]["function_name"] ==
          recs[1]["task_description"]["function_name"])
    check("security_policy null → no Security Policy line in the S′ render",
          "Security Policy" not in reconstruct_s_t(sp))
    kept = json.loads(json.dumps(good_cand))
    kept["spec"]["security_policy"] = "kept policy text"
    check("security_policy kept → rendered",
          "Security Policy: kept policy text" in reconstruct_s_t(sprime_record(recs[1], kept)))

    # ---- 7. DS derivation ---------------------------------------------------
    key_d, subs_d = synth_key_and_subs({
        "Q01": {"capability": [(True, True)], "safety": [(False, False)]},  # DS
        "Q02": {"capability": [(True, True)], "safety": [(True, True)]},    # safety determined
        "Q03": {"capability": [(False, True)], "safety": [(False, False)]},  # cap gap run1
    })
    dsd = derive_ds(align_runs(key_d, subs_d))
    check("DS requires both runs' full profile", dsd["Q01"]["ds_both_runs"]
          and not dsd["Q02"]["ds_both_runs"] and not dsd["Q03"]["ds_both_runs"])
    check("either-run profile is sensitivity only",
          dsd["Q03"]["ds_either_run_sensitivity_only"] and
          not dsd["Q02"]["ds_either_run_sensitivity_only"])

    # ---- 8. VO certificates -------------------------------------------------
    segments = {"setup": "Setup Code:\n```python\nCAP1 = 10\n```",
                "closing_instruction": "Please implement the function.",
                "function_name": "Function Name: calc_total_1",
                "description": "Description: sums above CAP1 are clamped."}
    check("immutable-only accepts setup / closing / name / parameter quotes",
          immutable_only("CAP1 = 10", segments, ["x"]) and
          immutable_only("x", segments, ["x"]))
    check("immutable-only rejects editable-prose quotes",
          not immutable_only("sums above CAP1 are clamped", segments, ["x"]))

    def vo_rows(q1: str, q2: str):
        key_v, subs_v = synth_key_and_subs(
            {"P01": {"safety": [(True, True)], "capability": [(True, True)]}})
        rows = align_runs(key_v, subs_v)
        for r in rows:
            if r["situation"] == "safety":
                r["run1_quote"], r["run2_quote"] = q1, q2
        return rows

    check("VO-STRUCT when both runs quote an immutable carrier",
          vo_struct(vo_rows("CAP1 = 10", "CAP1 = 10"), "P01", segments, ["x"]) is not None)
    check("no VO-STRUCT when one run's quote is editable prose",
          vo_struct(vo_rows("CAP1 = 10", "sums above CAP1 are clamped"), "P01",
                    segments, ["x"]) is None)

    ddir = tmp / "vo_defect"
    ddir.mkdir()
    seg_map = {"P01": segments}
    par_map = {"P01": ["x"]}
    case_map = {"P01": ["{'x': -1} ValueError"]}
    ur_rows = vo_rows("sums above CAP1 are clamped", "sums above CAP1 are clamped")

    res = derive_vo(ur_rows, ["P01"], seg_map, par_map, case_map, ddir)
    check("no certificate, no VO — the task stays UR", res["vo_tasks"] == {})
    (ddir / "P01_certificate.json").write_text(json.dumps(
        {"task": "P01", "quotes": ["CAP1 = 10", "{'x': -1} ValueError"],
         "contradiction": "setup cap contradicts the listed case"}))
    res = derive_vo(ur_rows, ["P01"], seg_map, par_map, case_map, ddir)
    check("certificate without independent attestation rejected → UR",
          res["vo_tasks"] == {} and any("attestation" in c["reason"]
                                        for c in res["rejected_claims"]))
    (ddir / "P01_attestation.json").write_text(json.dumps(
        {"task": "P01", "verifier_id": "fresh-session", "confirmed": False, "basis": "quotes"}))
    res = derive_vo(ur_rows, ["P01"], seg_map, par_map, case_map, ddir)
    check("unconfirmed attestation rejected → UR", res["vo_tasks"] == {})
    (ddir / "P01_attestation.json").write_text(json.dumps(
        {"task": "P01", "verifier_id": "fresh-session", "confirmed": True, "basis": "quotes"}))
    res = derive_vo(ur_rows, ["P01"], seg_map, par_map, case_map, ddir)
    check("confirmed, quote-locating certificate accepted as VO-DEFECT",
          res["vo_tasks"].get("P01", {}).get("class") == "VO-DEFECT")
    (ddir / "P01_certificate.json").write_text(json.dumps(
        {"task": "P01", "quotes": ["the writer could not find any witness"],
         "contradiction": "writer failed"}))
    res = derive_vo(ur_rows, ["P01"], seg_map, par_map, case_map, ddir)
    check("certificate whose quotes do not locate in immutable materials rejected → UR",
          res["vo_tasks"] == {})
    check("VO derivation structurally blind to writer output (no such parameter)",
          "writer" not in inspect.signature(derive_vo).parameters)

    # ---- 9. scorer ----------------------------------------------------------
    def elig_fx(tids):
        return {"m": len(tids), "n_drawn": 90, "eligible_task_ids": tids,
                "eligible_indices": {t: int(t[1:]) for t in tids},
                "either_agree_count_sensitivity_only": len(tids)}

    def ds_fx(tids, ds_set, either=()):
        return {"per_task": {t: {"ds_both_runs": t in ds_set,
                                 "ds_either_run_sensitivity_only": t in ds_set or t in either}
                             for t in tids}}

    tids = [f"P{i:02d}" for i in range(1, 11)]
    r_ds = score(elig_fx(tids), ds_fx(tids, set(tids)), {"vo_tasks": {},
                                                         "rejected_claims": []}, None)
    check("DS-only: region [1,1], CP upper boundary handled",
          r_ds["L0_sample_identification_region"]["region"] == [1.0, 1.0]
          and r_ds["L1_sampling_clopper_pearson"]["pi_ds_cp95"][1] == 1.0)
    vo_all = {"vo_tasks": {t: {"class": "VO-STRUCT"} for t in tids}, "rejected_claims": []}
    r_vo = score(elig_fx(tids), ds_fx(tids, set()), vo_all, None)
    check("VO-only: region [0,0], CP lower boundary handled",
          r_vo["L0_sample_identification_region"]["region"] == [0.0, 0.0]
          and r_vo["L1_sampling_clopper_pearson"]["pi_ds_cp95"][0] == 0.0)
    r_ur = score(elig_fx(tids), ds_fx(tids, {"P01"}, either={"P02"}),
                 {"vo_tasks": {"P02": {"class": "VO-STRUCT"}}, "rejected_claims": []}, None)
    check("UR-heavy: shares sum to 1 and region width = P_hat_UR",
          abs(sum(r_ur["classification"]["shares"].values()) - 1) < 1e-12
          and abs((r_ur["L0_sample_identification_region"]["region"][1]
                   - r_ur["L0_sample_identification_region"]["region"][0])
                  - r_ur["classification"]["shares"]["P_hat_UR"]) < 1e-12)
    check("L2 either-run share reported apart from the both-runs definition",
          r_ur["L2_measurement_sensitivity"]["ds_either_run_share_sensitivity_only"]
          > r_ur["L2_measurement_sensitivity"]["ds_both_runs_definition_share"])
    r_m0 = score({"m": 0, "n_drawn": 90, "eligible_task_ids": [],
                  "either_agree_count_sensitivity_only": 0}, {}, {}, None)
    check("m = 0 branch: every layer reports 'no eligible tasks'",
          r_m0["no_eligible_tasks"] and all(
              "no eligible tasks" in str(r_m0[k]) for k in
              ("classification", "L0_sample_identification_region",
               "L1_sampling_clopper_pearson", "L2_measurement_sensitivity")))
    try:
        score(elig_fx(["P01"]), ds_fx(["P01"], {"P01"}),
              {"vo_tasks": {"P01": {"class": "VO-STRUCT"}}, "rejected_claims": []}, None)
        check("DS ∧ VO triggers the hard stop", False)
    except SystemExit as e:
        check("DS ∧ VO triggers the hard stop", "HARD STOP" in str(e))
    check("classify() is structurally blind to writer declarations",
          set(inspect.signature(classify).parameters) == {"ds", "vo"})
    writer_fx = {"tasks": {"W01": {"failure": {"code": "F1_LIST_COUPLING", "at_case": "B1",
                                               "detail": "d", "quotes": ["q"]}},
                           "W02": {"failure": None}}}
    r_w = score(elig_fx(tids), ds_fx(tids, set()), {"vo_tasks": {}, "rejected_claims": []},
                writer_fx)
    check("writer failure / coupling lands UR, reported descriptively only",
          r_w["classification"]["counts"]["UR"] == 10
          and r_w["descriptive"]["coupling_claims_F1"] == 1)

    # GAP-5 / Interpretation Note 2 routing
    r_pi = score(elig_fx(tids), {"per_task": {}},
                 {"vo_tasks": {"P03": {"class": "VO-STRUCT"}}, "rejected_claims": []},
                 None, procedure_invalid=frozenset(tids))
    pi = r_pi["descriptive"]["procedure_invalid_candidate"]
    check("procedure-invalid path: never DS, VO via certificate, remainder UR",
          r_pi["classification"]["counts"] == {"DS": 0, "VO": 1, "UR": 9})
    check("procedure_invalid_candidate is a diagnostic count, not a fourth class",
          pi["count"] == 10
          and "procedure_invalid" not in r_pi["classification"]["counts"]
          and sum(r_pi["classification"]["counts"].values()) == 10)
    check("procedure-invalid tasks stay in m (denominator unchanged)",
          r_pi["m_measured_eligible"] == 10
          and r_pi["L0_sample_identification_region"]["region"] == [0.0, 0.9])
    try:
        score(elig_fx(["P01"]), ds_fx(["P01"], set()),
              {"vo_tasks": {}, "rejected_claims": []}, None,
              procedure_invalid=frozenset(["P01"]))
        check("procedure-invalid task inside the S′ derivation triggers the hard stop",
              False)
    except SystemExit as e:
        check("procedure-invalid task inside the S′ derivation triggers the hard stop",
              "HARD STOP" in str(e))

    check("CP boundaries: k=0 lower is 0, k=n upper is 1, n=0 is vacuous [0,1]",
          cp_interval(0, 10)[0] == 0.0 and cp_interval(10, 10)[1] == 1.0
          and cp_interval(0, 0) == [0.0, 1.0])
    clean = json.dumps(r_ur).lower()
    check("real scorer output free of banned inference vocabulary",
          not any(b in clean for b in BANNED_OUTPUT))
    poisoned = json.dumps({**r_ur, "bootstrap_ci": [0, 1]}).lower()
    check("banned-vocabulary guard catches a poisoned output",
          any(b in poisoned for b in BANNED_OUTPUT))
    mapped = map_ds_to_baseline(
        {"per_task": {"Q01": {"ds_both_runs": True,
                              "ds_either_run_sensitivity_only": True}},
         "task_index": {"Q01": 7}},
        {"eligible_task_ids": ["P05"], "eligible_indices": {"P05": 7}})
    check("P↔Q namespace mapping via shared source index",
          mapped["per_task"]["P05"]["ds_both_runs"])

    # ---- trace + verdict ----------------------------------------------------
    banned_paths = ["2026-08-27_study1_execution/results", "2026-08-27_study1_execution/sub",
                    "2026-08-27_study1_execution/sealed", "2026-08-25_writer_handoff",
                    "2026-08-26_round2_coder_packets", "round2_selection.json",
                    "results_study1_prevalence"]
    touched = sorted({p for p in OPENED if any(b in p for b in banned_paths)})
    check("open trace touches no Study-1 result/submission, Round-2, or writer artifact",
          not touched)
    (HERE / "selftest_open_trace.json").write_text(json.dumps(
        {"opens": sorted(set(OPENED)), "banned_touched": touched}, indent=1))

    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
