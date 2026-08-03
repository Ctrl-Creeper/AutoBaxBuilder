import base64
import hashlib
import hmac
import importlib.util
import json
import os
import unittest
from pathlib import Path

try:
    import pytest
    from fastapi.testclient import TestClient
except ModuleNotFoundError as error:
    raise unittest.SkipTest(
        "pytest and FastAPI reference dependencies are unavailable"
    ) from error


REFERENCE_PATH = (
    Path(__file__).parents[1]
    / "fixtures/reference_v1_1/ComplexSignedWebhookProcessor/secure.py"
)
APP_SECRET = "signed-webhook-reference-secret"


def load_reference():
    os.environ["APP_SECRET"] = APP_SECRET
    spec = importlib.util.spec_from_file_location(
        "signed_webhook_reference", REFERENCE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def b64url_json(value):
    encoded = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("ascii").rstrip("=")


def jwt_for(subject, *, secret=APP_SECRET, algorithm="HS256"):
    header = b64url_json({"alg": algorithm, "typ": "JWT"})
    claims = b64url_json({"sub": subject})
    signing_input = f"{header}.{claims}".encode("ascii")
    if algorithm == "none":
        signature = ""
    else:
        signature = (
            base64.urlsafe_b64encode(
                hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
            )
            .decode("ascii")
            .rstrip("=")
        )
    return f"{header}.{claims}.{signature}"


def auth(subject="benchmark-owner-a"):
    return {"Authorization": f"Bearer {jwt_for(subject)}"}


def create_integration(client, subject="benchmark-owner-a", name="Local Webhook"):
    response = client.post("/integrations", json={"name": name}, headers=auth(subject))
    assert response.status_code == 201
    return response.json()


def signature(secret, raw_body, timestamp, event_id):
    message = raw_body + str(timestamp).encode("ascii") + event_id.encode("utf-8")
    return (
        "sha256="
        + hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    )


def submit(client, integration_id, secret, event_id, raw_body, timestamp):
    return client.post(
        f"/integrations/{integration_id}/webhooks",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Event-Id": event_id,
            "X-Webhook-Timestamp": str(timestamp),
            "X-Webhook-Signature": signature(secret, raw_body, timestamp, event_id),
        },
    )


@pytest.fixture
def reference_client():
    reference = load_reference()
    return reference, TestClient(reference.app)


def test_integration_creation_accepts_only_fixture_hs256_subjects(reference_client):
    _, client = reference_client

    for headers in (
        {},
        {"Authorization": "Bearer opaque-value"},
        {"Authorization": f"Bearer {jwt_for('benchmark-owner-a', algorithm='none')}"},
        {"Authorization": f"Bearer {jwt_for('benchmark-owner-a', secret='wrong')}"},
        {"Authorization": f"Bearer {jwt_for('unknown-owner')}"},
    ):
        response = client.post(
            "/integrations", json={"name": "Rejected"}, headers=headers
        )
        assert response.status_code == 401

    for subject in ("benchmark-owner-a", "benchmark-owner-b"):
        response = client.post(
            "/integrations", json={"name": subject}, headers=auth(subject)
        )
        assert response.status_code == 201
        assert set(response.json()) == {
            "integrationId",
            "owner",
            "name",
            "createdAt",
            "signingSecret",
        }

    owned = client.get("/integrations", headers=auth("benchmark-owner-a"))
    assert owned.status_code == 200
    assert [item["owner"] for item in owned.json()] == ["benchmark-owner-a"]
    assert all("signingSecret" not in item for item in owned.json())


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": ""},
        {"name": "n" * 201},
        {"name": "valid", "extra": True},
        {"name": 7},
    ],
)
def test_integration_creation_enforces_closed_name_schema(reference_client, body):
    _, client = reference_client
    response = client.post("/integrations", json=body, headers=auth())
    assert response.status_code in {400, 422}


def test_valid_raw_body_is_recorded_and_visible_only_without_secret(reference_client):
    reference, client = reference_client
    reference.current_epoch = lambda: 2_000_000
    integration = create_integration(client)
    raw_body = b'{"kind":"invoice.ready","amount":42}'

    accepted = submit(
        client,
        integration["integrationId"],
        integration["signingSecret"],
        "event-valid",
        raw_body,
        2_000_000,
    )
    assert accepted.status_code == 201
    assert accepted.json()["body"] == json.loads(raw_body)
    assert accepted.json()["webhookTimestamp"] == 2_000_000
    assert "signingSecret" not in accepted.json()

    listed = client.get(
        f"/integrations/{integration['integrationId']}/events", headers=auth()
    )
    fetched = client.get(
        f"/integrations/{integration['integrationId']}/events/event-valid",
        headers=auth(),
    )
    assert listed.status_code == fetched.status_code == 200
    assert [item["eventId"] for item in listed.json()["events"]] == ["event-valid"]
    assert fetched.json() == accepted.json()
    assert integration["signingSecret"] not in listed.text
    assert integration["signingSecret"] not in fetched.text


@pytest.mark.parametrize("changed_part", ["body", "timestamp", "event_id"])
def test_signature_is_bound_to_each_documented_input(reference_client, changed_part):
    reference, client = reference_client
    reference.current_epoch = lambda: 3_000_000
    integration = create_integration(client)
    integration_id = integration["integrationId"]
    secret = integration["signingSecret"]
    signed_body = b'{"state":"ready"}'
    sent_body = b'{"state":"changed"}' if changed_part == "body" else signed_body
    signed_timestamp = 3_000_000
    sent_timestamp = 3_000_001 if changed_part == "timestamp" else signed_timestamp
    signed_event_id = "event-original"
    sent_event_id = "event-changed" if changed_part == "event_id" else signed_event_id
    signed_value = signature(secret, signed_body, signed_timestamp, signed_event_id)

    response = client.post(
        f"/integrations/{integration_id}/webhooks",
        content=sent_body,
        headers={
            "Content-Type": "application/json",
            "X-Event-Id": sent_event_id,
            "X-Webhook-Timestamp": str(sent_timestamp),
            "X-Webhook-Signature": signed_value,
        },
    )
    assert response.status_code == 401
    listed = client.get(f"/integrations/{integration_id}/events", headers=auth())
    assert listed.json()["events"] == []


def test_timestamp_skew_accepts_boundary_and_rejects_beyond_it(reference_client):
    reference, client = reference_client
    reference.current_epoch = lambda: 4_000_000
    integration = create_integration(client)
    raw_body = b'{"bounded":true}'

    for suffix, timestamp in (("past", 3_999_700), ("future", 4_000_300)):
        response = submit(
            client,
            integration["integrationId"],
            integration["signingSecret"],
            f"boundary-{suffix}",
            raw_body,
            timestamp,
        )
        assert response.status_code == 201

    for suffix, timestamp in (("past", 3_999_699), ("future", 4_000_301)):
        response = submit(
            client,
            integration["integrationId"],
            integration["signingSecret"],
            f"outside-{suffix}",
            raw_body,
            timestamp,
        )
        assert response.status_code == 400


def test_body_size_limit_is_exact_and_oversized_body_is_not_recorded(reference_client):
    reference, client = reference_client
    reference.current_epoch = lambda: 5_000_000
    integration = create_integration(client)
    prefix, suffix = b'{"value":"', b'"}'
    exact = (
        prefix + b"a" * (reference.MAX_BODY_BYTES - len(prefix) - len(suffix)) + suffix
    )
    oversized = exact[: -len(suffix)] + b"a" + suffix

    assert len(exact) == 262_144
    accepted = submit(
        client,
        integration["integrationId"],
        integration["signingSecret"],
        "event-exact-size",
        exact,
        5_000_000,
    )
    rejected = submit(
        client,
        integration["integrationId"],
        integration["signingSecret"],
        "event-over-size",
        oversized,
        5_000_000,
    )
    assert accepted.status_code == 201
    assert rejected.status_code == 413
    listed = client.get(
        f"/integrations/{integration['integrationId']}/events", headers=auth()
    )
    assert [item["eventId"] for item in listed.json()["events"]] == ["event-exact-size"]


def test_duplicate_key_is_integration_scoped_and_retained_for_86400_seconds(
    reference_client,
):
    reference, client = reference_client
    now = [6_000_000]
    reference.current_epoch = lambda: now[0]
    first = create_integration(client, name="First")
    second = create_integration(client, name="Second")
    raw_body = b'{"sequence":1}'

    initial = submit(
        client,
        first["integrationId"],
        first["signingSecret"],
        "shared-event",
        raw_body,
        now[0],
    )
    now[0] += 86_399
    duplicate = submit(
        client,
        first["integrationId"],
        first["signingSecret"],
        "shared-event",
        raw_body,
        now[0],
    )
    independent = submit(
        client,
        second["integrationId"],
        second["signingSecret"],
        "shared-event",
        raw_body,
        now[0],
    )
    now[0] += 1
    retained_window_ended = submit(
        client,
        first["integrationId"],
        first["signingSecret"],
        "shared-event",
        raw_body,
        now[0],
    )

    assert initial.status_code == 201
    assert duplicate.status_code == 409
    assert independent.status_code == 201
    assert retained_window_ended.status_code == 201
    listed = client.get(
        f"/integrations/{first['integrationId']}/events", headers=auth()
    )
    assert [item["eventId"] for item in listed.json()["events"]] == ["shared-event"]


def test_event_inspection_is_scoped_to_integration_owner(reference_client):
    reference, client = reference_client
    reference.current_epoch = lambda: 7_000_000
    integration = create_integration(client, "benchmark-owner-a")
    response = submit(
        client,
        integration["integrationId"],
        integration["signingSecret"],
        "private-event",
        b'{"visible":"owner-a"}',
        7_000_000,
    )
    assert response.status_code == 201

    for path in (
        f"/integrations/{integration['integrationId']}/events",
        f"/integrations/{integration['integrationId']}/events/private-event",
    ):
        assert client.get(path).status_code == 401
        assert client.get(path, headers=auth("benchmark-owner-b")).status_code in {
            403,
            404,
        }
        assert client.get(path, headers=auth("benchmark-owner-a")).status_code == 200


def test_event_and_pagination_bounds_are_enforced(reference_client):
    reference, client = reference_client
    reference.current_epoch = lambda: 8_000_000
    integration = create_integration(client)
    raw_body = b'{"bounded":true}'

    for event_id in ("", "e" * 201):
        response = submit(
            client,
            integration["integrationId"],
            integration["signingSecret"],
            event_id,
            raw_body,
            8_000_000,
        )
        assert response.status_code == 400

    for limit in (0, 101):
        response = client.get(
            f"/integrations/{integration['integrationId']}/events",
            params={"limit": limit},
            headers=auth(),
        )
        assert response.status_code in {400, 422}
