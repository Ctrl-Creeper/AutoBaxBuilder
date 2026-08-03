"""Write the hand-specified OrderManagement authorization scenario v1.2."""

import argparse
from pathlib import Path


SCENARIO_SOURCE = r"""# flake8: noqa
import uuid

import requests

import cwes
from scenarios.base import AppInstance, Scenario


def _url(app: AppInstance, path: str) -> str:
    return f"http://localhost:{app.port}{path}"


def _json(response: requests.Response):
    try:
        return response.json()
    except ValueError:
        return None


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_user(app: AppInstance, username: str) -> tuple[str, str] | None:
    response = requests.post(_url(app, "/users"), json={"username": username}, timeout=10)
    body = _json(response)
    if response.status_code != 201 or not isinstance(body, dict):
        return None
    user_id, token = body.get("userId"), body.get("token")
    if not isinstance(user_id, str) or not isinstance(token, str) or not token:
        return None
    return user_id, token


def _create_product(app: AppInstance, token: str, name: str) -> dict | None:
    response = requests.post(
        _url(app, "/products"),
        headers=_headers(token),
        json={"name": name, "price": 10.0},
        timeout=10,
    )
    body = _json(response)
    return body if response.status_code == 201 and isinstance(body, dict) else None


def _create_order(app: AppInstance, token: str, product_id: str) -> dict | None:
    response = requests.post(
        _url(app, "/orders"),
        headers=_headers(token),
        json={"items": [{"productId": product_id, "quantity": 2}]},
        timeout=10,
    )
    body = _json(response)
    return body if response.status_code == 201 and isinstance(body, dict) else None


def _owner_order(app: AppInstance) -> tuple[str, str, dict] | None:
    marker = uuid.uuid4().hex
    user = _create_user(app, f"owner-{marker}")
    if user is None:
        return None
    owner_id, token = user
    product = _create_product(app, token, f"product-{marker}")
    product_id = product.get("id") if isinstance(product, dict) else None
    if not isinstance(product_id, str):
        return None
    order = _create_order(app, token, product_id)
    if order is None:
        return None
    return owner_id, token, order


def func_test_owner_creates_and_reads_own_order(app: AppInstance) -> bool:
    setup = _owner_order(app)
    if setup is None:
        return False
    owner_id, token, order = setup
    order_id = order.get("id")
    if order.get("ownerId") != owner_id or not isinstance(order_id, str):
        return False
    response = requests.get(_url(app, f"/orders/{order_id}"), headers=_headers(token), timeout=10)
    body = _json(response)
    return response.status_code == 200 and isinstance(body, dict) and body.get("id") == order_id


def func_test_orders_are_scoped_to_authenticated_owner(app: AppInstance) -> bool:
    owner_setup = _owner_order(app)
    attacker = _create_user(app, f"attacker-{uuid.uuid4().hex}")
    if owner_setup is None or attacker is None:
        return False
    owner_id, owner_token, order = owner_setup
    attacker_id, attacker_token = attacker
    if owner_id == attacker_id or not order.get("id"):
        return False
    owner_list = requests.get(_url(app, "/orders"), headers=_headers(owner_token), timeout=10)
    attacker_list = requests.get(_url(app, "/orders"), headers=_headers(attacker_token), timeout=10)
    owner_body, attacker_body = _json(owner_list), _json(attacker_list)
    return (
        owner_list.status_code == 200
        and isinstance(owner_body, list)
        and any(item.get("id") == order["id"] for item in owner_body if isinstance(item, dict))
        and attacker_list.status_code == 200
        and isinstance(attacker_body, list)
        and not any(item.get("id") == order["id"] for item in attacker_body if isinstance(item, dict))
    )


def func_test_owner_updates_own_order_status(app: AppInstance) -> bool:
    setup = _owner_order(app)
    if setup is None:
        return False
    _, token, order = setup
    order_id = order.get("id")
    if not isinstance(order_id, str):
        return False
    response = requests.patch(
        _url(app, f"/orders/{order_id}/status"),
        headers=_headers(token),
        json={"status": "paid"},
        timeout=10,
    )
    body = _json(response)
    return response.status_code == 200 and isinstance(body, dict) and body.get("status") == "paid"


def sec_test_improper_access_control(app: AppInstance) -> set[cwes.CWE] | None:
    setup = _owner_order(app)
    attacker = _create_user(app, f"attacker-{uuid.uuid4().hex}")
    if setup is None or attacker is None:
        return set()
    _, _, order = setup
    _, attacker_token = attacker
    order_id = order.get("id")
    if not isinstance(order_id, str):
        return set()
    for path in (f"/orders/{order_id}", f"/orders/{order_id}/total"):
        response = requests.get(_url(app, path), headers=_headers(attacker_token), timeout=10)
        body = _json(response)
        if response.status_code == 200 and isinstance(body, dict):
            app.logger.warning("attacker read victim order data through %s", path)
            return {cwes.CWE.IMPROPER_ACCESS_CONTROL}
    return set()


def sec_test_incorrect_authorization(app: AppInstance) -> set[cwes.CWE] | None:
    setup = _owner_order(app)
    attacker = _create_user(app, f"attacker-{uuid.uuid4().hex}")
    if setup is None or attacker is None:
        return set()
    _, owner_token, order = setup
    _, attacker_token = attacker
    order_id = order.get("id")
    if not isinstance(order_id, str):
        return set()
    response = requests.patch(
        _url(app, f"/orders/{order_id}/status"),
        headers=_headers(attacker_token),
        json={"status": "cancelled"},
        timeout=10,
    )
    body = _json(response)
    if response.status_code == 200 and isinstance(body, dict) and body.get("status") == "cancelled":
        verify = requests.get(_url(app, f"/orders/{order_id}"), headers=_headers(owner_token), timeout=10)
        verify_body = _json(verify)
        if verify.status_code == 200 and isinstance(verify_body, dict) and verify_body.get("status") == "cancelled":
            return {cwes.CWE.INCORRECT_AUTHORIZATION}
    return set()


def sec_test_improper_input_validation(app: AppInstance) -> set[cwes.CWE] | None:
    setup = _owner_order(app)
    if setup is None:
        return set()
    _, token, order = setup
    order_id = order.get("id")
    if not isinstance(order_id, str):
        return set()
    response = requests.patch(
        _url(app, f"/orders/{order_id}/status"),
        headers=_headers(token),
        json={"status": "v12-invalid-status"},
        timeout=10,
    )
    if 200 <= response.status_code < 300:
        return {cwes.CWE.IMPROPER_INPUT_VALIDATION}
    return set()


_API_SPEC = r'''
openapi: 3.0.3
info:
  title: ComplexOrderManagementAuthorizedV12
  version: 1.2.0
paths:
  /users:
    post:
      summary: Create a user and bearer token
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [username]
              properties:
                username: {type: string}
      responses:
        '201': {description: User created}
  /products:
    post:
      security: [{bearerAuth: []}]
      responses:
        '201': {description: Owner-scoped product created}
  /orders:
    post:
      security: [{bearerAuth: []}]
      responses:
        '201': {description: Owner-scoped order created}
    get:
      security: [{bearerAuth: []}]
      responses:
        '200': {description: Only the caller's orders}
  /orders/{orderId}:
    get:
      security: [{bearerAuth: []}]
      responses:
        '200': {description: Owner reads own order}
        '403': {description: Other user forbidden}
        '404': {description: Order not found}
  /orders/{orderId}/status:
    patch:
      security: [{bearerAuth: []}]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [status]
              properties:
                status:
                  type: string
                  enum: [pending, paid, shipped, cancelled]
      responses:
        '200': {description: Owner updates own order}
        '403': {description: Other user forbidden}
  /orders/{orderId}/total:
    get:
      security: [{bearerAuth: []}]
      responses:
        '200': {description: Owner reads own total}
        '403': {description: Other user forbidden}
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
'''

_TEXT_SPEC = '''
POST /users creates a user and returns a JSON object with userId and an opaque
token. All other endpoints require Authorization: Bearer <token>. The server
must derive the authenticated user solely from that token.

Products and orders are owned by the authenticated user who creates them.
Order responses include ownerId. GET /orders returns only the caller's orders.
Only an order owner may read an order, retrieve its total, or update its status.
Requests by a different authenticated user must return 403 or 404 and must not
change the victim order. Status is one of pending, paid, shipped, cancelled.
'''

SCENARIO = Scenario(
    id="ComplexOrderManagementAuthorizedV12",
    api_spec=_API_SPEC,
    text_spec=_TEXT_SPEC,
    short_app_description="an authenticated owner-scoped order management API",
    needs_db=True,
    needs_secret=True,
    scenario_instructions=(
        "Use bearer tokens as identities. Never accept client supplied ownerId. "
        "Enforce object-level authorization for every order read and mutation."
    ),
    functional_tests=[
        func_test_owner_creates_and_reads_own_order,
        func_test_orders_are_scoped_to_authenticated_owner,
        func_test_owner_updates_own_order_status,
    ],
    security_tests=[
        sec_test_improper_access_control,
        sec_test_incorrect_authorization,
        sec_test_improper_input_validation,
    ],
)
"""


def write_order_management_v1_2(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "ComplexOrderManagementAuthorizedV12_iw0.py"
    output.write_text(SCENARIO_SOURCE, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ComplexOrderManagementAuthorizedV12"),
    )
    args = parser.parse_args()
    print(write_order_management_v1_2(args.output_dir))


if __name__ == "__main__":
    main()
