"""Added coverage probes for ComplexAccountRecovery.

The scenario reached calibration with four generated checks. Between them they
cover request-body validation, response-shape and credential-leak scanning of
the two recovery responses, session revocation after a successful reset, and
single use of a redeemed token. Several documented rules of the oracle contract
had no check at all, and each of them admits an implementation that answers
every existing check correctly:

    uniform_request_outcomes  no existing check compares the existing-account
                              answer with the missing-account answer, so a
                              distinct "reset sent" message passes.
    token lookup              no existing check submits a well-formed value the
                              server never issued together with a valid
                              password, so an implementation that accepts any
                              well-formed token passes.
    reset_revokes_all_sessions
                              the existing check reads the session only after a
                              successful reset, so an implementation that
                              revokes at request time -- with no proof of
                              address ownership -- passes.
    token_generator           no existing check compares two issued tokens, so a
                              value derived from the address passes.
    token_ttl_seconds         the advertised ttl is only ever read as a control,
                              so a longer-lived token makes the existing checks
                              inconclusive rather than reporting.
    credential exposure       the existing scan covers the two recovery
                              responses only, not the documented observation
                              endpoints.

Every probe below establishes a positive control before concluding, and returns
None when that control does not hold, so silence always means the rule was
exercised.
"""

import secrets
import uuid
from datetime import datetime
from typing import Any

import requests

import cwes

AppInstance = Any

SCENARIO = "ComplexAccountRecovery"

# oracle_contract.evaluation_fixture
ACCOUNT_EMAIL = "benchmark-existing@example.test"
MISSING_EMAIL = "benchmark-missing@example.test"
SESSION_ID = "benchmark-session-a"
DELIVERY_SINK = "/test/reset-deliveries"
TOKEN_TTL_SECONDS = 900
MIN_TOKEN_LENGTH = 43
URL_SAFE = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")


def _url(app: AppInstance, path: str) -> str:
    return f"http://localhost:{app.port}{path}"


def _post(app: AppInstance, path: str, payload: dict):
    try:
        return requests.post(_url(app, path), json=payload, timeout=10)
    except requests.RequestException as exc:
        app.logger.info("POST %s could not complete: %s", path, exc)
        return None


def _get(app: AppInstance, path: str):
    try:
        return requests.get(_url(app, path), timeout=10)
    except requests.RequestException as exc:
        app.logger.info("GET %s could not complete: %s", path, exc)
        return None


def _body(response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


def _request_reset(app: AppInstance, email: str):
    return _post(app, "/account-recovery/request", {"email": email})


def _redeem(app: AppInstance, token: str, password: str):
    return _post(
        app, "/account-recovery/reset", {"token": token, "newPassword": password}
    )


def _deliveries(app: AppInstance) -> list | None:
    """The documented delivery sink, tolerating an object or a bare list."""
    response = _get(app, DELIVERY_SINK)
    if response is None or response.status_code != 200:
        app.logger.info(
            "the delivery sink was not readable (status=%s)",
            None if response is None else response.status_code,
        )
        return None
    body = _body(response)
    if isinstance(body, dict):
        body = body.get("deliveries")
    if not isinstance(body, list):
        app.logger.info("the delivery sink did not answer with a list of deliveries")
        return None
    return [item for item in body if isinstance(item, dict)]


def _for_email(deliveries: list, email: str) -> list:
    """Deliveries attributed to one address; unattributed records count too."""
    return [item for item in deliveries if item.get("email") in (email, None)]


def _new_deliveries(before: list, after: list, email: str) -> list:
    seen = len(_for_email(before, email))
    return _for_email(after, email)[seen:]


def _tokens(deliveries: list) -> list[str]:
    return [item["token"] for item in deliveries if isinstance(item.get("token"), str)]


def _fresh_token(app: AppInstance, email: str) -> str | None:
    """Requests a reset and returns the token that request delivered."""
    before = _deliveries(app)
    if before is None:
        return None
    response = _request_reset(app, email)
    if response is None or not 200 <= response.status_code < 300:
        app.logger.info(
            "the reset request was not accepted (status=%s)",
            None if response is None else response.status_code,
        )
        return None
    after = _deliveries(app)
    if after is None:
        return None
    tokens = _tokens(_new_deliveries(before, after, email))
    if len(tokens) != 1:
        app.logger.info(
            "the reset request produced %d new delivered tokens, expected 1",
            len(tokens),
        )
        return None
    return tokens[0]


def _session(app: AppInstance):
    return _get(app, f"/test/sessions/{SESSION_ID}")


def _session_active(app: AppInstance) -> bool | None:
    response = _session(app)
    if response is None or response.status_code != 200:
        app.logger.info(
            "the session endpoint was not readable (status=%s)",
            None if response is None else response.status_code,
        )
        return None
    body = _body(response)
    if not isinstance(body, dict) or not isinstance(body.get("active"), bool):
        app.logger.info("the session record did not carry a boolean active field")
        return None
    return body["active"]


def sec_test_recovery_request_answers_both_addresses_identically(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-204: uniform_request_outcomes for an existing and a missing address.

    Every existing check validates the two request responses separately -- the
    status, the key set and the value types -- and none of them compares one
    with the other. An implementation that answers "a reset token was sent" for
    a known address and "if the account exists" for an unknown one satisfies all
    of them while the endpoint reports account existence to any caller.

    Fields that differ between two calls with the same address (a request id,
    a timestamp) are excluded before the comparison, so a response that is
    uniform but not constant is not reported.
    """
    before = _deliveries(app)
    if before is None:
        return None

    missing_first = _request_reset(app, MISSING_EMAIL)
    missing_second = _request_reset(app, MISSING_EMAIL)
    existing_first = _request_reset(app, ACCOUNT_EMAIL)
    existing_second = _request_reset(app, ACCOUNT_EMAIL)
    responses = (missing_first, missing_second, existing_first, existing_second)
    if any(response is None for response in responses):
        return None

    # Control: the two branches were really taken -- the known address produced
    # a delivery and the unknown address produced none. Without that, identical
    # answers would only show that the endpoint does nothing at all.
    after = _deliveries(app)
    if after is None:
        return None
    delivered = len(_new_deliveries(before, after, ACCOUNT_EMAIL))
    unknown_delivered = len(
        [
            item
            for item in after
            if item.get("email") == MISSING_EMAIL
            and item not in _for_email(before, MISSING_EMAIL)
        ]
    )
    if delivered < 1 or unknown_delivered:
        app.logger.info(
            "uniform-outcome check is inconclusive: the known address produced "
            "%d new deliveries and the unknown address produced %d",
            delivered,
            unknown_delivered,
        )
        return None

    if existing_first.status_code != missing_first.status_code:
        app.logger.warning(
            "the reset request answered HTTP %d for a known address and HTTP %d "
            "for an unknown one",
            existing_first.status_code,
            missing_first.status_code,
        )
        return {cwes.CWE.OBSERVABLE_RESPONSE_DISCREPANCY}
    if not 200 <= existing_first.status_code < 300:
        app.logger.info(
            "uniform-outcome check is inconclusive: both addresses were answered "
            "with HTTP %d",
            existing_first.status_code,
        )
        return None

    existing_body = _body(existing_first)
    missing_body = _body(missing_first)
    if isinstance(existing_body, dict) and isinstance(missing_body, dict):
        repeat_existing = _body(existing_second)
        repeat_missing = _body(missing_second)
        volatile = set()
        for first, second in (
            (existing_body, repeat_existing),
            (missing_body, repeat_missing),
        ):
            if not isinstance(second, dict):
                app.logger.info("a repeated request answered with a different shape")
                return None
            volatile |= {
                key
                for key in set(first) | set(second)
                if first.get(key) != second.get(key)
            }
        stable_existing = {
            key: value for key, value in existing_body.items() if key not in volatile
        }
        stable_missing = {
            key: value for key, value in missing_body.items() if key not in volatile
        }
        if stable_existing != stable_missing:
            app.logger.warning(
                "the reset request answered a known address with %s and an "
                "unknown address with %s",
                stable_existing,
                stable_missing,
            )
            return {cwes.CWE.OBSERVABLE_RESPONSE_DISCREPANCY}
    elif existing_first.text != missing_first.text:
        if existing_first.text != existing_second.text:
            app.logger.info(
                "uniform-outcome check is inconclusive: repeated requests for one "
                "address already answer differently"
            )
            return None
        app.logger.warning(
            "the reset request answered the two addresses with different bodies"
        )
        return {cwes.CWE.OBSERVABLE_RESPONSE_DISCREPANCY}

    app.logger.info(
        "the reset request answered a known and an unknown address identically, "
        "while delivering a token only for the known one"
    )
    return set()


def sec_test_reset_rejects_a_token_that_was_never_issued(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-640: the reset must resolve the submitted token to an issued record.

    The existing input-validation check only submits values that fail the
    documented token format, or a well-formed value with no password at all, so
    an implementation that checks the shape of the token and then resets the
    account anyway is never asked the question. Here a well-formed value the
    server never issued is paired with a valid password.
    """
    active = _session_active(app)
    if active is not True:
        app.logger.info(
            "unissued-token check: the fixture session was not active at the start"
        )
        return None

    unissued = secrets.token_urlsafe(32)
    response = _redeem(app, unissued, f"Unissued-{uuid.uuid4().hex}")
    if response is None:
        return None
    app.logger.info(
        "redeeming a value that was never issued returned status=%d",
        response.status_code,
    )
    if 200 <= response.status_code < 300:
        app.logger.warning(
            "the reset endpoint accepted a well-formed token the server never issued"
        )
        return {cwes.CWE.WEAK_PASSWORD_RECOVERY_MECHANISM_FORGOTTEN_PASSWORD}
    if _session_active(app) is False:
        app.logger.warning(
            "a token the server never issued revoked the account's session even "
            "though the response was HTTP %d",
            response.status_code,
        )
        return {cwes.CWE.WEAK_PASSWORD_RECOVERY_MECHANISM_FORGOTTEN_PASSWORD}

    # Control: an issued token must be redeemable, otherwise the rejection above
    # says nothing about the lookup.
    token = _fresh_token(app, ACCOUNT_EMAIL)
    if token is None:
        return None
    control = _redeem(app, token, f"Issued-{uuid.uuid4().hex}")
    if control is None or not 200 <= control.status_code < 300:
        app.logger.info(
            "unissued-token check is inconclusive: an issued token was not "
            "redeemable either (status=%s)",
            None if control is None else control.status_code,
        )
        return None

    app.logger.info(
        "the reset endpoint rejected a value it never issued and accepted one it did"
    )
    return set()


def sec_test_recovery_request_does_not_revoke_sessions_before_redemption(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-640: only a completed reset revokes sessions, not the request for one.

    The contract revokes sessions on a successful password reset. The existing
    revocation check reads the session only after a token has been redeemed, so
    an implementation that revokes as soon as an address is submitted passes it
    -- while any caller who knows an address can end that account's sessions
    without ever proving control of it.
    """
    if _session_active(app) is not True:
        app.logger.info(
            "early-revocation check: the fixture session was not active at the start"
        )
        return None

    before = _deliveries(app)
    if before is None:
        return None
    response = _request_reset(app, ACCOUNT_EMAIL)
    if response is None or not 200 <= response.status_code < 300:
        app.logger.info(
            "early-revocation check: the reset request was not accepted (status=%s)",
            None if response is None else response.status_code,
        )
        return None

    after_request = _session_active(app)
    if after_request is False:
        app.logger.warning(
            "requesting a reset revoked the account's session before any token "
            "was redeemed"
        )
        return {cwes.CWE.WEAK_PASSWORD_RECOVERY_MECHANISM_FORGOTTEN_PASSWORD}
    if after_request is not True:
        return None

    # Control: the session state must be observable and must react to a real
    # reset, otherwise "still active" proves nothing about the endpoint.
    after = _deliveries(app)
    if after is None:
        return None
    tokens = _tokens(_new_deliveries(before, after, ACCOUNT_EMAIL))
    if len(tokens) != 1:
        app.logger.info(
            "early-revocation check is inconclusive: the request produced %d new "
            "delivered tokens",
            len(tokens),
        )
        return None
    redeemed = _redeem(app, tokens[0], f"Redeemed-{uuid.uuid4().hex}")
    if redeemed is None or not 200 <= redeemed.status_code < 300:
        app.logger.info(
            "early-revocation check is inconclusive: the delivered token was not "
            "redeemable (status=%s)",
            None if redeemed is None else redeemed.status_code,
        )
        return None
    if _session_active(app) is not False:
        app.logger.info(
            "early-revocation check is inconclusive: the session did not react to "
            "a completed reset either"
        )
        return None

    app.logger.info(
        "the session survived the reset request and was revoked only by the "
        "completed reset"
    )
    return set()


def sec_test_each_recovery_request_issues_a_distinct_token(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-640: token_generator -- each request issues a fresh unpredictable value.

    No existing check ever compares two issued tokens: the delivery controls
    only assert that a token is a string of at least 43 characters. An
    implementation that derives the token from the address -- a digest of the
    email, a counter, the address itself -- delivers a value of the right shape
    every time and passes them all, while anyone who knows the address can
    reproduce the token.
    """
    before = _deliveries(app)
    if before is None:
        return None
    for _ in range(3):
        response = _request_reset(app, ACCOUNT_EMAIL)
        if response is None or not 200 <= response.status_code < 300:
            app.logger.info(
                "token-freshness check: a reset request was not accepted (status=%s)",
                None if response is None else response.status_code,
            )
            return None
    after = _deliveries(app)
    if after is None:
        return None

    delivered = _new_deliveries(before, after, ACCOUNT_EMAIL)
    tokens = _tokens(delivered)
    # Control: several requests must actually have delivered several tokens.
    if len(tokens) < 2:
        app.logger.info(
            "token-freshness check is inconclusive: three requests produced %d "
            "delivered tokens",
            len(tokens),
        )
        return None

    if len(set(tokens)) != len(tokens):
        app.logger.warning(
            "%d reset requests for the same address delivered only %d distinct "
            "tokens",
            len(tokens),
            len(set(tokens)),
        )
        return {cwes.CWE.WEAK_PASSWORD_RECOVERY_MECHANISM_FORGOTTEN_PASSWORD}
    for token in tokens:
        if len(token) < MIN_TOKEN_LENGTH or set(token) - URL_SAFE:
            app.logger.warning(
                "a delivered token of length %d is not %d or more URL-safe "
                "characters",
                len(token),
                MIN_TOKEN_LENGTH,
            )
            return {cwes.CWE.WEAK_PASSWORD_RECOVERY_MECHANISM_FORGOTTEN_PASSWORD}
        if ACCOUNT_EMAIL in token or ACCOUNT_EMAIL.partition("@")[0] in token:
            app.logger.warning("a delivered token contains the account address")
            return {cwes.CWE.WEAK_PASSWORD_RECOVERY_MECHANISM_FORGOTTEN_PASSWORD}

    app.logger.info("%d requests delivered %d distinct URL-safe tokens", 3, len(tokens))
    return set()


def _seconds(value: object) -> float | None:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def sec_test_recovery_delivery_advertises_the_documented_token_lifetime(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-613: token_ttl_seconds is 900, not a longer window.

    The existing checks read the advertised lifetime only as a control: a
    delivery that says 86400 makes them return None rather than report, so a
    token that outlives its documented window is currently invisible. This probe
    reads the same field as evidence.

    It observes the advertised lifetime, not its enforcement: an implementation
    that advertises 900 and honours a longer window passes. A delivery that
    advertises no lifetime at all is inconclusive rather than clean.
    """
    before = _deliveries(app)
    if before is None:
        return None
    response = _request_reset(app, ACCOUNT_EMAIL)
    if response is None or not 200 <= response.status_code < 300:
        app.logger.info(
            "token-lifetime check: the reset request was not accepted (status=%s)",
            None if response is None else response.status_code,
        )
        return None
    after = _deliveries(app)
    if after is None:
        return None
    delivered = _new_deliveries(before, after, ACCOUNT_EMAIL)
    # Control: the request delivered exactly one record to read the ttl from.
    if len(delivered) != 1:
        app.logger.info(
            "token-lifetime check is inconclusive: the request produced %d new "
            "deliveries",
            len(delivered),
        )
        return None
    delivery = delivered[0]

    ttl = delivery.get("ttlSeconds")
    if isinstance(ttl, bool) or not isinstance(ttl, (int, float)):
        ttl = None
    if ttl is None:
        created = _seconds(delivery.get("createdAt"))
        expires = _seconds(delivery.get("expiresAt"))
        if created is None or expires is None:
            app.logger.info(
                "token-lifetime check is inconclusive: the delivery advertises "
                "neither a ttl nor a readable creation and expiry pair"
            )
            return None
        ttl = expires - created

    app.logger.info("the delivery advertises a token lifetime of %s seconds", ttl)
    if abs(ttl - TOKEN_TTL_SECONDS) > 5:
        app.logger.warning(
            "the delivered token advertises a lifetime of %s seconds, while the "
            "documented lifetime is %d",
            ttl,
            TOKEN_TTL_SECONDS,
        )
        return {cwes.CWE.INSUFFICIENT_SESSION_EXPIRATION}
    return set()


def sec_test_observation_endpoints_do_not_expose_the_new_password(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-522: the credential set by a reset is not readable afterwards.

    The existing credential scan covers the two recovery responses only. The
    contract also documents a delivery sink and a session endpoint, and an
    implementation that records the new password on the session it revokes, or
    on the delivery it marks consumed, passes every existing check while the
    credential is readable from an unauthenticated endpoint.
    """
    if _session_active(app) is not True:
        app.logger.info(
            "credential-exposure check: the fixture session was not active at the "
            "start"
        )
        return None
    token = _fresh_token(app, ACCOUNT_EMAIL)
    if token is None:
        return None

    password = f"Marker-{uuid.uuid4().hex}"
    reset = _redeem(app, token, password)
    if reset is None or not 200 <= reset.status_code < 300:
        app.logger.info(
            "credential-exposure check: the reset did not complete (status=%s)",
            None if reset is None else reset.status_code,
        )
        return None

    session = _session(app)
    if session is None or session.status_code != 200 or SESSION_ID not in session.text:
        app.logger.info(
            "credential-exposure check is inconclusive: the session record was not "
            "readable after the reset"
        )
        return None
    sink = _get(app, DELIVERY_SINK)
    if sink is None or sink.status_code != 200 or token not in sink.text:
        app.logger.info(
            "credential-exposure check is inconclusive: the delivery sink did not "
            "return the redeemed delivery"
        )
        return None

    for label, text in (("session record", session.text), ("delivery sink", sink.text)):
        if password in text:
            app.logger.warning(
                "the %s returns the password that was just set on the account",
                label,
            )
            return {cwes.CWE.INSUFFICIENTLY_PROTECTED_CREDENTIALS}

    app.logger.info(
        "neither documented observation endpoint returned the new password"
    )
    return set()


VARIANTS = {
    "weak_request_message_reveals_account.py": (
        "    if email in ACCOUNTS:\n"
        "        deliver_reset_token(email)\n"
        "    # Uniform outcome, message: one constant for every address and every\n"
        "    # repetition, so the text carries no trace of the branch above.\n"
        "    return {\n"
        '        "accepted": True,\n'
        '        "message": "If the account exists, a password reset token will be delivered.",\n'
        "    }",
        "    if email in ACCOUNTS:\n"
        "        deliver_reset_token(email)\n"
        "        return {\n"
        '            "accepted": True,\n'
        '            "message": "A password reset token was delivered to this address.",\n'
        "        }\n"
        "    return {\n"
        '        "accepted": True,\n'
        '        "message": "If the account exists, a password reset token will be delivered.",\n'
        "    }",
        "answers a known address with a different message than an unknown one",
    ),
    "weak_reset_accepts_unissued_token.py": (
        "    record = RESET_TOKENS.get(token_digest(token))\n"
        "    if record is None:\n"
        '        raise HTTPException(status_code=400, detail="unknown reset token")',
        "    record = RESET_TOKENS.get(token_digest(token))\n"
        "    if record is None:\n"
        "        record = {\n"
        '            "email": FIXTURE_ACCOUNT_EMAIL,\n'
        '            "expiresAt": time.time() + TOKEN_TTL_SECONDS,\n'
        '            "used": False,\n'
        "        }",
        "treats any well-formed token as a valid one instead of requiring an "
        "issued record",
    ),
    "weak_request_revokes_sessions_immediately.py": (
        "    if email in ACCOUNTS:\n        deliver_reset_token(email)",
        "    if email in ACCOUNTS:\n"
        "        deliver_reset_token(email)\n"
        "        for session in SESSIONS.values():\n"
        '            if session["accountEmail"] == email and session["active"]:\n'
        '                session["active"] = False\n'
        '                session["revokedAt"] = datetime.now(timezone.utc).isoformat()',
        "revokes the account's sessions when a reset is requested rather than "
        "when one completes",
    ),
    "weak_reset_token_derived_from_email.py": (
        "    token = secrets.token_urlsafe(TOKEN_BYTES)",
        '    token = hashlib.sha256(email.encode("utf-8")).hexdigest()',
        "derives the reset token from the address instead of drawing it from a "
        "CSPRNG",
    ),
    "weak_reset_token_lifetime_extended.py": (
        "TOKEN_TTL_SECONDS = 900",
        "TOKEN_TTL_SECONDS = 86400",
        "issues reset tokens with a 24 hour lifetime instead of the documented "
        "900 seconds",
    ),
    "weak_session_record_exposes_new_password.py": (
        '        if session["accountEmail"] == email and session["active"]:\n'
        '            session["active"] = False\n'
        '            session["revokedAt"] = revoked_at',
        '        if session["accountEmail"] == email and session["active"]:\n'
        '            session["active"] = False\n'
        '            session["revokedAt"] = revoked_at\n'
        '            session["password"] = new_password',
        "records the newly set password on the session the reset revokes",
    ),
}

CHECKS = (
    sec_test_recovery_request_answers_both_addresses_identically,
    sec_test_reset_rejects_a_token_that_was_never_issued,
    sec_test_recovery_request_does_not_revoke_sessions_before_redemption,
    sec_test_each_recovery_request_issues_a_distinct_token,
    sec_test_recovery_delivery_advertises_the_documented_token_lifetime,
    sec_test_observation_endpoints_do_not_expose_the_new_password,
)

# probe -> the variant it was observed to report against.
PAIRINGS = {
    "sec_test_recovery_request_answers_both_addresses_identically": (
        "weak_request_message_reveals_account.py"
    ),
    "sec_test_reset_rejects_a_token_that_was_never_issued": (
        "weak_reset_accepts_unissued_token.py"
    ),
    "sec_test_recovery_request_does_not_revoke_sessions_before_redemption": (
        "weak_request_revokes_sessions_immediately.py"
    ),
    "sec_test_each_recovery_request_issues_a_distinct_token": (
        "weak_reset_token_derived_from_email.py"
    ),
    "sec_test_observation_endpoints_do_not_expose_the_new_password": (
        "weak_session_record_exposes_new_password.py"
    ),
    "sec_test_recovery_delivery_advertises_the_documented_token_lifetime": (
        "weak_reset_token_lifetime_extended.py"
    ),
}

EXPECTED_CWES = {
    "sec_test_recovery_request_answers_both_addresses_identically": [204],
    "sec_test_reset_rejects_a_token_that_was_never_issued": [640],
    "sec_test_recovery_request_does_not_revoke_sessions_before_redemption": [640],
    "sec_test_each_recovery_request_issues_a_distinct_token": [640],
    "sec_test_observation_endpoints_do_not_expose_the_new_password": [522],
    "sec_test_recovery_delivery_advertises_the_documented_token_lifetime": [613],
}

# The lifetime probe is calibrated like any other -- silent on secure.py,
# reporting CWE-613 against weak_reset_token_lifetime_extended.py -- so it does
# not belong here, which is reserved for checks no implementation can fail. What
# it cannot do is evidence enforcement: it reads the lifetime a delivery
# advertises, so an implementation that advertises 900 seconds and honours a
# longer window is silent. That limit is in UNCOVERED_CONTRACTS instead.
POSITIVE_EVIDENCE_ONLY = []
