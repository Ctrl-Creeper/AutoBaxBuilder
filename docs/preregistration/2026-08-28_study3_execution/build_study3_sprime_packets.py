"""Study 3 — S′ verification packet builder (two fresh blinded J1 runs over the candidates).

Consumes the frozen, validator-accepted writer output (hash-verified against
writer_handoff/SHA256SUMS_WRITER_FROZEN) and the original benchmark records. For each
measured-eligible task it assembles an S′ record via study3_pins.sprime_record — function
name, setup, and every case copied from the original record object, only the prose fields
(and optional security_policy) taken from the candidate — and renders it through the
benchmark's own shipped get_prompt, byte-checked against the mechanical re-rendering. The
frozen components therefore cannot drift: immutability holds by construction, not by trust.

Blinding (protocol §5): the verification coders never learn that S′ is derived, that a
baseline exists, what any case kind is, or anything about the writer — the packets carry
fresh shuffled task ids (Q…), the standard J1 instructions, and nothing else. No verifier
faces an existential question; they answer bounded per-case questions only. Writer
declarations do NOT enter the packets; they stay in the frozen writer record.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from study3_pins import (SCHEMA_SPRIME, load_frozen_sums, sha256_file, sprime_record)
from packet_build import build_packages

HERE = Path(__file__).resolve().parent
WRITER_DIR = HERE / "writer_handoff"


def main() -> None:
    if "--approved-packet-build" not in sys.argv:
        sys.exit("The S′ packet build is not yet approved. Runs only with "
                 "--approved-packet-build, after the writer output is frozen.")
    if (HERE / "sprime" / "run1_package").exists():
        sys.exit("sprime/run1_package already exists; a frozen build is never overwritten")

    frozen = load_frozen_sums(WRITER_DIR / "SHA256SUMS_WRITER_FROZEN")
    wpath = WRITER_DIR / "study3_writer_ACCEPTED.json"
    if sha256_file(wpath) != frozen[wpath.name]:
        sys.exit("writer output does not match its frozen hash; refusing to build")
    writer = json.loads(wpath.read_text())
    key_w = json.loads((WRITER_DIR / "sealed/_KEY_DO_NOT_SHOW_WRITER.json").read_text())

    from secodeplt_task_runner import load  # noqa: E402  (benchmark loader only)
    records = {r["index"]: r for r in load(only_stdlib=False)}

    sprime_records = {}
    for wid, task in sorted(writer["tasks"].items()):
        idx = key_w["tasks"][wid]["index"]
        sprime_records[idx] = sprime_record(records[idx], task)

    key = build_packages(
        sprime_records, sorted(sprime_records), HERE / "sprime",
        schema_version=SCHEMA_SPRIME,
        task_seed_name="sprime_task_order",
        run_seed_names={"run1": "sprime_run1_cases", "run2": "sprime_run2_cases"},
        key_extra={"stage": "sprime",
                   "writer_output_sha256": frozen[wpath.name],
                   "eligibility_manifest_sha256": sha256_file(HERE / "eligibility_study3.json")},
        id_prefix="Q")
    n_cases = sum(len(v["case_situations_source_order"]) for v in key["tasks"].values())
    print(f"S′ packets built: {len(key['tasks'])} tasks, {n_cases} cases")
    print(f"payload sha {key['canonical_payload_sha256']['run1'][:16]}… (identical across runs)")


if __name__ == "__main__":
    main()
