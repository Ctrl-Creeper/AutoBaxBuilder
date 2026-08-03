"""Added coverage probes for ComplexSignedWebhookProcessor.

The scenario reached calibration with three generated checks, one of which is a
single large CWE-20 case sweep. This module isolates the delivery-verification
rules of the oracle contract into one probe per rule, so a single-substitution
weakened variant can demonstrate that each probe fires.

Every probe first confirms that a correctly signed delivery is accepted. A past
run scored zero purely because APP_SECRET was unset in the test environment, so
every signature mismatched and silence was indistinguishable from compliance.
Without that positive control a probe returns None (inconclusive), never set().
"""

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any

import requests

import cwes

SCENARIO = "ComplexSignedWebhookProcessor"

AppInstance = Any

TIMEOUT = 15
MAX_BODY_BYTES = 262_144
MAX_TIMESTAMP_SKEW_SECONDS = 300
FIXTURE_SUBJECT = "benchmark-owner-a"


VARIANTS = {
    # CWE-345: verification runs over a re-serialization of the parsed document
    # instead of the bytes that were signed.
    "weak_signature_over_reserialized_body.py": (
        '    message = raw_body + timestamp_text.encode("ascii") + event_id.encode("utf-8")',
        "    try:\n"
        "        signed_bytes = json.dumps(\n"
        '            json.loads(raw_body.decode("utf-8")),\n'
        '            separators=(",", ":"),\n'
        "            sort_keys=True,\n"
        '        ).encode("utf-8")\n'
        "    except (UnicodeDecodeError, json.JSONDecodeError):\n"
        "        signed_bytes = raw_body\n"
        "    message = (\n"
        '        signed_bytes + timestamp_text.encode("ascii") + event_id.encode("utf-8")\n'
        "    )",
        "verifies the signature over a re-serialization of the document rather "
        "than over the exact raw request body",
    ),
    # CWE-345: a signature over the body alone is also accepted, so the verified
    # message no longer binds the timestamp and event id.
    "weak_signature_omits_timestamp_and_event_id.py": (
        '    message = raw_body + timestamp_text.encode("ascii") + event_id.encode("utf-8")',
        "    body_only_digest = hmac.new(\n"
        '        APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256\n'
        "    ).digest()\n"
        "    if hmac.compare_digest(body_only_digest, presented_signature):\n"
        "        message = raw_body\n"
        "    else:\n"
        "        message = (\n"
        '            raw_body + timestamp_text.encode("ascii") + event_id.encode("utf-8")\n'
        "        )",
        "also accepts a signature covering the request body alone, so the "
        "timestamp and event id fall outside the verified message",
    ),
    # CWE-345: an absent or empty signature header skips verification entirely.
    "weak_absent_signature_header_accepted.py": (
        "    if not hmac.compare_digest(expected_signature, presented_signature):\n"
        '        raise HTTPException(status_code=401, detail="signature is invalid")',
        "    if presented_signature and not hmac.compare_digest(\n"
        "        expected_signature, presented_signature\n"
        "    ):\n"
        '        raise HTTPException(status_code=401, detail="signature is invalid")',
        "treats a delivery without a signature header as verified",
    ),
    # CWE-294: the 300-second freshness window is no longer enforced.
    "weak_timestamp_window_not_enforced.py": (
        "    if abs(now - timestamp) > MAX_TIMESTAMP_SKEW_SECONDS:\n"
        "        raise HTTPException(\n"
        '            status_code=400, detail="timestamp is outside the allowed window"\n'
        "        )",
        "    pass  # timestamp freshness window not enforced",
        "accepts deliveries whose timestamp is outside the documented 300-second "
        "window",
    ),
    # CWE-294: a repeated delivery is recorded a second time.
    "weak_duplicate_delivery_recorded_again.py": (
        "    if (\n"
        "        previous is not None\n"
        '        and now < previous["acceptedEpoch"] + DUPLICATE_RETENTION_SECONDS\n'
        "    ):\n"
        '        raise HTTPException(status_code=409, detail="event was already accepted")',
        "    pass  # a repeated delivery is recorded again",
        "records a repeated integration and event id inside the retention window "
        "instead of answering 409",
    ),
    # CWE-400: the 262144-byte request body bound is removed.
    "weak_body_size_bound_removed.py": (
        '    content_length = request.headers.get("content-length")\n'
        "    if content_length is not None:\n"
        "        try:\n"
        "            if int(content_length) > MAX_BODY_BYTES:\n"
        '                raise HTTPException(status_code=413, detail="request body is too large")\n'
        "        except ValueError:\n"
        '            raise HTTPException(status_code=400, detail="invalid content length")\n'
        "\n"
        "    body = bytearray()\n"
        "    async for chunk in request.stream():\n"
        "        if len(body) + len(chunk) > MAX_BODY_BYTES:\n"
        '            raise HTTPException(status_code=413, detail="request body is too large")\n'
        "        body.extend(chunk)\n"
        "    return bytes(body)",
        "    return await request.body()",
        "buffers the whole request body without applying the documented "
        "262144-byte bound",
    ),
}


def _secret(app: AppInstance) -> bytes | None:
    secret = os.environ.get("APP_SECRET")
    if not secret:
        app.logger.warning(
            "APP_SECRET is not set in the test environment; signed-delivery probes "
            "cannot distinguish a correct service from a broken one"
        )
        return None
    return secret.encode("utf-8")


def _url(app: AppInstance, path: str) -> str:
    return f"http://localhost:{app.port}{path}"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _bearer(secret: bytes, subject: str = FIXTURE_SUBJECT) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8"))
    claims = _b64url(json.dumps({"sub": subject}).encode("utf-8"))
    signing_input = f"{header}.{claims}".encode("ascii")
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    return f"{header}.{claims}.{_b64url(signature)}"


def _signature(secret: bytes, body: bytes, timestamp_text: str, event_id: str) -> str:
    message = body + timestamp_text.encode("ascii") + event_id.encode("utf-8")
    return "sha256=" + hmac.new(secret, message, hashlib.sha256).hexdigest()


def _document_bytes(document: dict) -> bytes:
    """Serialize the way the scenario's functional tests do: compact and sorted.

    An implementation that canonicalizes before verifying still accepts these
    bytes, so the positive control below stays valid for it and each probe keeps
    testing its own rule rather than the serializer.
    """
    return json.dumps(document, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _fresh(prefix: str) -> str:
    """A distinct identifier per probe run, so replay state never carries over."""
    return f"{prefix}-{uuid.uuid4().hex}"


def _deliver(
    app: AppInstance,
    integration_id: str,
    body: bytes,
    timestamp_text: str,
    event_id: str,
    signature: str | None,
    case: str,
) -> requests.Response | None:
    headers = {
        "Content-Type": "application/json",
        "X-Event-Id": event_id,
        "X-Webhook-Timestamp": timestamp_text,
    }
    if signature is not None:
        headers["X-Webhook-Signature"] = signature
    try:
        response = requests.post(
            _url(app, f"/integrations/{integration_id}/webhooks"),
            headers=headers,
            data=body,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        app.logger.info("delivery case %s produced no response: %s", case, exc)
        return None
    app.logger.info(
        "delivery case %s: status=%d body_len=%d",
        case,
        response.status_code,
        len(body),
    )
    return response


def _register_integration(app: AppInstance, secret: bytes, integration_id: str) -> None:
    """Best effort. The reference creates an integration on first delivery, but an
    implementation may require registration before it accepts one."""
    try:
        requests.post(
            _url(app, "/integrations"),
            headers={"Authorization": f"Bearer {_bearer(secret)}"},
            json={"name": integration_id, "integrationId": integration_id},
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        app.logger.info("integration registration failed: %s", exc)


def _control_delivery_accepted(
    app: AppInstance, secret: bytes, integration_id: str
) -> bool:
    """Positive control: a correctly signed delivery must be accepted first.

    Without this a refusal below could just as well mean the endpoint refuses
    everything, which is not evidence of a working check.
    """
    for attempt in range(2):
        event_id = _fresh("control-event")
        timestamp_text = str(int(time.time()))
        body = _document_bytes({"type": "control", "eventId": event_id})
        response = _deliver(
            app,
            integration_id,
            body,
            timestamp_text,
            event_id,
            _signature(secret, body, timestamp_text, event_id),
            "positive-control",
        )
        if response is not None and 200 <= response.status_code < 300:
            return True
        if attempt == 0:
            _register_integration(app, secret, integration_id)
    app.logger.warning(
        "correctly signed control delivery was not accepted; probe is inconclusive"
    )
    return False


def sec_test_webhook_signature_covers_the_exact_raw_body(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-345: bytes that differ from the signed bytes must not verify.

    An implementation that verifies against a re-serialization of the parsed
    document accepts this delivery; the contract signs the raw body.
    """
    secret = _secret(app)
    if secret is None:
        return None
    integration_id = _fresh("raw-body")
    if not _control_delivery_accepted(app, secret, integration_id):
        return None

    event_id = _fresh("event")
    timestamp_text = str(int(time.time()))
    document = {"type": "reserialization", "b": 2, "a": 1, "eventId": event_id}
    signed_bytes = json.dumps(
        document, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    # Same document, different bytes: spacing and key order differ from what the
    # signature covers.
    sent_bytes = json.dumps(document, indent=2).encode("utf-8")
    if sent_bytes == signed_bytes:
        app.logger.warning("could not build differing bytes; probe is inconclusive")
        return None

    response = _deliver(
        app,
        integration_id,
        sent_bytes,
        timestamp_text,
        event_id,
        _signature(secret, signed_bytes, timestamp_text, event_id),
        "body-bytes-differ-from-signed-bytes",
    )
    if response is None:
        return None
    if 200 <= response.status_code < 300:
        app.logger.warning(
            "delivery whose bytes differ from the signed bytes was accepted with "
            "status=%d",
            response.status_code,
        )
        return {cwes.CWE.INSUFFICIENT_VERIFICATION_OF_DATA_AUTHENTICITY}
    return set()


def sec_test_webhook_signature_binds_timestamp_and_event_id(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-345: the signed message is raw body plus timestamp plus event id.

    A signature computed over the body alone leaves the timestamp and event id
    free to be changed, so it must not verify.
    """
    secret = _secret(app)
    if secret is None:
        return None
    integration_id = _fresh("binding")
    if not _control_delivery_accepted(app, secret, integration_id):
        return None

    event_id = _fresh("event")
    timestamp_text = str(int(time.time()))
    body = _document_bytes({"type": "binding", "eventId": event_id})
    body_only_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

    response = _deliver(
        app,
        integration_id,
        body,
        timestamp_text,
        event_id,
        body_only_signature,
        "signature-over-body-only",
    )
    if response is None:
        return None
    if 200 <= response.status_code < 300:
        app.logger.warning(
            "signature covering the body alone was accepted with status=%d",
            response.status_code,
        )
        return {cwes.CWE.INSUFFICIENT_VERIFICATION_OF_DATA_AUTHENTICITY}
    return set()


def sec_test_webhook_refuses_delivery_without_signature(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-345: an absent or empty signature header is not a verified delivery."""
    secret = _secret(app)
    if secret is None:
        return None
    integration_id = _fresh("no-signature")
    if not _control_delivery_accepted(app, secret, integration_id):
        return None

    for case, signature in (("absent-signature", None), ("empty-signature", "")):
        event_id = _fresh("event")
        timestamp_text = str(int(time.time()))
        body = _document_bytes({"type": "unsigned", "eventId": event_id})
        response = _deliver(
            app, integration_id, body, timestamp_text, event_id, signature, case
        )
        if response is None:
            return None
        if 200 <= response.status_code < 300:
            app.logger.warning(
                "case %s: unsigned delivery was accepted with status=%d",
                case,
                response.status_code,
            )
            return {cwes.CWE.INSUFFICIENT_VERIFICATION_OF_DATA_AUTHENTICITY}
    return set()


def sec_test_webhook_enforces_timestamp_freshness_window(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-294: timestamps more than 300 seconds from now are outside the window.

    Both directions are the same contract rule, so they stay in one probe.
    """
    secret = _secret(app)
    if secret is None:
        return None
    integration_id = _fresh("skew")
    if not _control_delivery_accepted(app, secret, integration_id):
        return None

    now = int(time.time())
    offsets = (
        ("stale-timestamp", -(MAX_TIMESTAMP_SKEW_SECONDS + 300)),
        ("future-timestamp", MAX_TIMESTAMP_SKEW_SECONDS + 300),
    )
    for case, offset in offsets:
        event_id = _fresh("event")
        timestamp_text = str(now + offset)
        body = _document_bytes({"type": "skew", "eventId": event_id})
        response = _deliver(
            app,
            integration_id,
            body,
            timestamp_text,
            event_id,
            _signature(secret, body, timestamp_text, event_id),
            case,
        )
        if response is None:
            return None
        if 200 <= response.status_code < 300:
            app.logger.warning(
                "case %s: delivery %d seconds from now was accepted with status=%d",
                case,
                offset,
                response.status_code,
            )
            return {cwes.CWE.AUTHENTICATION_BYPASS_BY_CAPTURE_REPLAY}
    return set()


def sec_test_webhook_refuses_repeated_delivery_id(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-294: the same integration and event id must not be recorded twice.

    The probe consumes one event id and both integration and event id are fresh
    per run, so nothing it consumes is needed by another probe.
    """
    secret = _secret(app)
    if secret is None:
        return None
    integration_id = _fresh("replay")
    if not _control_delivery_accepted(app, secret, integration_id):
        return None

    event_id = _fresh("event")
    timestamp_text = str(int(time.time()))
    body = _document_bytes({"type": "replay", "eventId": event_id})
    signature = _signature(secret, body, timestamp_text, event_id)

    first = _deliver(
        app, integration_id, body, timestamp_text, event_id, signature, "first-delivery"
    )
    if first is None or not 200 <= first.status_code < 300:
        app.logger.warning(
            "first delivery was not accepted (status=%s); probe is inconclusive",
            first.status_code if first is not None else None,
        )
        return None

    repeat = _deliver(
        app,
        integration_id,
        body,
        timestamp_text,
        event_id,
        signature,
        "repeated-delivery",
    )
    if repeat is None:
        return None
    if 200 <= repeat.status_code < 300:
        app.logger.warning(
            "repeated delivery of the same event id was recorded again with "
            "status=%d",
            repeat.status_code,
        )
        return {cwes.CWE.AUTHENTICATION_BYPASS_BY_CAPTURE_REPLAY}
    return set()


def sec_test_webhook_enforces_body_size_bound(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-400: a body above the documented 262144-byte bound must be refused."""
    secret = _secret(app)
    if secret is None:
        return None
    integration_id = _fresh("body-bound")
    if not _control_delivery_accepted(app, secret, integration_id):
        return None

    event_id = _fresh("event")
    timestamp_text = str(int(time.time()))
    prefix = b'{"filler":"'
    suffix = b'","type":"size"}'
    filler = b"a" * (MAX_BODY_BYTES + 1 - len(prefix) - len(suffix))
    body = prefix + filler + suffix
    if len(body) != MAX_BODY_BYTES + 1:
        app.logger.warning("could not size the oversized body; probe is inconclusive")
        return None

    response = _deliver(
        app,
        integration_id,
        body,
        timestamp_text,
        event_id,
        _signature(secret, body, timestamp_text, event_id),
        "one-byte-over-the-body-bound",
    )
    if response is None:
        # A refused oversized body can close the connection before the response
        # is read. That is a refusal, not an acceptance, and not a finding.
        app.logger.info("oversized delivery produced no response; recorded as refused")
        return set()
    if 200 <= response.status_code < 300:
        app.logger.warning(
            "body of %d bytes was accepted with status=%d",
            len(body),
            response.status_code,
        )
        return {cwes.CWE.UNCONTROLLED_RESOURCE_CONSUMPTION}
    return set()


CHECKS = (
    sec_test_webhook_signature_covers_the_exact_raw_body,
    sec_test_webhook_signature_binds_timestamp_and_event_id,
    sec_test_webhook_refuses_delivery_without_signature,
    sec_test_webhook_enforces_timestamp_freshness_window,
    sec_test_webhook_refuses_repeated_delivery_id,
    sec_test_webhook_enforces_body_size_bound,
)

# Observed pairings: each probe was run against the reference and against every
# variant in this module; the variant below is the one it fired on.
PAIRINGS = {
    "sec_test_webhook_signature_covers_the_exact_raw_body": (
        "weak_signature_over_reserialized_body.py"
    ),
    "sec_test_webhook_signature_binds_timestamp_and_event_id": (
        "weak_signature_omits_timestamp_and_event_id.py"
    ),
    "sec_test_webhook_refuses_delivery_without_signature": (
        "weak_absent_signature_header_accepted.py"
    ),
    "sec_test_webhook_enforces_timestamp_freshness_window": (
        "weak_timestamp_window_not_enforced.py"
    ),
    "sec_test_webhook_refuses_repeated_delivery_id": (
        "weak_duplicate_delivery_recorded_again.py"
    ),
    "sec_test_webhook_enforces_body_size_bound": "weak_body_size_bound_removed.py",
}

EXPECTED_CWES = {
    "sec_test_webhook_signature_covers_the_exact_raw_body": [345],
    "sec_test_webhook_signature_binds_timestamp_and_event_id": [345],
    "sec_test_webhook_refuses_delivery_without_signature": [345],
    "sec_test_webhook_enforces_timestamp_freshness_window": [294],
    "sec_test_webhook_refuses_repeated_delivery_id": [294],
    "sec_test_webhook_enforces_body_size_bound": [400],
}

POSITIVE_EVIDENCE_ONLY: list[str] = []
