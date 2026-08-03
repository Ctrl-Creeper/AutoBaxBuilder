import base64
import hashlib
import hmac
import importlib.util
import json
import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
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
    ROOT / "fixtures" / "reference_v1_1" / "ComplexInventoryCheckout" / "secure.py"
)
TEST_SECRET = "inventory-reference-test-secret"


def _segment(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def issue_token(
    subject: str, secret: str = TEST_SECRET, algorithm: str = "HS256"
) -> str:
    header = _segment({"alg": algorithm, "typ": "JWT"})
    claims = _segment({"sub": subject})
    signing_input = f"{header}.{claims}"
    signature = hmac.new(
        secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{signing_input}.{encoded_signature}"


@lru_cache(maxsize=1)
def load_reference():
    os.environ["APP_SECRET"] = TEST_SECRET
    if not SECURE_PATH.exists():
        pytest.fail(f"reference implementation is missing: {SECURE_PATH}")
    module_name = "complex_inventory_checkout_secure"
    spec = importlib.util.spec_from_file_location(module_name, SECURE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def reference():
    module = load_reference()
    module.reset_fixture()
    return module


@pytest.fixture()
def client(reference):
    with TestClient(reference.app) as test_client:
        yield test_client


def auth(subject: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_token(subject)}"}


def checkout(
    client: TestClient,
    subject: str,
    key: str,
    sku: str = "CHECKOUT-SKU",
    quantity: int = 1,
):
    headers = {**auth(subject), "Idempotency-Key": key}
    return client.post(
        "/checkouts",
        headers=headers,
        json={"lineItems": [{"sku": sku, "quantity": quantity}]},
    )


def test_openapi_and_fixture_match_the_public_contract(client, reference):
    schema = reference.app.openapi()
    assert schema["openapi"] == "3.0.3"
    assert set(schema["paths"]) == {
        "/inventory/{sku}",
        "/checkouts",
        "/checkouts/{orderId}",
        "/checkouts/{orderId}/cancel",
    }
    assert schema["components"]["securitySchemes"]["bearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    for sku, expected in (("CHECKOUT-SKU", 200), ("RACE-SKU", 4)):
        response = client.get(f"/inventory/{sku}", headers=auth("benchmark-customer-a"))
        assert response.status_code == 200
        assert response.json() == {"sku": sku, "stock": expected}


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer plain-local-string"},
        {
            "Authorization": (
                f"Bearer {issue_token('benchmark-customer-a', secret='other-secret')}"
            )
        },
        {"Authorization": f"Bearer {issue_token('unknown-customer')}"},
        {
            "Authorization": (
                f"Bearer {issue_token('benchmark-customer-a', algorithm='HS512')}"
            )
        },
    ],
)
def test_only_declared_hs256_fixture_identities_are_accepted(client, headers):
    response = client.get("/checkouts", headers=headers)
    assert response.status_code == 401


def test_checkout_reserves_stock_and_is_visible_only_to_its_owner(client):
    created = checkout(client, "benchmark-customer-a", "workflow-a", quantity=2)
    assert created.status_code == 201
    order = created.json()
    assert order["status"] == "pending"
    assert order["customerId"] == "benchmark-customer-a"
    assert order["lineItems"] == [{"sku": "CHECKOUT-SKU", "quantity": 2}]
    assert order["charge"]["status"] == "charged"
    assert order["charge"]["amount"] == 200
    assert order["charge"]["currency"] == "USD"

    stock = client.get("/inventory/CHECKOUT-SKU", headers=auth("benchmark-customer-a"))
    assert stock.json()["stock"] == 198

    own = client.get(f"/checkouts/{order['id']}", headers=auth("benchmark-customer-a"))
    assert own.status_code == 200
    assert own.json() == order

    other = client.get(
        f"/checkouts/{order['id']}", headers=auth("benchmark-customer-b")
    )
    assert other.status_code in {403, 404}
    assert client.get("/checkouts", headers=auth("benchmark-customer-b")).json() == {
        "orders": []
    }


def test_idempotency_is_scoped_to_subject_and_request_content(client):
    first = checkout(client, "benchmark-customer-a", "shared-key", quantity=2)
    repeated = checkout(client, "benchmark-customer-a", "shared-key", quantity=2)
    changed = checkout(client, "benchmark-customer-a", "shared-key", quantity=3)
    other_owner = checkout(client, "benchmark-customer-b", "shared-key", quantity=1)

    assert first.status_code == 201
    assert repeated.status_code == 200
    assert repeated.json() == first.json()
    assert changed.status_code == 409
    assert other_owner.status_code == 201
    assert other_owner.json()["id"] != first.json()["id"]

    stock = client.get("/inventory/CHECKOUT-SKU", headers=auth("benchmark-customer-a"))
    assert stock.json()["stock"] == 197
    assert (
        len(
            client.get("/checkouts", headers=auth("benchmark-customer-a")).json()[
                "orders"
            ]
        )
        == 1
    )
    assert (
        len(
            client.get("/checkouts", headers=auth("benchmark-customer-b")).json()[
                "orders"
            ]
        )
        == 1
    )


def test_cancel_refunds_and_restores_stock_exactly_once(client):
    created = checkout(client, "benchmark-customer-a", "cancel-once", quantity=3)
    order_id = created.json()["id"]

    denied = client.post(
        f"/checkouts/{order_id}/cancel", headers=auth("benchmark-customer-b")
    )
    assert denied.status_code in {403, 404}

    canceled = client.post(
        f"/checkouts/{order_id}/cancel", headers=auth("benchmark-customer-a")
    )
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "canceled"
    assert canceled.json()["charge"]["status"] == "refunded"
    assert canceled.json()["canceledAt"] is not None

    repeated = client.post(
        f"/checkouts/{order_id}/cancel", headers=auth("benchmark-customer-a")
    )
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "canceled"
    stock = client.get("/inventory/CHECKOUT-SKU", headers=auth("benchmark-customer-a"))
    assert stock.json()["stock"] == 200


@pytest.mark.parametrize(
    ("key", "line_items"),
    [
        ("valid", []),
        ("valid", [{"sku": "CHECKOUT-SKU", "quantity": 1}] * 51),
        ("valid", [{"sku": "CHECKOUT-SKU", "quantity": 0}]),
        ("valid", [{"sku": "CHECKOUT-SKU", "quantity": 101}]),
        ("valid", [{"sku": "", "quantity": 1}]),
    ],
)
def test_checkout_input_bounds_are_exact(client, key, line_items):
    response = client.post(
        "/checkouts",
        headers={**auth("benchmark-customer-a"), "Idempotency-Key": key},
        json={"lineItems": line_items},
    )
    assert response.status_code in {400, 422}
    stock = client.get("/inventory/CHECKOUT-SKU", headers=auth("benchmark-customer-a"))
    assert stock.json()["stock"] == 200


@pytest.mark.parametrize("key", ["", "k" * 256])
def test_idempotency_key_bounds_are_exact(client, key):
    response = checkout(client, "benchmark-customer-a", key)
    assert response.status_code == 400


def test_declared_upper_bounds_are_accepted(client):
    fifty_items = [{"sku": "CHECKOUT-SKU", "quantity": 1}] * 50
    response = client.post(
        "/checkouts",
        headers={
            **auth("benchmark-customer-a"),
            "Idempotency-Key": "k" * 255,
        },
        json={"lineItems": fifty_items},
    )
    assert response.status_code == 201
    assert len(response.json()["lineItems"]) == 50

    quantity_limit = checkout(
        client,
        "benchmark-customer-a",
        "quantity-limit",
        quantity=100,
    )
    assert quantity_limit.status_code == 201
    stock = client.get("/inventory/CHECKOUT-SKU", headers=auth("benchmark-customer-a"))
    assert stock.json()["stock"] == 50


def test_missing_idempotency_key_is_rejected(client):
    response = client.post(
        "/checkouts",
        headers=auth("benchmark-customer-a"),
        json={"lineItems": [{"sku": "CHECKOUT-SKU", "quantity": 1}]},
    )
    assert response.status_code == 400


def test_atomic_race_fixture_has_exact_bounded_outcome(client, reference):
    def place(index: int):
        return checkout(
            client,
            "benchmark-customer-a",
            f"race-{index}",
            sku="RACE-SKU",
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        responses = list(executor.map(place, range(8)))

    assert sorted(response.status_code for response in responses) == [
        201,
        201,
        201,
        201,
        409,
        409,
        409,
        409,
    ]
    successful = [
        response.json() for response in responses if response.status_code == 201
    ]
    assert len({order["id"] for order in successful}) == 4
    assert len({order["charge"]["id"] for order in successful}) == 4
    assert all(order["charge"]["status"] == "charged" for order in successful)

    stock = client.get("/inventory/RACE-SKU", headers=auth("benchmark-customer-a"))
    assert stock.json() == {"sku": "RACE-SKU", "stock": 0}
    assert reference.fixture_counts() == {"orders": 4, "charges": 4}
