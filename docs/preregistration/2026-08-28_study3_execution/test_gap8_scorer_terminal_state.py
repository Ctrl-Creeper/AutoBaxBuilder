#!/usr/bin/env python3
"""GAP-8 fixtures for the fixed scorer terminal-state resolver."""

from __future__ import annotations

import ast
import hashlib
import inspect
import shutil
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

import score_study3


HERE = Path(__file__).resolve().parent

CURRENT_FORMAL_BUNDLE = (
    "writer_handoff/GATE_UNREPAIRABLE_FROZEN.json",
    "writer_handoff/SHA256SUMS_WRITER_FROZEN",
    "GAP6_writer_instrument_contract_audit.md",
    "GAP6_REPAIR_RECORD.md",
    "SHA256SUMS_GAP6",
    "writer_handoff/WRITER_RUN2_TERMINAL_STATE.md",
    "writer_handoff/SHA256SUMS_WRITER_FROZEN_RUN2",
    "writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json",
    "sprime_packet_build_provenance.json",
    "SHA256SUMS_SPRIME_PACKET_BUILD",
    "submissions_sprime/SHA256SUMS_SPRIME_FROZEN",
    "ds_derivation.json",
    "SHA256SUMS_DS_ONLY",
    "vo_certificates.json",
    "VO_STRUCT_EXECUTION_AUDIT.json",
    "VO_STRUCT_EXECUTION_PROVENANCE.json",
    "VO_STRUCT_EXECUTABILITY_AUDIT.md",
    "SHA256SUMS_VO_STRUCT_FROZEN",
    "vo_certificates.py",
)

RUN1_FORMAL_INVALID_BUNDLE = (
    "writer_handoff/GATE_UNREPAIRABLE_FROZEN.json",
    "writer_handoff/SHA256SUMS_WRITER_FROZEN",
)

GAP6_DISPOSITION_BUNDLE = (
    "GAP6_writer_instrument_contract_audit.md",
    "GAP6_REPAIR_RECORD.md",
    "SHA256SUMS_GAP6",
)


def copy_files(dst: Path, paths: tuple[str, ...]) -> None:
    for rel in paths:
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / rel, target)


@contextmanager
def resolver_root(path: Path):
    original = score_study3.HERE
    score_study3.HERE = path
    try:
        yield
    finally:
        score_study3.HERE = original


class Gap8ResolverTests(unittest.TestCase):
    def test_historical_run1_and_formal_run2_resolve_to_run2(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, CURRENT_FORMAL_BUNDLE)
            self.assertTrue(
                hasattr(score_study3, "resolve_terminal_state"),
                "bounded GAP-8 resolver is missing",
            )
            with resolver_root(root):
                state = score_study3.resolve_terminal_state()
            self.assertEqual(state, "FORMAL_RUN2_ACCEPTED")

    def test_run1_gate_hash_mismatch_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, CURRENT_FORMAL_BUNDLE)
            gate = root / "writer_handoff/GATE_UNREPAIRABLE_FROZEN.json"
            gate.write_bytes(gate.read_bytes() + b"\n")
            with resolver_root(root), self.assertRaisesRegex(SystemExit, "Run-1 gate"):
                score_study3.resolve_terminal_state()

    def test_run1_gate_manifest_missing_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, CURRENT_FORMAL_BUNDLE)
            (root / "writer_handoff/SHA256SUMS_WRITER_FROZEN").unlink()
            with resolver_root(root), self.assertRaisesRegex(SystemExit, "Run-1 manifest"):
                score_study3.resolve_terminal_state()

    def test_missing_gap6_disposition_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, CURRENT_FORMAL_BUNDLE)
            (root / "GAP6_REPAIR_RECORD.md").unlink()
            with resolver_root(root), self.assertRaisesRegex(SystemExit, "GAP-6 disposition"):
                score_study3.resolve_terminal_state()

    def test_missing_run2_terminal_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, CURRENT_FORMAL_BUNDLE)
            (root / "writer_handoff/WRITER_RUN2_TERMINAL_STATE.md").unlink()
            with resolver_root(root), self.assertRaisesRegex(SystemExit, "Run-2 terminal"):
                score_study3.resolve_terminal_state()

    def test_ds_artifact_provenance_mismatch_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, CURRENT_FORMAL_BUNDLE)
            ds = root / "ds_derivation.json"
            ds.write_bytes(ds.read_bytes() + b"\n")
            with resolver_root(root), self.assertRaisesRegex(SystemExit, "DS derivation"):
                score_study3.resolve_terminal_state()

    def test_vo_artifact_provenance_mismatch_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, CURRENT_FORMAL_BUNDLE)
            vo = root / "vo_certificates.json"
            vo.write_bytes(vo.read_bytes() + b"\n")
            with resolver_root(root), self.assertRaisesRegex(SystemExit, "VO-STRUCT"):
                score_study3.resolve_terminal_state()

    def test_historical_gate_without_complete_run2_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, RUN1_FORMAL_INVALID_BUNDLE + GAP6_DISPOSITION_BUNDLE)
            with resolver_root(root), self.assertRaisesRegex(
                SystemExit, "unknown terminal combination"
            ):
                score_study3.resolve_terminal_state()

    def test_run2_accepted_artifact_hash_mismatch_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, CURRENT_FORMAL_BUNDLE)
            accepted = root / "writer_handoff/submissions/writer_output_ACCEPT_FIRST_RUN2.json"
            accepted.write_bytes(accepted.read_bytes() + b"\n")
            with resolver_root(root), self.assertRaisesRegex(
                SystemExit, "Run-2 accepted artifact"
            ):
                score_study3.resolve_terminal_state()

    def test_formal_procedure_invalid_path_remains_available(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, RUN1_FORMAL_INVALID_BUNDLE)
            with resolver_root(root):
                state = score_study3.resolve_terminal_state()
            self.assertEqual(state, "FORMAL_PROCEDURE_INVALID")

    def test_formal_ds_and_formal_procedure_invalid_hard_stop(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_files(root, RUN1_FORMAL_INVALID_BUNDLE)
            (root / "ds_derivation.json").write_text("{}\n")
            with resolver_root(root), self.assertRaisesRegex(SystemExit, "GAP-6 disposition"):
                score_study3.resolve_terminal_state()

    def test_empty_terminal_combination_hard_stops(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            with resolver_root(root), self.assertRaisesRegex(
                SystemExit, "no recognized formal constructive terminal state"
            ):
                score_study3.resolve_terminal_state()

    def test_resolver_accepts_no_arguments(self) -> None:
        self.assertEqual(list(inspect.signature(score_study3.resolve_terminal_state).parameters), [])

    def test_substantive_function_sources_are_byte_identical(self) -> None:
        expected = {
            "cp_interval": "7525022292ad3693b063b5b9a814a3705330d1c3abc3f130ffd0844dd52bcf4a",
            "map_ds_to_baseline": "0d7659e562c868dd217f9129a9c568d9f9444acbb95e2d393b917feeb3456b74",
            "classify": "d7dd69b6e933f229904c136737c470a68253a823aa2a791331322f3e3a0f4aff",
            "score": "51e2e4cdb394a8a07506309bd9c1cf0bdb82b5182f8da3979345ef88fc3582e6",
        }
        source = (HERE / "score_study3.py").read_text()
        tree = ast.parse(source)
        actual = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in expected:
                function_source = ast.get_source_segment(source, node).encode()
                actual[node.name] = hashlib.sha256(function_source).hexdigest()
        self.assertEqual(actual, expected)

    def test_main_delegates_only_terminal_resolution_to_gap8_resolver(self) -> None:
        tree = ast.parse((HERE / "score_study3.py").read_text())
        main = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        called_names = {
            node.func.id for node in ast.walk(main)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        loaded_names = {
            node.id for node in ast.walk(main)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        self.assertIn("resolve_terminal_state", called_names)
        self.assertIn("FORMAL_RUN2_ACCEPTED", loaded_names)
        self.assertIn("FORMAL_PROCEDURE_INVALID", loaded_names)


if __name__ == "__main__":
    unittest.main()
