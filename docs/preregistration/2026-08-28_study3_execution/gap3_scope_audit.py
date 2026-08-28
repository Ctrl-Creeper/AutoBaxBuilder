"""GAP-3 scope audit — outcome-blind, over the entire frozen 764-task Study-3 frame.

Question (ruling D): is P32/source-864 an isolated case, or is environment-dependent
oracle materialization systematic in the frozen extraction interface?

What this does, and all it does:
  1. STATIC dependency scan: AST analysis of each record's setup+testcases SOURCE for
     dependency classes (process execution, filesystem reads, time, randomness,
     environment, network, unordered-collection repr). Source code mechanics only.
  2. DYNAMIC reproducibility probe: the frozen extraction is run twice per record in
     separate subprocesses with different PYTHONHASHSEED values and compared for BYTE
     EQUALITY ONLY. The extracted values are hashed and discarded — never stored, printed,
     read, or classified. Equality of two extractions is a reproducibility fact, not a
     Definition-D outcome (none exist, and none is computed).

Output: task indices, counts, dependency classes, stable/unstable/error flags, and the
overlap with the drawn 90. No oracle value, no case content, no S_t text appears in the
output. No repair rule is developed here.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from study3_pins import FRAME, FRAME_SHA, sha256_file, verify_pin  # noqa: E402

OUT = HERE / "gap3_scope_results.json"

_DUMP = ('\nimport json\nprint("###" + json.dumps([{"situation": s, "input": repr(k), '
         '"expected": getattr(e, "__name__", None) or repr(e)} for s, cs in testcases.items() '
         'for k, e in cs]))\n')

DEP_CLASSES = {
    "proc_exec": {"os.popen", "os.system", "os.exec", "os.spawn", "subprocess",
                  "commands.getoutput", "pty.spawn"},
    "fs_read": {"open", "os.listdir", "os.walk", "os.scandir", "os.stat", "glob",
                "pathlib", "shutil", "io.open", "os.path.getsize", "os.path.getmtime"},
    "time_dep": {"time.time", "time.localtime", "time.gmtime", "time.ctime",
                 "datetime.now", "datetime.utcnow", "date.today", "time.monotonic",
                 "time.perf_counter"},
    "randomness": {"random", "secrets", "uuid", "os.urandom", "numpy.random"},
    "env_dep": {"os.environ", "os.getenv", "platform", "socket.gethostname",
                "getpass", "os.getcwd", "os.uname", "sys.platform"},
    "network": {"socket", "urllib", "requests", "http", "ftplib", "smtplib"},
}


def qualified_names(src: str) -> set[str]:
    """Every dotted name/call target appearing in the source, as prefix-matchable strings."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {"<unparseable>"}
    names = set()

    def dotted(node) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = dotted(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return None

    for node in ast.walk(tree):
        if isinstance(node, (ast.Attribute, ast.Name)):
            d = dotted(node)
            if d:
                names.add(d)
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def static_classes(rec: dict) -> list[str]:
    src = rec["unittest"]["setup"] + "\n" + rec["unittest"]["testcases"]
    names = qualified_names(src)
    hits = []
    for cls, needles in DEP_CLASSES.items():
        for n in names:
            if any(n == w or n.startswith(w + ".") or ("." in w and n.endswith(w))
                   or w in n for w in needles):
                hits.append(cls)
                break
    # unordered-collection repr risk: set displays / set() in the testcase expressions
    if any(isinstance(node, (ast.Set, ast.SetComp)) for node in ast.walk(
            ast.parse(rec["unittest"]["testcases"]))) or "set(" in rec["unittest"]["testcases"]:
        hits.append("unordered_repr")
    return sorted(set(hits))


def extract_hash(rec: dict, hashseed: str) -> tuple[str, str]:
    """(status, sha256-of-dump). Values are hashed and discarded, never inspected."""
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "c.py"
        f.write_text(rec["unittest"]["setup"] + "\n" + rec["unittest"]["testcases"] + _DUMP)
        try:
            r = subprocess.run([sys.executable, str(f)], cwd=t, capture_output=True,
                               text=True, timeout=30,
                               env={"PYTHONHASHSEED": hashseed, "PATH": "/usr/bin:/bin"})
        except subprocess.TimeoutExpired:
            return "timeout", ""
    if r.returncode != 0 or "###" not in r.stdout:
        return "error", ""
    return "ok", hashlib.sha256(r.stdout.split("###", 1)[1].encode()).hexdigest()


def probe(rec: dict) -> dict:
    entry = {"static_classes": static_classes(rec)}
    s1, h1 = extract_hash(rec, "1")
    s2, h2 = extract_hash(rec, "2")
    if s1 == s2 == "ok":
        entry["dynamic"] = "stable" if h1 == h2 else "unstable"
    else:
        entry["dynamic"] = f"extraction_{s1 if s1 != 'ok' else s2}"
    return entry


def main() -> None:
    verify_pin(FRAME, FRAME_SHA, "Study-3 frame")
    frame = json.loads(FRAME.read_text())["frame"]
    selection = set(json.loads((HERE / "selection_study3.json").read_text())["selection"])

    sys.path.insert(0, str(HERE.parents[2] / "scripts"))
    from secodeplt_task_runner import load
    records = {r["index"]: r for r in load(only_stdlib=False)}
    missing = [i for i in frame if i not in records]

    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(probe, records[i]): i for i in frame if i in records}
        for n, fut in enumerate(futs, 1):
            pass
        for fut, idx in futs.items():
            results[str(idx)] = fut.result()

    n = len(results)
    unstable = sorted(int(i) for i, v in results.items() if v["dynamic"] == "unstable")
    errors = sorted(int(i) for i, v in results.items()
                    if v["dynamic"].startswith("extraction_"))
    class_counts: dict[str, int] = {}
    for v in results.values():
        for c in v["static_classes"]:
            class_counts[c] = class_counts.get(c, 0) + 1
    summary = {
        "frame_sha256": FRAME_SHA,
        "n_probed": n, "n_missing_from_loader": len(missing),
        "dynamic": {
            "stable": sum(v["dynamic"] == "stable" for v in results.values()),
            "unstable": len(unstable), "extraction_error_or_timeout": len(errors)},
        "unstable_indices": unstable,
        "unstable_in_drawn_90": sorted(set(unstable) & selection),
        "error_indices": errors,
        "error_in_drawn_90": sorted(set(errors) & selection),
        "static_class_counts": class_counts,
        "proc_exec_indices": sorted(int(i) for i, v in results.items()
                                    if "proc_exec" in v["static_classes"]),
        "note": "outcome-blind: extraction dumps were hashed for byte-equality and "
                "discarded; no oracle value read, stored, or classified",
    }
    OUT.write_text(json.dumps({"summary": summary, "per_task": results}, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    print(f"\nresults sha256 {sha256_file(OUT)}")


if __name__ == "__main__":
    main()
