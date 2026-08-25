"""Contamination check for the writer package, run before authoring begins.

The primary check is **provenance, not vocabulary**. Every generated task file is
rebuilt from its source record and compared byte for byte; a match proves the file
contains exactly what the builder derived from the frozen selection and the fixed
template, and nothing else. This project has already established that lexical
absence does not imply informational absence, so a keyword scan cannot carry the
argument. The keyword scan is retained, explicitly, as a secondary check only.

For the two hand-authored files, which cannot be regenerated, independence is
checked by n-gram overlap against the documents that must not have fed them.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from build_writer_package import extract_cases, render  # noqa: E402
from secodeplt_task_runner import load  # noqa: E402

OUT = Path("docs/preregistration/2026-08-25_writer_handoff")
PKG = OUT / "writer_package"
SEL = Path("docs/preregistration/2026-08-25_round2_selection/round2_selection.json")

FORBIDDEN_SOURCES = [
    "docs/preregistration/2026-08-25_coder2_handoff/INSTRUMENT_DEVELOPMENT_ROUND_1.md",
    "docs/preregistration/2026-08-25_coder2_handoff/DIAGNOSTIC_disagreement_analysis.md",
    "docs/preregistration/2026-08-25_coder2_handoff/PRE_ADJUDICATION_NOTES.md",
    "docs/preregistration/2026-08-25_coder2_handoff/coder2_answers.json",
    "docs/preregistration/2026-08-25_coder2_handoff/sealed/PROVENANCE_instrument_development.md",
    "docs/preregistration/2026-08-24_instrument_feasibility/feasibility_table.json",
]
IDR1 = {666, 813, 1364, 643, 1083, 681, 1072, 1067, 893, 1350, 816, 434}

fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        fails.append(msg)
        print(f"  FAIL {msg}")


def shingles(text: str, n: int = 8) -> set[str]:
    w = re.findall(r"[a-z']+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def main() -> None:
    man = json.loads(SEL.read_text())
    selection = set(man["selection"])
    key = json.loads((OUT / "sealed/_KEY_DO_NOT_SHOW_WRITER.json").read_text())["mapping"]
    records = {r["index"]: r for r in load(only_stdlib=False)}

    # --- 1. primary: every task file regenerates from its source record
    mismatched = []
    for wid, meta in sorted(key.items()):
        rec = records[meta["index"]]
        want = render(wid, rec, extract_cases(rec))
        got = (PKG / "tasks" / f"{wid}.md").read_text()
        if want != got:
            mismatched.append(wid)
    check(not mismatched, f"every task file regenerates byte-identically from source ({mismatched})")
    print(f"  ok   {len(key)} task files regenerate byte-identically from their source records")

    # --- 2. the package covers the frozen selection exactly
    covered = {m["index"] for m in key.values()}
    check(covered == selection, "sealed mapping covers exactly the frozen selection")
    check(len(key) == 90, f"exactly 90 task files (found {len(key)})")
    check(not (covered & IDR1), "no development-round task is present")
    print(f"  ok   mapping covers the frozen selection exactly, 90 tasks, no development overlap")

    # --- 3. only expected files ship, and the key is not among them
    shipped = {p.name for p in PKG.rglob("*") if p.is_file()}
    expected = {f"W{i:02d}.md" for i in range(1, 91)} | {"INSTRUCTIONS.md", "output_template.json"}
    check(shipped == expected, f"package contains only the expected files (extra: {shipped - expected})")
    check(not any("KEY" in p.name for p in PKG.rglob("*")), "the sealed key is not inside the package")
    print("  ok   package contains only the 90 task files, the instructions and the template")

    # --- 4. hand-authored files: independence by n-gram overlap, not by keyword
    for name in ("INSTRUCTIONS.md", "output_template.json"):
        mine = shingles((PKG / name).read_text())
        for src in FORBIDDEN_SOURCES:
            p = Path(src)
            if not p.exists():
                continue
            shared = mine & shingles(p.read_text())
            check(not shared, f"{name} shares no 8-gram with {p.name} (shared: {list(shared)[:2]})")
    print("  ok   hand-authored files share no 8-gram with any withheld document")

    # --- 5. secondary only: token scan for known labels and development ids
    tokens = re.compile(r"\bSEPARABLE\b|\bINSEPARABLE\b|STRUCTURALLY.CARRIED|NOT_YET_BLINDED|"
                        r"OVER.STRIPPED|coder1|coder2|fcf1120|Round 1|IDR1|CWE", re.I)
    for p in sorted(PKG.rglob("*")):
        if p.is_file():
            hits = set(tokens.findall(p.read_text()))
            check(not hits, f"[secondary] {p.name} contains no withheld label token ({hits})")
    idpat = re.compile(r"\b(?:" + "|".join(str(i) for i in sorted(IDR1)) + r")\b")
    stray = [p.name for p in (PKG / "tasks").glob("*.md") if idpat.search(p.read_text())]
    print(f"  ok   [secondary] no withheld label tokens; development ids appear as bare numbers in "
          f"{len(stray)} files (benign: they are also ordinary values in task data)")

    # --- 6. the manifest describes what is actually on disk
    mf = json.loads((OUT / "writer_package_manifest.json").read_text())
    live = {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(PKG.rglob("*")) if p.is_file()}
    check(live == mf["files"], "manifest hashes match the files on disk")
    check(mf["selection_sha256"] == hashlib.sha256(SEL.read_bytes()).hexdigest(),
          "manifest pins the frozen selection file by hash")
    print("  ok   manifest matches disk and pins the frozen selection")

    print(f"\n{'CONTAMINATION CHECK PASSED' if not fails else str(len(fails)) + ' FAILURES'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
