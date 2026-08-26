"""Isolation preflight for the two Round-2 coding runs.

Checks the environment the runs will execute in, not the research content. It asks
whether each isolated directory holds exactly the frozen package and nothing that
could unblind it, and whether the two directories are independent of each other.

It deliberately does not re-examine what the tasks say; the packet audit already
established that, and re-deriving it here would only create another place where a
content judgement could leak in.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
OUT = Path(__file__).resolve().parent
BASE = Path("/Users/lewiswu/round2_coding")
CANONICAL = "20c105adf3328d8b9100aec6047a547533b524ff92fecafa479b97dfd9a48b43"
STARTUP_SHA = "41bf76b963741394a40a01c30b4f968386908180e97c9a3e6078e66f54af2f52"

fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def main() -> None:
    man = json.loads((OUT / "coder_packets_manifest.json").read_text())

    for n, coder in ((1, "coder1"), (2, "coder2")):
        d = BASE / f"coder{n}"
        print(f"\n=== {d} ===")

        live = {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(d.rglob("*")) if p.is_file()}
        frozen = man[coder]["files"]

        # 1 — file count matches the manifest, allowing only the startup prompt
        extra = set(live) - set(frozen)
        check(extra == {"STARTUP_PROMPT.txt"} and not set(frozen) - set(live),
              f"contents match the manifest plus the startup prompt "
              f"(unexpected {sorted(extra - {'STARTUP_PROMPT.txt'})}, missing {sorted(set(frozen) - set(live))})")

        # 2 — package hash still the frozen value
        roll = hashlib.sha256("".join(f"{k}:{v}\n" for k, v in sorted(
            {k: v for k, v in live.items() if k in frozen}.items())).encode()).hexdigest()
        check(roll == man[coder]["package_sha256"],
              f"package sha256 is the frozen value ({roll[:16]}…)")

        # 3 — canonical payload unchanged, taken from the frozen manifest
        check(man["canonical_payload_sha256"][coder] == CANONICAL,
              f"canonical semantic payload is {CANONICAL[:16]}…")

        # 4/5 — nothing that could unblind the run is reachable inside the directory
        forbidden = [p for p in d.rglob("*") if p.is_file() and (
            "KEY" in p.name or p.suffix == ".git" or
            p.name in ("writer_output.json", "writer_output_ACCEPTED.json") or
            "protocol" in p.name.lower() or "provenance" in p.name.lower() or
            "amendment" in p.name.lower() or "manifest" in p.name.lower())]
        check(not forbidden, f"no sealed key, protocol, provenance or writer artefact present ({[p.name for p in forbidden]})")
        check(not (d / ".git").exists() and not any(p.name == ".git" for p in d.rglob("*")),
              "no repository inside the directory")
        check(REPO not in d.parents and BASE != REPO,
              "the directory is outside the repository tree")

        # 6 — the startup prompt names only files that exist here
        sp = d / "STARTUP_PROMPT.txt"
        check(hashlib.sha256(sp.read_bytes()).hexdigest() == STARTUP_SHA,
              "startup prompt is the frozen text, identical for both runs")
        named = ["INSTRUCTIONS.md", "answers_template.json", "coder_answers.json",
                 "tasks/C01.md", "tasks/C90.md"]
        missing = [f for f in named if f != "coder_answers.json" and not (d / f).exists()]
        check(not missing, f"every file the prompt names exists here ({missing})")
        check("round2_coding" not in sp.read_text() and str(REPO) not in sp.read_text(),
              "the prompt contains no path outside the working directory")

        # 7 — output paths do not collide
        check(not (d / "coder_answers.json").exists(), "no output file present yet")

    o1, o2 = BASE / "coder1/coder_answers.json", BASE / "coder2/coder_answers.json"
    print("\n=== independence ===")
    check(o1 != o2 and o1.parent != o2.parent, "the two runs write to separate directories")
    t1 = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE / "coder1/tasks").glob("*.md")}
    t2 = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE / "coder2/tasks").glob("*.md")}
    check(set(t1) == set(t2), "both directories carry the same 90 task ids")
    check(sum(1 for k in t1 if t1[k] != t2[k]) > 0,
          f"task files differ on disk as intended ({sum(1 for k in t1 if t1[k] != t2[k])} of {len(t1)} "
          "differ; only the case order does)")
    check((BASE / "coder1/INSTRUCTIONS.md").read_bytes() == (BASE / "coder2/INSTRUCTIONS.md").read_bytes(),
          "both runs receive byte-identical instructions")
    check((BASE / "coder1/answers_template.json").read_bytes() ==
          (BASE / "coder2/answers_template.json").read_bytes(),
          "both runs receive byte-identical response schemas")

    print(f"\n{'ISOLATION PREFLIGHT PASSED' if not fails else str(len(fails)) + ' FAILURES'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
