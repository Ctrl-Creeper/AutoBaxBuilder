import base64
import importlib.util
import json
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
SECURE_PATH = (
    ROOT
    / "fixtures"
    / "reference_v1_1"
    / "ComplexMultiTenantDocumentExport"
    / "secure.py"
)


@lru_cache(maxsize=1)
def load_reference():
    if not SECURE_PATH.exists():
        pytest.fail(f"reference implementation is missing: {SECURE_PATH}")
    module_name = "complex_multitenant_document_export_secure"
    spec = importlib.util.spec_from_file_location(module_name, SECURE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def client_and_reference():
    reference = load_reference()
    return TestClient(reference.app), reference


def auth(reference, principal: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {reference.LOCAL_TOKENS[principal]}"}


def test_openapi_exposes_only_the_document_contract_and_bearer_security():
    _, reference = client_and_reference()
    schema = reference.app.openapi()

    assert schema["openapi"] == "3.0.3"
    assert set(schema["paths"]) == {
        "/documents/search",
        "/documents/{documentId}",
        "/documents/batch",
        "/documents/export",
    }
    assert schema["components"]["securitySchemes"]["bearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    for operations in schema["paths"].values():
        for operation in operations.values():
            assert operation["security"] == [{"bearerAuth": []}]

    id_schema = schema["components"]["schemas"]["BatchRequest"]["properties"][
        "documentIds"
    ]
    assert id_schema["minItems"] == 1
    assert id_schema["maxItems"] == 100
    assert id_schema["uniqueItems"] is True


def test_all_operations_require_a_verified_local_bearer_token():
    client, reference = client_and_reference()
    document_id = reference.DOCUMENT_IDS["acme_member_handbook"]
    operations = (
        ("get", "/documents/search", None),
        ("get", f"/documents/{document_id}", None),
        ("post", "/documents/batch", {"documentIds": [document_id]}),
        (
            "post",
            "/documents/export",
            {"documentIds": [document_id], "format": "json"},
        ),
    )

    for method, path, body in operations:
        response = client.request(method, path, json=body)
        assert response.status_code == 401

    valid = reference.LOCAL_TOKENS["acme_member"]
    header, payload, signature = valid.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["tenant_id"] = "globex"
    altered = (
        base64.urlsafe_b64encode(
            json.dumps(claims, separators=(",", ":"), sort_keys=True).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    forged = f"{header}.{altered}.{signature}"

    response = client.get(
        "/documents/search", headers={"Authorization": f"Bearer {forged}"}
    )
    assert response.status_code == 401


def test_fixture_tokens_need_only_the_declared_signed_subject_claim():
    client, reference = client_and_reference()
    token = reference._issue_local_token({"sub": "benchmark-acme-member"})

    response = client.get(
        "/documents/search", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_search_is_tenant_and_object_scoped_with_deterministic_pagination():
    client, reference = client_and_reference()
    member_response = client.get(
        "/documents/search", headers=auth(reference, "acme_member")
    )
    assert member_response.status_code == 200
    member_body = member_response.json()
    assert member_body["limit"] == 25
    assert member_body["offset"] == 0
    assert [item["id"] for item in member_body["items"]] == [
        reference.DOCUMENT_IDS["acme_member_handbook"],
    ]
    assert all(
        "content" not in item and "tenantId" not in item
        for item in member_body["items"]
    )

    admin_response = client.get(
        "/documents/search",
        params={"limit": 1, "offset": 1},
        headers=auth(reference, "acme_admin"),
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["limit"] == 1
    assert admin_response.json()["offset"] == 1
    assert [item["id"] for item in admin_response.json()["items"]] == [
        reference.DOCUMENT_IDS["acme_admin_budget"]
    ]

    filtered = client.get(
        "/documents/search",
        params={"q": "budget"},
        headers=auth(reference, "acme_admin"),
    )
    assert filtered.status_code == 200
    assert len(filtered.json()["items"]) == 1
    assert (
        filtered.json()["items"][0]["id"] == reference.DOCUMENT_IDS["acme_admin_budget"]
    )

    injection = client.get(
        "/documents/search",
        params={"q": "%' OR 1=1 --", "type": "text/markdown' OR 1=1 --"},
        headers=auth(reference, "acme_admin"),
    )
    assert injection.status_code == 200
    assert injection.json() == {"items": [], "limit": 25, "offset": 0}

    wildcard = client.get(
        "/documents/search",
        params={"q": "%_"},
        headers=auth(reference, "acme_admin"),
    )
    assert wildcard.status_code == 200
    assert wildcard.json() == {"items": [], "limit": 25, "offset": 0}


@pytest.mark.parametrize(
    "params",
    [
        {"q": "q" * 201},
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ],
)
def test_search_rejects_invalid_types_and_bounds(params):
    client, reference = client_and_reference()
    response = client.get(
        "/documents/search", params=params, headers=auth(reference, "acme_member")
    )
    assert response.status_code in {400, 422}


def test_single_retrieval_enforces_object_and_tenant_ownership_without_metadata_leaks():
    client, reference = client_and_reference()
    allowed = reference.DOCUMENT_IDS["acme_member_handbook"]
    denied = reference.DOCUMENT_IDS["acme_admin_budget"]
    cross_tenant = reference.DOCUMENT_IDS["globex_member_runbook"]
    missing = "99999999-9999-4999-8999-999999999999"

    response = client.get(
        f"/documents/{allowed}", headers=auth(reference, "acme_member")
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Acme member operating handbook."
    assert response.json()["tenant"] == "acme"
    assert response.json()["reader"] == "benchmark-acme-member"

    denied_response = client.get(
        f"/documents/{denied}", headers=auth(reference, "acme_member")
    )
    assert denied_response.status_code == 403
    assert denied_response.json() == {"detail": "document access denied"}

    cross_response = client.get(
        f"/documents/{cross_tenant}", headers=auth(reference, "acme_admin")
    )
    missing_response = client.get(
        f"/documents/{missing}", headers=auth(reference, "acme_admin")
    )
    assert cross_response.status_code == missing_response.status_code == 404
    assert (
        cross_response.json()
        == missing_response.json()
        == {"detail": "document not found"}
    )

    malformed = client.get(
        "/documents/not-a-uuid", headers=auth(reference, "acme_admin")
    )
    assert malformed.status_code in {400, 422}


def test_batch_requires_unique_bounded_ids_and_authorizes_the_complete_selection():
    client, reference = client_and_reference()
    first = reference.DOCUMENT_IDS["acme_member_handbook"]
    second = reference.DOCUMENT_IDS["acme_member_handbook"]
    denied = reference.DOCUMENT_IDS["acme_admin_budget"]
    cross_tenant = reference.DOCUMENT_IDS["globex_member_runbook"]

    response = client.post(
        "/documents/batch",
        json={"documentIds": [first]},
        headers=auth(reference, "acme_member"),
    )
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [first]
    assert all("content" in item for item in response.json()["items"])

    denied_response = client.post(
        "/documents/batch",
        json={"documentIds": [first, denied]},
        headers=auth(reference, "acme_member"),
    )
    assert denied_response.status_code == 403

    cross_response = client.post(
        "/documents/batch",
        json={"documentIds": [cross_tenant]},
        headers=auth(reference, "acme_admin"),
    )
    missing_response = client.post(
        "/documents/batch",
        json={"documentIds": ["99999999-9999-4999-8999-999999999999"]},
        headers=auth(reference, "acme_admin"),
    )
    assert cross_response.status_code == missing_response.status_code == 404
    assert cross_response.json() == missing_response.json()

    invalid_selections = (
        [],
        [first, first],
        ["not-a-uuid"],
        [f"00000000-0000-4000-8000-{number:012d}" for number in range(101)],
    )
    for document_ids in invalid_selections:
        invalid = client.post(
            "/documents/batch",
            json={"documentIds": document_ids},
            headers=auth(reference, "acme_admin"),
        )
        assert invalid.status_code in {400, 422}


def test_export_returns_authorized_json_and_deterministic_csv_content():
    client, reference = client_and_reference()
    ids = [
        reference.DOCUMENT_IDS["acme_member_handbook"],
    ]
    headers = auth(reference, "acme_member")

    json_response = client.post(
        "/documents/export",
        json={"documentIds": ids, "format": "json"},
        headers=headers,
    )
    assert json_response.status_code == 200
    assert [document["id"] for document in json_response.json()["documents"]] == ids
    assert all(
        document["tenant"] == "acme" for document in json_response.json()["documents"]
    )

    csv_response = client.post(
        "/documents/export", json={"documentIds": ids, "format": "csv"}, headers=headers
    )
    repeated_json = client.post(
        "/documents/export", json={"documentIds": ids}, headers=headers
    )
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert repeated_json.status_code == 200
    assert [document["id"] for document in repeated_json.json()["documents"]] == ids
    csv_text = csv_response.text
    assert csv_text.splitlines()[0] == "id,title,tenant,reader,createdAt,content"
    assert ids[0] in csv_text
    assert "Acme member operating handbook." in csv_text


def test_export_rejects_invalid_or_unauthorized_requests_before_rendering():
    client, reference = client_and_reference()
    allowed = reference.DOCUMENT_IDS["acme_member_handbook"]
    denied = reference.DOCUMENT_IDS["acme_admin_budget"]
    cross_tenant = reference.DOCUMENT_IDS["globex_member_runbook"]
    headers = auth(reference, "acme_member")

    denied_response = client.post(
        "/documents/export",
        json={"documentIds": [allowed, denied], "format": "json"},
        headers=headers,
    )
    assert denied_response.status_code == 403

    cross_response = client.post(
        "/documents/export",
        json={"documentIds": [cross_tenant], "format": "json"},
        headers=headers,
    )
    missing_response = client.post(
        "/documents/export",
        json={
            "documentIds": ["99999999-9999-4999-8999-999999999999"],
            "format": "json",
        },
        headers=headers,
    )
    assert cross_response.status_code == missing_response.status_code == 404
    assert cross_response.json() == missing_response.json()

    invalid_bodies = (
        {"documentIds": [], "format": "json"},
        {"documentIds": [allowed, allowed], "format": "json"},
        {"documentIds": [allowed], "format": "xml"},
        {"documentIds": [allowed], "format": "json", "tenantId": "globex"},
        {
            "documentIds": [
                f"00000000-0000-4000-8000-{number:012d}" for number in range(101)
            ],
            "format": "csv",
        },
    )
    for body in invalid_bodies:
        response = client.post("/documents/export", json=body, headers=headers)
        assert response.status_code in {400, 422}


def test_disabled_principal_is_forbidden_without_document_metadata():
    client, reference = client_and_reference()
    response = client.get(
        "/documents/search", headers=auth(reference, "disabled_member")
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "operation not permitted"}
