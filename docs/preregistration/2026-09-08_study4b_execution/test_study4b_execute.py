from __future__ import annotations

import math

import pytest

try:
    import study4b_execute as execute
except ModuleNotFoundError:
    execute = None


TASKS = [
    {
        "ds_task_id": "Q01",
        "source_index": 101,
        "s_sha256": "s1",
        "sprime_sha256": "sp1",
    },
    {
        "ds_task_id": "Q02",
        "source_index": 202,
        "s_sha256": "s2",
        "sprime_sha256": "sp2",
    },
]


def test_schedule_matches_task_level_assignment_and_paired_execution_blocks():
    assert execute is not None, "study4b_execute is not implemented"
    schedule = execute.build_request_schedule(TASKS, repeats=4, root_seed=12345)

    assert len(schedule) == 16
    assert [row["request_order"] for row in schedule] == list(range(1, 17))
    assert len({row["request_id"] for row in schedule}) == 16
    assert len({row["seed"] for row in schedule}) == 16

    for start in range(0, len(schedule), 2):
        pair = schedule[start : start + 2]
        assert {row["condition"] for row in pair} == {"S", "Sprime"}
        assert len({row["block_id"] for row in pair}) == 1
        assert len({row["ds_task_id"] for row in pair}) == 1
        assert len({row["repeat"] for row in pair}) == 1

    for task_id in ("Q01", "Q02"):
        rows = [row for row in schedule if row["ds_task_id"] == task_id]
        s_arms = {row["seed_arm"] for row in rows if row["condition"] == "S"}
        sp_arms = {
            row["seed_arm"] for row in rows if row["condition"] == "Sprime"
        }
        assert len(s_arms) == 1
        assert len(sp_arms) == 1
        assert s_arms != sp_arms
        assert {row["repeat"] for row in rows} == {1, 2, 3, 4}


def test_schedule_is_deterministic_for_the_frozen_seed():
    assert execute is not None, "study4b_execute is not implemented"
    assert execute.build_request_schedule(TASKS, 4, 777) == execute.build_request_schedule(
        TASKS, 4, 777
    )
    assert execute.build_request_schedule(TASKS, 4, 777) != execute.build_request_schedule(
        TASKS, 4, 778
    )


def test_generation_payload_has_only_the_frozen_user_message_and_parameters():
    assert execute is not None, "study4b_execute is not implemented"
    payload = execute.generation_payload("implement me", seed=99)

    assert payload == {
        "model": "Ornith-1.5-35B-A3B-Abliterated-MLX-4bit",
        "messages": [{"role": "user", "content": "implement me"}],
        "temperature": 0.2,
        "top_p": 1.0,
        "max_tokens": 8192,
        "chat_template_kwargs": {"enable_thinking": False},
        "seed": 99,
        "stream": False,
    }


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_only_frozen_http_statuses_are_retryable(status: int):
    assert execute is not None, "study4b_execute is not implemented"
    assert execute.is_retryable_http_status(status)


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422, 501])
def test_other_http_statuses_are_hard_stops(status: int):
    assert execute is not None, "study4b_execute is not implemented"
    assert not execute.is_retryable_http_status(status)


def test_exact_sign_flip_p_value_uses_task_level_differences():
    assert execute is not None, "study4b_execute is not implemented"
    # Of the 2^3 sign assignments for three equal non-zero task effects,
    # only all-positive and all-negative are as extreme as the observed sum.
    assert execute.exact_sign_flip_p_value([0.25, 0.25, 0.25]) == pytest.approx(0.25)
    assert execute.exact_sign_flip_p_value([0.0, 0.0]) == 1.0


def test_task_equal_aggregate_is_not_sensitive_to_row_order():
    assert execute is not None, "study4b_execute is not implemented"
    rows = []
    values = {
        ("Q01", "S"): [1, 1, 1, 1],
        ("Q01", "Sprime"): [0, 0, 0, 0],
        ("Q02", "S"): [0, 0, 0, 0],
        ("Q02", "Sprime"): [0, 0, 0, 0],
    }
    for (task_id, condition), outcomes in values.items():
        for repeat, security_pass in enumerate(outcomes, 1):
            rows.append(
                {
                    "ds_task_id": task_id,
                    "condition": condition,
                    "repeat": repeat,
                    "security_pass": security_pass,
                    "capability_pass": 1,
                    "joint_pass": security_pass,
                }
            )

    result = execute.aggregate_endpoints(rows, ["Q01", "Q02"], repeats=4)

    assert result["security"]["rate_S"] == 0.5
    assert result["security"]["rate_Sprime"] == 0.0
    assert result["security"]["delta"] == 0.5
    assert result["security"]["task_differences"] == [1.0, 0.0]
    assert result["capability"]["delta"] == 0.0
    assert math.isfinite(result["security"]["ci_95"][0])
    assert math.isfinite(result["security"]["ci_95"][1])


def test_extract_code_uses_first_fenced_block_or_entire_response():
    assert execute is not None, "study4b_execute is not implemented"
    assert execute.extract_code("before\n```python\nreturn 1\n```\n```\nreturn 2\n```") == "return 1\n"
    assert execute.extract_code("return 3") == "return 3"
