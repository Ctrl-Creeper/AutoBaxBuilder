from pathlib import Path

import pytest

try:
    import study4b_prepare as prepare
except ModuleNotFoundError:
    prepare = None


EXPECTED_DS_IDS = [
    "Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07", "Q08", "Q09",
    "Q10", "Q11", "Q12", "Q13", "Q14", "Q15", "Q16", "Q17", "Q19",
    "Q20", "Q21", "Q22", "Q23", "Q24", "Q25", "Q26", "Q29", "Q30",
    "Q31", "Q32", "Q33", "Q35", "Q36", "Q37", "Q38", "Q39", "Q40",
    "Q41", "Q42", "Q43", "Q44", "Q45", "Q46", "Q47", "Q49", "Q50",
    "Q51", "Q52",
]


def test_extract_specification_returns_exact_bytes_between_markers(tmp_path: Path):
    assert prepare is not None, "study4b_prepare is not implemented"
    packet = tmp_path / "Q01.md"
    packet.write_text(
        "header\n<<<BEGIN SPECIFICATION S>>>\nline one\nline two\n"
        "<<<END SPECIFICATION S>>>\nfooter\n"
    )

    assert prepare.extract_specification(packet) == "line one\nline two"


def test_extract_specification_rejects_ambiguous_markers(tmp_path: Path):
    assert prepare is not None, "study4b_prepare is not implemented"
    packet = tmp_path / "bad.md"
    packet.write_text("<<<BEGIN SPECIFICATION S>>>\na\n")

    with pytest.raises(ValueError, match="exactly one marker pair"):
        prepare.extract_specification(packet)


def test_restore_uses_exact_frozen_ds47_without_ur_tasks():
    assert prepare is not None, "study4b_prepare is not implemented"
    restoration = prepare.restore_ds47_pairs()
    rows = restoration["pairs"]

    assert [row["ds_task_id"] for row in rows] == EXPECTED_DS_IDS
    assert len({row["source_index"] for row in rows}) == 47
    assert all(row["s_run1_equals_run2"] for row in rows)
    assert all(row["sprime_run1_equals_run2"] for row in rows)
    assert all(row["oracle_matches_sealed_materialization"] for row in rows)


def test_context_gate_includes_output_and_wrapper_reserves():
    assert prepare is not None, "study4b_prepare is not implemented"
    largest_fitting_prompt = (
        prepare.CONTEXT_LIMIT
        - prepare.MAX_OUTPUT_TOKENS
        - prepare.WRAPPER_RESERVE
    )

    assert prepare.fits_context(largest_fitting_prompt)
    assert not prepare.fits_context(largest_fitting_prompt + 1)


def test_model_directory_verification_rejects_file_drift(tmp_path: Path):
    assert prepare is not None, "study4b_prepare is not implemented"
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "a.txt").write_text("alpha")
    expected = [
        {
            "name": "a.txt",
            "bytes": 5,
            "sha256": "8ed3f6ad685b959ead7022518e1af76cd816f8e8ec7ccdda1ed4018e8f2223f8",
        }
    ]
    prepare.verify_model_directory(model_dir, expected)

    (model_dir / "a.txt").write_text("changed")
    with pytest.raises(RuntimeError, match="model directory or weights drift"):
        prepare.verify_model_directory(model_dir, expected)
