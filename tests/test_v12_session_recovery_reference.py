import importlib.util
import sys
import unittest
from functools import lru_cache
from pathlib import Path

try:
    import pytest
    from fastapi.testclient import TestClient
except ModuleNotFoundError as error:
    raise unittest.SkipTest(
        "optional host-side FastAPI reference dependencies are not installed"
    ) from error


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "reference_v1_1"


@lru_cache(maxsize=None)
def load_reference(scenario: str):
    path = FIXTURES / scenario / "secure.py"
    module_name = f"{scenario.lower()}_secure"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def sign_in(client: TestClient, username: str, password: str):
    csrf = client.get("/csrf-token").json()["csrfToken"]
    response = client.post(
        "/auth/login",
        headers={"X-CSRF-Token": csrf},
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["csrfToken"], response.json()["profile"]


def test_session_fixture_supports_two_distinct_scoped_profiles():
    reference = load_reference("BeginnerSessionProfile")
    reference.SESSIONS.clear()
    client_a = TestClient(reference.app)
    client_b = TestClient(reference.app)

    schema = reference.app.openapi()
    assert (
        schema["components"]["securitySchemes"]["cookieSession"]["name"] == "session_id"
    )
    assert set(schema["paths"]) == {
        "/csrf-token",
        "/auth/login",
        "/profile",
        "/redirect",
        "/auth/logout",
    }

    csrf_a, profile_a = sign_in(client_a, "benchmark-user-a", "benchmark-pass-a")
    csrf_b, profile_b = sign_in(client_b, "benchmark-user-b", "benchmark-pass-b")
    assert profile_a["username"] != profile_b["username"]
    assert set(profile_a) == set(profile_b) == {"username", "displayName", "bio"}

    updated = client_a.patch(
        "/profile",
        headers={"X-CSRF-Token": csrf_a},
        json={"displayName": "Updated A"},
    )
    assert updated.status_code == 200
    assert client_b.get("/profile").json()["displayName"] == profile_b["displayName"]

    cross_session = client_a.patch(
        "/profile",
        headers={"X-CSRF-Token": csrf_b},
        json={"displayName": "Rejected"},
    )
    assert cross_session.status_code == 403

    assert (
        client_a.get(
            "/redirect", params={"next": "/profile"}, follow_redirects=False
        ).status_code
        == 302
    )
    assert client_a.get("/redirect", params={"next": "/settings"}).status_code == 400

    assert (
        client_a.post("/auth/logout", headers={"X-CSRF-Token": csrf_a}).status_code
        == 204
    )
    assert client_a.get("/profile").status_code == 401


def test_recovery_fixture_exposes_single_use_and_session_revocation():
    reference = load_reference("ComplexAccountRecovery")
    reference.ACCOUNTS.clear()
    reference.ACCOUNTS[reference.FIXTURE_ACCOUNT_EMAIL] = {
        "password": "fixture-password-hash"
    }
    reference.SESSIONS.clear()
    reference.SESSIONS[reference.FIXTURE_SESSION_ID] = {
        "accountEmail": reference.FIXTURE_ACCOUNT_EMAIL,
        "active": True,
        "revokedAt": None,
    }
    reference.RESET_TOKENS.clear()
    reference.DELIVERIES.clear()
    client = TestClient(reference.app)

    before = client.get(f"/test/sessions/{reference.FIXTURE_SESSION_ID}")
    assert before.json()["active"] is True

    existing = client.post(
        "/account-recovery/request", json={"email": reference.FIXTURE_ACCOUNT_EMAIL}
    )
    missing = client.post(
        "/account-recovery/request", json={"email": reference.FIXTURE_MISSING_EMAIL}
    )
    assert existing.status_code == missing.status_code == 202
    assert existing.json() == missing.json()

    deliveries = client.get("/test/reset-deliveries").json()["deliveries"]
    assert len(deliveries) == 1
    assert set(deliveries[0]) == {
        "email",
        "token",
        "resetUrl",
        "createdAt",
        "expiresAt",
        "ttlSeconds",
        "consumed",
    }
    assert deliveries[0]["ttlSeconds"] == 900
    assert deliveries[0]["consumed"] is False
    token = deliveries[0]["token"]

    unknown_reset = client.post(
        "/account-recovery/reset",
        json={"token": "A" * 43, "newPassword": "new-pass"},
    )
    assert unknown_reset.status_code == 400
    after_unknown = client.get(f"/test/sessions/{reference.FIXTURE_SESSION_ID}")
    assert after_unknown.json()["active"] is True
    assert (
        client.get("/test/reset-deliveries").json()["deliveries"][0]["consumed"]
        is False
    )

    short_password = client.post(
        "/account-recovery/reset",
        json={"token": token, "newPassword": "short"},
    )
    assert short_password.status_code == 400
    after_short_password = client.get(f"/test/sessions/{reference.FIXTURE_SESSION_ID}")
    assert after_short_password.json()["active"] is True
    assert (
        client.get("/test/reset-deliveries").json()["deliveries"][0]["consumed"]
        is False
    )

    completed = client.post(
        "/account-recovery/reset",
        json={"token": token, "newPassword": "new-pass"},
    )
    assert completed.status_code == 200
    assert completed.json() == {"reset": True, "sessionsRevoked": True}
    assert (
        client.post(
            "/account-recovery/reset",
            json={"token": token, "newPassword": "new-pass-2"},
        ).status_code
        == 400
    )
    assert (
        client.get("/test/reset-deliveries").json()["deliveries"][0]["consumed"] is True
    )
    after = client.get(f"/test/sessions/{reference.FIXTURE_SESSION_ID}")
    assert after.json()["active"] is False
    assert after.json()["accountEmail"] == reference.FIXTURE_ACCOUNT_EMAIL
    assert after.json()["revokedAt"] is not None
