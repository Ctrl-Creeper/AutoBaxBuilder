"""CWEval replication — sample-size arithmetic, exactly the frozen precision rule.

Rule (Study-1 protocol §6.1, fixed before any CWEval work): worst-case 95% half-width
<= 0.10 on the safety stratum, computed with the then-available ICC planning values.
Inputs allowed: the frame's own structural counts and the two frozen Study-1 ICC
planning values (0.577 / 0.572) — the sole SeCodePLT-derived quantities admitted, per
the frozen §6.1. No prevalence value enters; worst-case means p = 0.5.

Cluster = family (language variants share specification content).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
ICC_PLANNING = (0.577, 0.572)   # frozen Study-1 per-run ICC planning values
HALF_WIDTH_TARGET = 0.10
Z, P_WORST = 1.96, 0.5

frame = json.loads((OUT / "cweval_frame.json").read_text())
fams = frame["families"]
sec = [f["n_security"] for f in fams.values()]
n_fam, n_sec = len(sec), sum(sec)
m_bar = n_sec / n_fam

n_eff_needed = (Z / HALF_WIDTH_TARGET) ** 2 * P_WORST * (1 - P_WORST)

result = {"rule": "worst-case (p=0.5) 95% half-width <= 0.10 on the safety stratum",
          "cluster": "family", "frame": {"families": n_fam, "security_cases": n_sec,
                                         "mean_security_cases_per_family": m_bar},
          "icc_planning_values": ICC_PLANNING, "n_eff_needed": n_eff_needed, "by_icc": {}}

for icc in ICC_PLANNING:
    deff = 1 + (m_bar - 1) * icc
    need_cases = n_eff_needed * deff
    need_fams = math.ceil(need_cases / m_bar)
    census_n_eff = n_sec / deff
    census_hw = Z * math.sqrt(P_WORST * (1 - P_WORST) / census_n_eff)
    result["by_icc"][str(icc)] = {
        "design_effect": deff, "security_cases_required": need_cases,
        "families_required": need_fams, "families_available": n_fam,
        "target_attainable": need_fams <= n_fam,
        "census_achieved_worst_case_half_width": census_hw}

worst = result["by_icc"][str(max(ICC_PLANNING))]
result["conclusion"] = (
    "The frozen precision target is NOT attainable on this benchmark: "
    f"{worst['families_required']} families would be required and {n_fam} exist. "
    "The mechanical resolution is a census of the entire eligible frame; the achieved "
    f"worst-case planning half-width is ±{worst['census_achieved_worst_case_half_width']:.3f}. "
    "Recorded as GAP-1 in the protocol: §6.1 fixed the precision rule but did not "
    "prescribe the insufficient-frame branch; census is the only choice-free completion.")

(OUT / "sample_size_arithmetic.json").write_text(json.dumps(result, indent=2))
for icc, v in result["by_icc"].items():
    print(f"ICC {icc}: DEFF {v['design_effect']:.3f}  need {v['security_cases_required']:.0f} "
          f"cases / {v['families_required']} families (have {n_fam})  "
          f"census half-width ±{v['census_achieved_worst_case_half_width']:.3f}")
print("\n" + result["conclusion"])
