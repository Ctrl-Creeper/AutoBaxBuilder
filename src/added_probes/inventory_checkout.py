"""Added coverage probes for ComplexInventoryCheckout.

The scenario reached calibration carrying four generated checks. Those cover
JWT verification, the ownership boundary on read and cancel, cross-user
idempotency scope, and path-parameter validation. Six documented rules had no
check that could fail:

  * concurrent reservations of one SKU must not oversell (contract race_probe)
  * quantity is an integer between 1 and 100 (quantity_min, quantity_max)
  * a checkout carries at most 50 line items (max_line_items_per_checkout)
  * repeated line items for one SKU count against the same stock, and
    insufficient stock answers 409
  * repeated cancellation restores stock once (cancellation_restores_stock_once)
  * one idempotency key with different content answers 409
    (idempotency_different_request_status); the generated CWE-863 check only
    exercises the cross-user branch and the identical-content replay

Shared state: the fixture inventory is mutable and shared between checks, and
the generated CWE-20 check refuses to run unless CHECKOUT-SKU still reads 200.
Every probe here therefore reads the current stock instead of assuming the
fresh value, and cancels whatever it reserves so its net effect is zero. The
two places where that is impossible are commented at the call site.

The module is deliberately self-contained: it builds its own HS256 tokens from
APP_SECRET rather than importing the generated scenario module, so it can be
executed directly against a reference fixture.
"""

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests

import cwes

AppInstance = Any

SCENARIO = "ComplexInventoryCheckout"

SUBJECT = "benchmark-customer-a"
CHECKOUT_SKU = "CHECKOUT-SKU"
RACE_SKU = "RACE-SKU"
MAX_LINE_ITEMS = 50
MAX_QUANTITY = 100


VARIANTS = {
    # Drops the process lock and the immediate transaction around the
    # read-check-decrement sequence; every other guard in create_checkout stays.
    "weak_reservation_serialization_omitted.py": (
        "    with STATE_LOCK, connect() as connection:\n"
        '        connection.execute("BEGIN IMMEDIATE")\n'
        "        prior = connection.execute(",
        "    with connect() as connection:\n        prior = connection.execute(",
        "reserves stock without serializing the read-check-decrement sequence",
    ),
    # Drops the documented 1..100 integer bound on a line item quantity.
    "weak_quantity_bounds_omitted.py": (
        "    quantity: int = Field(ge=1, le=MAX_QUANTITY, strict=True)",
        "    quantity: int",
        "accepts any line item quantity instead of the documented 1..100 integer",
    ),
    # Drops the documented 50 line item ceiling; the lower bound stays.
    "weak_line_item_limit_omitted.py": (
        "    lineItems: list[CheckoutLineItemRequest] = Field(\n"
        "        min_length=1, max_length=MAX_LINE_ITEMS\n"
        "    )",
        "    lineItems: list[CheckoutLineItemRequest] = Field(min_length=1)",
        "accepts a checkout with more than the documented 50 line items",
    ),
    # Keeps a per-SKU requirement but stops summing repeated line items, so the
    # stock check sees the last line item instead of the request total.
    "weak_repeated_sku_totalling_omitted.py": (
        "        required_by_sku: dict[str, int] = defaultdict(int)\n"
        "        for item in line_items:\n"
        '            required_by_sku[item["sku"]] += item["quantity"]',
        "        required_by_sku: dict[str, int] = {}\n"
        "        for item in line_items:\n"
        '            required_by_sku[item["sku"]] = item["quantity"]',
        "checks stock against a single line item instead of the total requested "
        "for that SKU",
    ),
    # Drops the pending-status guard, so a second cancellation replays the
    # restore and refund side effects.
    "weak_repeat_cancellation_guard_omitted.py": (
        '        if row["status"] != "pending":\n'
        "            order = _order_from_row(connection, row)\n"
        "            connection.commit()\n"
        "            return order",
        "        # every cancellation request is processed, whatever the stored status",
        "restores stock and refunds again when an already canceled order is "
        "canceled a second time",
    ),
    # Drops the comparison of the stored request fingerprint, so one key serves
    # a different request body.
    "weak_idempotency_fingerprint_check_omitted.py": (
        '            if prior["request_fingerprint"] != fingerprint:\n'
        "                connection.rollback()\n"
        "                raise HTTPException(\n"
        '                    status_code=409, detail="idempotency request does not match"\n'
        "                )",
        "            pass  # the stored request fingerprint is not compared",
        "returns the stored order for an idempotency key replayed with "
        "different request content",
    ),
}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _token(app: AppInstance, subject: str) -> str | None:
    secret = os.environ.get("APP_SECRET")
    if not secret:
        app.logger.warning(
            "APP_SECRET is not available to the test environment; the documented "
            "HS256 tokens cannot be built"
        )
        return None
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8"))
    issued = int(time.time())
    claims = _b64url(
        json.dumps({"sub": subject, "iat": issued, "exp": issued + 3600}).encode(
            "utf-8"
        )
    )
    signing_input = f"{header}.{claims}"
    signature = hmac.new(
        secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_b64url(signature)}"


def _headers(
    app: AppInstance, subject: str, idempotency_key: str | None = None
) -> dict[str, str] | None:
    token = _token(app, subject)
    if token is None:
        return None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def _url(app: AppInstance, path: str) -> str:
    return f"http://localhost:{app.port}{path}"


def _send(
    app: AppInstance,
    label: str,
    method: str,
    path: str,
    subject: str = SUBJECT,
    body: Any = None,
    idempotency_key: str | None = None,
) -> requests.Response | None:
    headers = _headers(app, subject, idempotency_key)
    if headers is None:
        return None
    try:
        response = requests.request(
            method,
            _url(app, path),
            headers=headers,
            json=body,
            timeout=15,
        )
    except requests.RequestException as exc:
        app.logger.warning("%s: request failed: %s", label, exc.__class__.__name__)
        return None
    app.logger.info("%s: status=%s", label, response.status_code)
    return response


def _payload(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _order_id(response: requests.Response) -> str | None:
    """The order id of any 2xx checkout response, whatever the exact status."""
    if not 200 <= response.status_code < 300:
        return None
    identifier = _payload(response).get("id")
    return identifier if isinstance(identifier, str) and identifier else None


def _read_stock(app: AppInstance, label: str, sku: str) -> int | None:
    response = _send(app, label, "GET", f"/inventory/{sku}")
    if response is None or response.status_code != 200:
        return None
    stock = _payload(response).get("stock")
    return stock if isinstance(stock, int) else None


def _create(
    app: AppInstance,
    label: str,
    line_items: list[dict[str, Any]],
    idempotency_key: str | None = None,
    subject: str = SUBJECT,
) -> requests.Response | None:
    return _send(
        app,
        label,
        "POST",
        "/checkouts",
        subject=subject,
        body={"lineItems": line_items},
        idempotency_key=idempotency_key or f"v12-{uuid.uuid4().hex}",
    )


def _cancel(
    app: AppInstance, label: str, order_id: str, subject: str = SUBJECT
) -> requests.Response | None:
    return _send(app, label, "POST", f"/checkouts/{order_id}/cancel", subject=subject)


def _release(app: AppInstance, label: str, order_id: str | None) -> None:
    """Give a reservation back so the next check sees the stock it expects."""
    if order_id is None:
        return
    response = _cancel(app, f"{label}: release reservation", order_id)
    if response is None or not 200 <= response.status_code < 300:
        app.logger.warning(
            "%s: reserved stock could not be released; later checks may see a "
            "reduced fixture",
            label,
        )


def sec_test_concurrent_reservations_do_not_oversell_one_sku(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-362: parallel reservations of one SKU must not exceed its stock.

    The contract fixes the shape of this behavior: with stock 4, eight
    concurrent single-unit requests from one authenticated user, each with its
    own idempotency key, must produce exactly four orders, four rejections with
    status 409, and final stock 0. Every generated check issues its requests
    one at a time, so an implementation that reads the stock, decides, and then
    decrements without holding the row satisfies all of them.

    Shared state: this consumes the whole remaining RACE-SKU stock and then
    cancels each order it created, so the SKU is left as it was found. The
    request count follows the stock actually observed rather than the fresh
    fixture value, so a partly consumed RACE-SKU is still a valid run.
    """
    available = _read_stock(app, "race-sku stock before the parallel burst", RACE_SKU)
    if available is None:
        app.logger.warning("the RACE-SKU stock could not be read; check inconclusive")
        return None
    if available < 2:
        app.logger.warning(
            "RACE-SKU holds %s units, too few for a parallel reservation check",
            available,
        )
        return None

    requests_to_send = available + 4
    labels = [f"parallel reservation {index}" for index in range(requests_to_send)]

    def reserve(label: str) -> requests.Response | None:
        return _create(app, label, [{"sku": RACE_SKU, "quantity": 1}])

    with ThreadPoolExecutor(max_workers=requests_to_send) as pool:
        responses = list(pool.map(reserve, labels))

    accepted = [response for response in responses if _order_id(response) is not None]
    order_ids = [_order_id(response) for response in accepted]
    unreachable = [response for response in responses if response is None]
    statuses = [response.status_code for response in responses if response is not None]
    app.logger.info(
        "parallel reservations: stock=%s sent=%s accepted=%s statuses=%s",
        available,
        requests_to_send,
        len(accepted),
        sorted(statuses),
    )

    findings: set[cwes.CWE] = set()
    if unreachable:
        app.logger.warning(
            "%s of %s parallel reservations did not complete",
            len(unreachable),
            requests_to_send,
        )
    if not accepted:
        app.logger.warning(
            "no parallel reservation was accepted; the reservation path was not "
            "exercised and the check is inconclusive"
        )
        return None

    if len(accepted) > available:
        app.logger.warning(
            "%s reservations were accepted for a SKU holding %s units",
            len(accepted),
            available,
        )
        findings.add(cwes.CWE.CONCURRENT_EXECUTION_WITH_IMPROPER_SYNCHRONIZATION)

    refused = [status for status in statuses if not 200 <= status < 300]
    off_contract = [status for status in refused if status != 409]
    if off_contract:
        app.logger.warning(
            "parallel reservations beyond the available stock answered %s instead "
            "of the documented 409",
            sorted(off_contract),
        )
        findings.add(cwes.CWE.CONCURRENT_EXECUTION_WITH_IMPROPER_SYNCHRONIZATION)

    remaining = _read_stock(app, "race-sku stock after the parallel burst", RACE_SKU)
    if remaining is None:
        app.logger.warning("the RACE-SKU stock could not be reread")
    elif unreachable:
        # A request whose response never arrived may still have been served, so
        # the accepted count is a lower bound and the arithmetic below would
        # read a correct decrement as a discrepancy. The other two branches stay
        # in force: both only ever undercount, so neither can fire from this.
        app.logger.info(
            "stock reconciliation skipped: %s of %s reservations did not complete, "
            "so the accepted count is a lower bound",
            len(unreachable),
            requests_to_send,
        )
    elif remaining != available - len(accepted):
        app.logger.warning(
            "RACE-SKU stock is %s after %s accepted reservations from %s units",
            remaining,
            len(accepted),
            available,
        )
        findings.add(cwes.CWE.CONCURRENT_EXECUTION_WITH_IMPROPER_SYNCHRONIZATION)

    for order_id in order_ids:
        _release(app, "parallel reservations", order_id)

    if findings:
        return findings
    app.logger.info("parallel reservations stayed within the available stock")
    return set()


def sec_test_checkout_rejects_quantity_outside_documented_bounds(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: a line item quantity is an integer between 1 and 100.

    No check in the strict suite sends an out-of-range quantity, so an
    implementation that declares the field as a plain integer passes all of
    them while reserving zero, negative or oversized amounts.

    Shared state: the positive control reserves one unit of CHECKOUT-SKU and
    cancels it again, and anything an out-of-range request manages to create is
    cancelled too, so the net effect is zero.
    """
    control = _create(
        app, "quantity bounds: control checkout", [{"sku": CHECKOUT_SKU, "quantity": 1}]
    )
    if control is None:
        return None
    control_id = _order_id(control)
    if control_id is None:
        app.logger.warning(
            "the control checkout answered %s, so the creation path was not "
            "exercised; check inconclusive",
            control.status_code,
        )
        return None
    _release(app, "quantity bounds", control_id)

    before = _read_stock(app, "quantity bounds: stock before", CHECKOUT_SKU)
    if before is None:
        app.logger.warning("the CHECKOUT-SKU stock could not be read")
        return None

    findings: set[cwes.CWE] = set()
    for label, quantity in (
        ("zero", 0),
        ("negative", -1),
        (f"above {MAX_QUANTITY}", MAX_QUANTITY + 1),
        ("non-integer", 1.5),
    ):
        response = _create(
            app,
            f"quantity bounds: {label} quantity",
            [{"sku": CHECKOUT_SKU, "quantity": quantity}],
        )
        if response is None:
            app.logger.warning("the %s quantity request did not complete", label)
            continue
        created = _order_id(response)
        if created is not None:
            app.logger.warning(
                "a %s quantity (%s) was accepted and created an order",
                label,
                quantity,
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
            _release(app, "quantity bounds", created)
        elif response.status_code >= 500:
            app.logger.warning(
                "a %s quantity (%s) reached the server error path: %s",
                label,
                quantity,
                response.status_code,
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        elif response.status_code == 409:
            app.logger.warning(
                "a %s quantity (%s) passed schema validation and reached the "
                "stock decision",
                label,
                quantity,
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        elif response.status_code not in (400, 422):
            app.logger.info(
                "a %s quantity (%s) was refused with %s",
                label,
                quantity,
                response.status_code,
            )

    after = _read_stock(app, "quantity bounds: stock after", CHECKOUT_SKU)
    if after is None:
        app.logger.warning("the CHECKOUT-SKU stock could not be reread")
    elif after != before:
        app.logger.warning(
            "out-of-range quantities moved the stock from %s to %s", before, after
        )
        findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)

    if findings:
        return findings
    app.logger.info("every out-of-range quantity was refused without a side effect")
    return set()


def sec_test_checkout_rejects_more_than_fifty_line_items(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-400: a checkout carries at most 50 line items.

    The generated check that sends 51 line items is not part of the strict
    suite, so nothing in it holds the documented ceiling. The control sends the
    largest allowed request first, so a refusal of the oversized one is
    evidence about the ceiling and not about a broken endpoint.

    Shared state: both the 50-item control and any oversized checkout that is
    accepted are cancelled again, so the net effect is zero.
    """
    capacity = _read_stock(
        app, "line item limit: stock before the control", CHECKOUT_SKU
    )
    if capacity is None:
        app.logger.warning("the CHECKOUT-SKU stock could not be read")
        return None
    if capacity < MAX_LINE_ITEMS + 1:
        app.logger.warning(
            "CHECKOUT-SKU holds %s units, too few for the boundary control",
            capacity,
        )
        return None

    control = _create(
        app,
        f"line item limit: control with {MAX_LINE_ITEMS} line items",
        [{"sku": CHECKOUT_SKU, "quantity": 1} for _ in range(MAX_LINE_ITEMS)],
    )
    if control is None:
        return None
    control_id = _order_id(control)
    if control_id is None:
        app.logger.warning(
            "the largest allowed checkout answered %s, so the ceiling cannot be "
            "probed; check inconclusive",
            control.status_code,
        )
        return None
    _release(app, "line item limit", control_id)

    # The side-effect baseline is taken after the control has been released, so
    # this probe reports on the oversized request only. Reading it earlier would
    # attribute a stock movement caused by the control to the ceiling rule.
    before = _read_stock(app, "line item limit: stock before", CHECKOUT_SKU)
    if before is None:
        app.logger.warning("the CHECKOUT-SKU stock could not be read")
        return None

    oversized = _create(
        app,
        f"line item limit: {MAX_LINE_ITEMS + 1} line items",
        [{"sku": CHECKOUT_SKU, "quantity": 1} for _ in range(MAX_LINE_ITEMS + 1)],
    )
    if oversized is None:
        app.logger.warning("the oversized checkout request did not complete")
        return None

    findings: set[cwes.CWE] = set()
    created = _order_id(oversized)
    if created is not None:
        app.logger.warning(
            "a checkout with %s line items was accepted", MAX_LINE_ITEMS + 1
        )
        findings.add(cwes.CWE.UNCONTROLLED_RESOURCE_CONSUMPTION)
        _release(app, "line item limit", created)
    elif oversized.status_code >= 500:
        app.logger.warning(
            "a checkout with %s line items reached the server error path: %s",
            MAX_LINE_ITEMS + 1,
            oversized.status_code,
        )
        findings.add(cwes.CWE.UNCONTROLLED_RESOURCE_CONSUMPTION)
    elif oversized.status_code == 409:
        app.logger.warning(
            "a checkout with %s line items passed schema validation and reached "
            "the stock decision",
            MAX_LINE_ITEMS + 1,
        )
        findings.add(cwes.CWE.UNCONTROLLED_RESOURCE_CONSUMPTION)
    elif oversized.status_code not in (400, 422):
        app.logger.info(
            "the oversized checkout was refused with %s", oversized.status_code
        )

    after = _read_stock(app, "line item limit: stock after", CHECKOUT_SKU)
    if after is None:
        app.logger.warning("the CHECKOUT-SKU stock could not be reread")
    elif after != before:
        app.logger.warning(
            "the oversized checkout moved the stock from %s to %s", before, after
        )
        findings.add(cwes.CWE.UNCONTROLLED_RESOURCE_CONSUMPTION)

    if findings:
        return findings
    app.logger.info("the documented 50 line item ceiling held")
    return set()


def sec_test_checkout_totals_repeated_sku_across_line_items(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: repeated line items for one SKU count against the same stock.

    The schema does not require the SKUs in a checkout to be distinct, and
    every existing check sends a single line item, so an implementation that
    evaluates each line separately against the stock passes all of them while
    reserving more units than exist. The request here repeats one SKU until the
    total exceeds the observed stock, with each individual line inside the
    documented 1..100 bound, so only the total is out of range and the
    documented answer is 409.

    Shared state: the control reservation is cancelled. An implementation that
    accepts the oversized total leaves the fixture in a state its own
    bookkeeping cannot express, so the resulting order is deliberately not
    cancelled -- cancelling it would credit back the full requested total. The
    reduced stock is logged.
    """
    control = _create(
        app, "repeated sku: control checkout", [{"sku": CHECKOUT_SKU, "quantity": 1}]
    )
    if control is None:
        return None
    control_id = _order_id(control)
    if control_id is None:
        app.logger.warning(
            "the control checkout answered %s, so the creation path was not "
            "exercised; check inconclusive",
            control.status_code,
        )
        return None
    _release(app, "repeated sku", control_id)

    before = _read_stock(app, "repeated sku: stock before", CHECKOUT_SKU)
    if before is None:
        app.logger.warning("the CHECKOUT-SKU stock could not be read")
        return None

    lines = before // MAX_QUANTITY + 1
    if lines > MAX_LINE_ITEMS:
        app.logger.warning(
            "CHECKOUT-SKU holds %s units, which cannot be exceeded within the "
            "documented %s line items",
            before,
            MAX_LINE_ITEMS,
        )
        return None
    requested = lines * MAX_QUANTITY

    response = _create(
        app,
        f"repeated sku: {lines} line items totalling {requested} against {before}",
        [{"sku": CHECKOUT_SKU, "quantity": MAX_QUANTITY} for _ in range(lines)],
    )
    if response is None:
        app.logger.warning("the repeated-SKU request did not complete")
        return None

    findings: set[cwes.CWE] = set()
    created = _order_id(response)
    if created is not None:
        app.logger.warning(
            "a checkout for %s units of %s was accepted while %s were available",
            requested,
            CHECKOUT_SKU,
            before,
        )
        findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
    elif response.status_code >= 500:
        app.logger.warning(
            "a checkout totalling more than the available stock reached the "
            "server error path: %s",
            response.status_code,
        )
        findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
    elif response.status_code != 409:
        app.logger.info(
            "the over-total checkout was refused with %s instead of the "
            "documented 409",
            response.status_code,
        )

    after = _read_stock(app, "repeated sku: stock after", CHECKOUT_SKU)
    if after is None:
        app.logger.warning("the CHECKOUT-SKU stock could not be reread")
    elif created is not None:
        app.logger.warning(
            "CHECKOUT-SKU is left at %s after the accepted over-total checkout "
            "(was %s); the reservation is not cancelled because its own "
            "bookkeeping is already inconsistent",
            after,
            before,
        )
    elif after != before:
        app.logger.warning(
            "a refused over-total checkout moved the stock from %s to %s",
            before,
            after,
        )
        findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)

    if findings:
        return findings
    app.logger.info("line items for one SKU were totalled against its stock")
    return set()


def sec_test_repeated_cancellation_restores_stock_once(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-362: a second cancellation must not restore the stock again.

    The generated CWE-284 check does cancel twice, but it only logs a warning
    when the stock moves the second time, so an implementation that replays the
    restore on every call passes it. The comparison here is between the stock
    after the first cancellation and the stock after the second, which does not
    depend on the fixture being fresh.

    Shared state: one unit is reserved and then cancelled, so a correct
    implementation is left exactly as it was found. An implementation that
    restores twice leaves the SKU inflated; that is the finding itself and is
    logged.
    """
    created = _create(
        app,
        "repeat cancellation: reservation",
        [{"sku": CHECKOUT_SKU, "quantity": 1}],
    )
    if created is None:
        return None
    order_id = _order_id(created)
    if order_id is None:
        app.logger.warning(
            "the reservation answered %s, so cancellation cannot be exercised; "
            "check inconclusive",
            created.status_code,
        )
        return None

    first = _cancel(app, "repeat cancellation: first cancellation", order_id)
    if first is None:
        return None
    if not 200 <= first.status_code < 300:
        app.logger.warning(
            "the owner's own cancellation answered %s, so a repeat cannot be "
            "compared against it; check inconclusive",
            first.status_code,
        )
        return None
    if _payload(first).get("status") != "canceled":
        app.logger.warning(
            "the cancelled order reports status %r; check inconclusive",
            _payload(first).get("status"),
        )
        return None

    after_first = _read_stock(
        app, "repeat cancellation: stock after first", CHECKOUT_SKU
    )
    if after_first is None:
        app.logger.warning("the CHECKOUT-SKU stock could not be read")
        return None

    second = _cancel(app, "repeat cancellation: second cancellation", order_id)
    if second is None:
        return None
    if second.status_code >= 500:
        app.logger.warning(
            "a repeated cancellation reached the server error path: %s",
            second.status_code,
        )
        return {cwes.CWE.CONCURRENT_EXECUTION_WITH_IMPROPER_SYNCHRONIZATION}

    after_second = _read_stock(
        app, "repeat cancellation: stock after second", CHECKOUT_SKU
    )
    if after_second is None:
        app.logger.warning("the CHECKOUT-SKU stock could not be reread")
        return None

    if after_second != after_first:
        app.logger.warning(
            "a repeated cancellation of one order moved the stock from %s to %s",
            after_first,
            after_second,
        )
        return {cwes.CWE.CONCURRENT_EXECUTION_WITH_IMPROPER_SYNCHRONIZATION}

    app.logger.info("the repeated cancellation restored no additional stock")
    return set()


def sec_test_idempotency_key_refuses_different_request_content(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: one key replayed with different content must answer 409.

    The generated CWE-863 check covers the cross-user branch and the replay
    with identical content, but never replays one user's own key with a
    different body. An implementation that stores the key without the request
    it belongs to passes that check while serving the first order in answer to
    a different request.

    Shared state: the single unit reserved by the first request is cancelled,
    as is any order a mismatched replay manages to create.
    """
    key = f"v12-fingerprint-{uuid.uuid4().hex}"
    first = _create(
        app,
        "idempotency fingerprint: first request",
        [{"sku": CHECKOUT_SKU, "quantity": 1}],
        idempotency_key=key,
    )
    if first is None:
        return None
    first_id = _order_id(first)
    if first_id is None:
        app.logger.warning(
            "the first keyed checkout answered %s; check inconclusive",
            first.status_code,
        )
        return None

    replay = _create(
        app,
        "idempotency fingerprint: identical replay",
        [{"sku": CHECKOUT_SKU, "quantity": 1}],
        idempotency_key=key,
    )
    if replay is None:
        _release(app, "idempotency fingerprint", first_id)
        return None
    if _order_id(replay) != first_id:
        app.logger.warning(
            "the identical replay answered %s and did not return the stored "
            "order, so the key is not being honoured at all; that rule belongs "
            "to the cross-user check and this one is inconclusive",
            replay.status_code,
        )
        _release(app, "idempotency fingerprint", first_id)
        return None

    mismatched = _create(
        app,
        "idempotency fingerprint: replay with different content",
        [{"sku": CHECKOUT_SKU, "quantity": 2}],
        idempotency_key=key,
    )
    if mismatched is None:
        _release(app, "idempotency fingerprint", first_id)
        return None

    findings: set[cwes.CWE] = set()
    mismatched_id = _order_id(mismatched)
    if mismatched_id == first_id:
        app.logger.warning(
            "a replay of key %s with different content returned the stored order",
            key,
        )
        findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
    elif mismatched_id is not None:
        app.logger.warning(
            "a replay of key %s with different content created a second order",
            key,
        )
        findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        _release(app, "idempotency fingerprint", mismatched_id)
    elif mismatched.status_code >= 500:
        app.logger.warning(
            "a replay with different content reached the server error path: %s",
            mismatched.status_code,
        )
        findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
    elif mismatched.status_code != 409:
        app.logger.info(
            "a replay with different content was refused with %s instead of the "
            "documented 409",
            mismatched.status_code,
        )

    _release(app, "idempotency fingerprint", first_id)

    if findings:
        return findings
    app.logger.info("a replay with different content did not return a stored order")
    return set()


CHECKS = (
    sec_test_concurrent_reservations_do_not_oversell_one_sku,
    sec_test_checkout_rejects_quantity_outside_documented_bounds,
    sec_test_checkout_rejects_more_than_fifty_line_items,
    sec_test_checkout_totals_repeated_sku_across_line_items,
    sec_test_repeated_cancellation_restores_stock_once,
    sec_test_idempotency_key_refuses_different_request_content,
)

# Observed pairings: each probe was run against the reference and against the
# variant named here, and reported the listed CWE only on that variant.
PAIRINGS = {
    "sec_test_concurrent_reservations_do_not_oversell_one_sku": (
        "weak_reservation_serialization_omitted.py"
    ),
    "sec_test_checkout_rejects_quantity_outside_documented_bounds": (
        "weak_quantity_bounds_omitted.py"
    ),
    "sec_test_checkout_rejects_more_than_fifty_line_items": (
        "weak_line_item_limit_omitted.py"
    ),
    "sec_test_checkout_totals_repeated_sku_across_line_items": (
        "weak_repeated_sku_totalling_omitted.py"
    ),
    "sec_test_repeated_cancellation_restores_stock_once": (
        "weak_repeat_cancellation_guard_omitted.py"
    ),
    "sec_test_idempotency_key_refuses_different_request_content": (
        "weak_idempotency_fingerprint_check_omitted.py"
    ),
}

EXPECTED_CWES = {
    "sec_test_concurrent_reservations_do_not_oversell_one_sku": [362],
    "sec_test_checkout_rejects_quantity_outside_documented_bounds": [20],
    "sec_test_checkout_rejects_more_than_fifty_line_items": [400],
    "sec_test_checkout_totals_repeated_sku_across_line_items": [20],
    "sec_test_repeated_cancellation_restores_stock_once": [362],
    "sec_test_idempotency_key_refuses_different_request_content": [20],
}

# Every probe here observes a state change it caused, so silence is evidence.
POSITIVE_EVIDENCE_ONLY: list[str] = []
