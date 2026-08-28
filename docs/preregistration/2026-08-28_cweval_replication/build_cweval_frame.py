"""CWEval replication — mechanical eligible-frame construction (phase 1, no coding).

Enumerates task files exactly the way the benchmark's own generate.py does (files
ending `_task` with an extension in the shipped LANGS, skipping __pycache__), joins
each to its `*_test.py`, counts cases by the benchmark's OWN pytest marks, groups
into families (cwe id + variant number, across language variants), and excludes the
`cwe_943_0` family per the frozen prior-exposure ruling in the Study-1 protocol §6.

Nothing here reads a specification for content, judges anything, or touches any
SeCodePLT result value. Case counts come from mark occurrences — a structural count,
recorded per file together with the counting method so a zero or an oddity is a
reported fact, not a silent repair.

Every enumerated source file is hash-pinned into the frame manifest, along with the
prompt-pipeline files that define the model-visible S_t boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

CWEVAL = Path("/Users/lewiswu/网络安全/CWEval")
BENCHMARK = CWEVAL / "benchmark"
LANGS = ("c", "cpp", "go", "py", "js")          # commons.py LANGS, pinned below
EXCLUDED_FAMILY = "cwe_943_0"                    # frozen prior-exposure exclusion
PIPELINE_PINS = ("cweval/generate.py", "cweval/ppt/__init__.py", "cweval/commons.py")
OUT = Path(__file__).resolve().parent


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def family_of(stem: str) -> str:
    """cwe_<id>_<variant>[_<lang>]_task -> cwe_<id>_<variant>."""
    m = re.match(r"(cwe_\d+_\d+)(?:_[a-z]+)?_task$", stem)
    return m.group(1) if m else stem


def main() -> None:
    tasks = []
    for p in sorted(BENCHMARK.rglob("*")):
        if "__pycache__" in p.parts or not p.is_file():
            continue
        stem, ext = p.stem, p.suffix[1:]
        if not stem.endswith("_task") or ext not in LANGS:
            continue
        test = p.with_name(stem.replace("_task", "_test") + ".py")
        entry = {
            "task_file": str(p.relative_to(CWEVAL)),
            "task_sha256": sha(p),
            "lang": ext,
            "family": family_of(stem),
            "test_file": str(test.relative_to(CWEVAL)) if test.exists() else None,
        }
        if test.exists():
            t = test.read_text()
            entry["test_sha256"] = sha(test)
            entry["n_functionality_marks"] = t.count("pytest.mark.functionality")
            entry["n_security_marks"] = t.count("pytest.mark.security")
            entry["count_method"] = "textual occurrences of the benchmark's own marks"
        tasks.append(entry)

    families: dict[str, list[dict]] = {}
    for t in tasks:
        families.setdefault(t["family"], []).append(t)

    eligible = {f: v for f, v in sorted(families.items()) if f != EXCLUDED_FAMILY}
    excluded = {f: [t["task_file"] for t in v] for f, v in families.items()
                if f == EXCLUDED_FAMILY}

    issues = [t["task_file"] for f, v in eligible.items() for t in v
              if t.get("test_file") is None or t.get("n_security_marks", 0) == 0
              or t.get("n_functionality_marks", 0) == 0]

    frame = {
        "benchmark_repo": str(CWEVAL),
        "enumeration_rule": "generate.py _get_cases: '*_task' stem, extension in LANGS, "
                            "skip __pycache__",
        "langs": LANGS,
        "pipeline_pins": {rel: sha(CWEVAL / rel) for rel in PIPELINE_PINS},
        "excluded_families": excluded,
        "exclusion_rule": "cwe_943_0 family: prior exposure disclosed and pre-excluded in the "
                          "frozen Study-1 protocol §6",
        "n_task_files_enumerated": len(tasks),
        "n_task_files_eligible": sum(len(v) for v in eligible.values()),
        "n_families_eligible": len(eligible),
        "case_totals_eligible": {
            "functionality": sum(t.get("n_functionality_marks", 0)
                                 for v in eligible.values() for t in v),
            "security": sum(t.get("n_security_marks", 0)
                            for v in eligible.values() for t in v)},
        "files_with_structural_issues": issues,
        "families": {f: {"n_task_files": len(v),
                         "langs": sorted(t["lang"] for t in v),
                         "n_functionality": sum(t.get("n_functionality_marks", 0) for t in v),
                         "n_security": sum(t.get("n_security_marks", 0) for t in v),
                         "task_files": v}
                     for f, v in eligible.items()},
    }
    (OUT / "cweval_frame.json").write_text(json.dumps(frame, indent=2))

    fams = frame["families"]
    sec = [f["n_security"] for f in fams.values()]
    print(f"task files enumerated   {len(tasks)}  (eligible {frame['n_task_files_eligible']})")
    print(f"families eligible       {len(fams)}   (excluded: {list(excluded) or 'none'})")
    print(f"cases eligible          functionality {frame['case_totals_eligible']['functionality']}"
          f"  security {frame['case_totals_eligible']['security']}")
    print(f"security cases/family   mean {sum(sec)/len(sec):.2f}  min {min(sec)}  max {max(sec)}")
    print(f"langs per family        {sorted(set(len(f['langs']) for f in fams.values()))}")
    print(f"structural issues       {len(issues)}: {issues[:5]}")
    sys.exit(0)


if __name__ == "__main__":
    main()
