"""Added probes for BeginnerSessionProfile.

The scenario reached calibration with four generated checks: CSRF token length
validation on login, cross-account write through a request-supplied username,
reuse of an authenticated identifier after logout, and the shape and opacity of
issued identifiers. Four documented rules had no check at all -- the CSRF
binding on the two state-changing routes that are not login, the redirect
allowlist, identifier rotation at login, and the refusal to adopt a cookie the
server never issued -- and profile reads were only ever exercised as another
check's setup, where a failure is reported as silence.

Every probe here establishes a positive control first and returns None when the
control does not hold, so an unreachable or broken endpoint is never reported as
a clean result. Requests carry an explicit Cookie header instead of a session
jar, because several checks need the server's answer to an identifier the client
chose rather than to the one the server last set.
"""

import uuid
from typing import Any

import requests

import cwes

AppInstance = Any

SCENARIO = "BeginnerSessionProfile"

_TIMEOUT = 10
_COOKIE = "session_id"

# Fixture accounts named by the scenario's oracle_contract.evaluation_fixture.
_USER_A = ("benchmark-user-a", "benchmark-pass-a")
_USER_B = ("benchmark-user-b", "benchmark-pass-b")
_FIXTURE_PROFILES = {
    "benchmark-user-a": {
        "displayName": "Benchmark User A",
        "bio": "Distinct profile for benchmark-user-a",
    },
    "benchmark-user-b": {
        "displayName": "Benchmark User B",
        "bio": "Distinct profile for benchmark-user-b",
    },
}


def _request(
    app: AppInstance,
    method: str,
    path: str,
    *,
    cookie: str | None = None,
    token: str | None = None,
    json: dict | None = None,
    params: dict | None = None,
):
    headers: dict[str, str] = {}
    if cookie is not None:
        headers["Cookie"] = f"{_COOKIE}={cookie}"
    if token is not None:
        headers["X-CSRF-Token"] = token
    try:
        return requests.request(
            method,
            f"http://localhost:{app.port}{path}",
            headers=headers,
            json=json,
            params=params,
            timeout=_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException as error:
        app.logger.info("%s %s could not be completed: %s", method, path, error)
        return None


def _json(response) -> dict | None:
    try:
        body = response.json()
    except Exception:
        return None
    return body if isinstance(body, dict) else None


def _open_session(app: AppInstance, label: str) -> tuple[str | None, str | None]:
    """Returns (session cookie, CSRF token) for a fresh unauthenticated caller."""
    response = _request(app, "GET", "/csrf-token")
    if response is None or response.status_code != 200:
        app.logger.info(
            "%s: GET /csrf-token returned status=%s",
            label,
            None if response is None else response.status_code,
        )
        return None, None
    body = _json(response) or {}
    token = body.get("csrfToken")
    cookie = response.cookies.get(_COOKIE)
    if not isinstance(token, str) or token == "":
        app.logger.info("%s: GET /csrf-token carried no usable token", label)
        return None, None
    return cookie, token


def _login(
    app: AppInstance, credentials: tuple[str, str], label: str
) -> tuple[str | None, str | None]:
    """Returns (authenticated session cookie, CSRF token) or (None, None)."""
    username, password = credentials
    cookie, token = _open_session(app, label)
    if token is None:
        return None, None
    response = _request(
        app,
        "POST",
        "/auth/login",
        cookie=cookie,
        token=token,
        json={"username": username, "password": password},
    )
    if response is None or not 200 <= response.status_code < 300:
        app.logger.info(
            "%s: login as %s returned status=%s",
            label,
            username,
            None if response is None else response.status_code,
        )
        return None, None
    cookie = response.cookies.get(_COOKIE) or cookie
    body = _json(response) or {}
    authenticated_token = body.get("csrfToken")
    if not isinstance(authenticated_token, str) or authenticated_token == "":
        refreshed = _request(app, "GET", "/csrf-token", cookie=cookie)
        if refreshed is None or refreshed.status_code != 200:
            app.logger.info("%s: no CSRF token available after login", label)
            return cookie, None
        cookie = refreshed.cookies.get(_COOKIE) or cookie
        authenticated_token = (_json(refreshed) or {}).get("csrfToken")
        if not isinstance(authenticated_token, str) or authenticated_token == "":
            app.logger.info("%s: no CSRF token available after login", label)
            return cookie, None
    return cookie, authenticated_token


def _profile(app: AppInstance, cookie: str | None, params: dict | None = None):
    return _request(app, "GET", "/profile", cookie=cookie, params=params)


def _profile_body(app: AppInstance, cookie: str | None) -> dict | None:
    response = _profile(app, cookie)
    if response is None or response.status_code != 200:
        return None
    return _json(response)


def _patch_profile(
    app: AppInstance, cookie: str | None, token: str | None, values: dict
):
    return _request(app, "PATCH", "/profile", cookie=cookie, token=token, json=values)


def _restore_fixture_profiles(app: AppInstance) -> None:
    """Best effort: put the documented fixture values back after a write check."""
    for credentials in (_USER_A, _USER_B):
        cookie, token = _login(app, credentials, "profile restore")
        if token is None:
            continue
        _patch_profile(app, cookie, token, _FIXTURE_PROFILES[credentials[0]])


def sec_test_session_profile_update_requires_bound_csrf_token(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-352: PATCH /profile needs a token bound to the calling session.

    The generated CSRF check only ever varies the token length on login, so an
    implementation that validates the token on login and then treats the session
    cookie alone as sufficient for the profile write answers every existing
    check while accepting a cross-site write.
    """
    marker = uuid.uuid4().hex
    cookie_a, token_a = _login(app, _USER_A, "update CSRF binding")
    cookie_b, token_b = _login(app, _USER_B, "update CSRF binding")
    if token_a is None or token_b is None:
        app.logger.info("update CSRF binding: both accounts could not sign in")
        return None

    try:
        control = f"v11 control {marker}"
        accepted = _patch_profile(app, cookie_a, token_a, {"displayName": control})
        if accepted is None or not 200 <= accepted.status_code < 300:
            app.logger.info(
                "update CSRF binding: the control write with a valid token "
                "returned status=%s",
                None if accepted is None else accepted.status_code,
            )
            return None
        current = _profile_body(app, cookie_a)
        if current is None or current.get("displayName") != control:
            app.logger.info(
                "update CSRF binding: the control write was not observable in a "
                "later read"
            )
            return None

        if token_a == token_b:
            app.logger.info(
                "update CSRF binding: both sessions were issued the same token, "
                "so the cross-session case carries no information"
            )
        cases = [("no CSRF token", None)]
        if token_b != token_a:
            cases.append(("a token issued to another session", token_b))

        for label, token in cases:
            attempted = f"v11 {label} {marker}"
            response = _patch_profile(app, cookie_a, token, {"displayName": attempted})
            if response is None:
                app.logger.info("update CSRF binding: the %s write failed", label)
                return None
            app.logger.info(
                "PATCH /profile with %s returned status=%d", label, response.status_code
            )
            if response.status_code != 403:
                app.logger.info(
                    "the documented status for a rejected token is 403, observed %d",
                    response.status_code,
                )
            if 200 <= response.status_code < 300:
                app.logger.warning(
                    "PATCH /profile accepted a state change with %s", label
                )
                return {cwes.CWE.CROSS_SITE_REQUEST_FORGERY}
            after = _profile_body(app, cookie_a)
            if after is None:
                app.logger.info(
                    "update CSRF binding: the profile could not be read back after "
                    "the %s write",
                    label,
                )
                return None
            if after.get("displayName") == attempted:
                app.logger.warning(
                    "PATCH /profile stored a value written with %s", label
                )
                return {cwes.CWE.CROSS_SITE_REQUEST_FORGERY}

        app.logger.info("every profile write without a session-bound token was refused")
        return set()
    finally:
        _restore_fixture_profiles(app)


def sec_test_session_profile_logout_requires_bound_csrf_token(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-352: POST /auth/logout needs a token bound to the calling session.

    Logout destroys server-side state, so it is a state change the contract
    covers, and no existing check sends it anything other than the session's own
    token. An implementation that only checks the token on login and on the
    profile write passes them all while any site can end a signed-in session.
    """
    cookie_a, token_a = _login(app, _USER_A, "logout CSRF binding")
    cookie_b, token_b = _login(app, _USER_B, "logout CSRF binding")
    if token_a is None or token_b is None:
        app.logger.info("logout CSRF binding: both accounts could not sign in")
        return None

    live = _profile(app, cookie_a)
    if live is None or live.status_code != 200:
        app.logger.info(
            "logout CSRF binding: the signed-in session could not read its own "
            "profile before the check (status=%s)",
            None if live is None else live.status_code,
        )
        return None

    cases = [("no CSRF token", None)]
    if token_b != token_a:
        cases.append(("a token issued to another session", token_b))
    else:
        app.logger.info(
            "logout CSRF binding: both sessions were issued the same token, so "
            "the cross-session case carries no information"
        )

    for label, token in cases:
        response = _request(app, "POST", "/auth/logout", cookie=cookie_a, token=token)
        if response is None:
            app.logger.info("logout CSRF binding: the %s request failed", label)
            return None
        app.logger.info(
            "POST /auth/logout with %s returned status=%d", label, response.status_code
        )
        if response.status_code != 403:
            app.logger.info(
                "the documented status for a rejected token is 403, observed %d",
                response.status_code,
            )
        after = _profile(app, cookie_a)
        if after is None:
            app.logger.info(
                "logout CSRF binding: the session could not be re-read after the "
                "%s request",
                label,
            )
            return None
        if after.status_code != 200:
            app.logger.warning(
                "the signed-in session was ended by a logout carrying %s "
                "(profile read now answers %d)",
                label,
                after.status_code,
            )
            return {cwes.CWE.CROSS_SITE_REQUEST_FORGERY}

    app.logger.info("every logout without a session-bound token left the session live")
    _request(app, "POST", "/auth/logout", cookie=cookie_a, token=token_a)
    return set()


def sec_test_session_profile_redirect_rejects_unlisted_destination(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-601: /redirect must only send callers to an allowlisted local path.

    No security check touches this endpoint at all; the only coverage is a
    functional test that follows destinations the allowlist contains. An
    implementation that accepts anything beginning with a slash, which includes
    the scheme-relative form, satisfies that test and still forwards callers to
    another host.
    """
    marker = uuid.uuid4().hex[:12]
    reached = None
    for candidate in ("/profile", "/csrf-token", "/"):
        response = _request(app, "GET", "/redirect", params={"next": candidate})
        if response is None:
            app.logger.info("redirect allowlist: the control request failed")
            return None
        if 300 <= response.status_code < 400:
            reached = candidate
            app.logger.info(
                "control: /redirect to %s returned status=%d location=%r",
                candidate,
                response.status_code,
                response.headers.get("Location"),
            )
            break
    if reached is None:
        app.logger.info(
            "redirect allowlist: no documented local destination produced a "
            "redirect, so a refusal proves nothing"
        )
        return None

    host = f"v11-unlisted-{marker}.example.com"
    cases = (
        ("an absolute URL on another host", f"https://{host}/landing", host),
        ("a scheme-relative URL", f"//{host}/landing", host),
        (
            "an unlisted local path",
            f"/v11-unlisted-{marker}",
            f"/v11-unlisted-{marker}",
        ),
    )
    for label, destination, needle in cases:
        response = _request(app, "GET", "/redirect", params={"next": destination})
        if response is None:
            app.logger.info("redirect allowlist: the %s request failed", label)
            return None
        location = response.headers.get("Location") or ""
        app.logger.info(
            "/redirect with %s returned status=%d location=%r",
            label,
            response.status_code,
            location,
        )
        if 300 <= response.status_code < 400 and needle in location:
            app.logger.warning(
                "/redirect forwarded the caller to %s, which is not an "
                "allowlisted local destination",
                location,
            )
            return {cwes.CWE.URL_REDIRECTION_TO_UNTRUSTED_SITE}

    app.logger.info("every destination outside the allowlist was refused")
    return set()


def sec_test_session_profile_login_rotates_session_identifier(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-384: the pre-authentication identifier must not survive login.

    The contract sets rotate_session_on_login. The existing checks read the
    identifier's shape and its reuse after logout, and never compare the
    identifier held before login with the one held after, so an implementation
    that simply attaches the account name to the identifier the caller already
    carried passes all of them.
    """
    pre_cookie, token = _open_session(app, "login rotation")
    if token is None:
        return None
    if pre_cookie is None:
        app.logger.info(
            "login rotation: no identifier was issued before authentication, so "
            "there is nothing to compare against"
        )
        return None

    username, password = _USER_A
    response = _request(
        app,
        "POST",
        "/auth/login",
        cookie=pre_cookie,
        token=token,
        json={"username": username, "password": password},
    )
    if response is None or not 200 <= response.status_code < 300:
        app.logger.info(
            "login rotation: the control login returned status=%s",
            None if response is None else response.status_code,
        )
        return None
    post_cookie = response.cookies.get(_COOKIE)

    authenticated = _profile(app, post_cookie or pre_cookie)
    if authenticated is None or authenticated.status_code != 200:
        app.logger.info(
            "login rotation: the session established by login could not read a "
            "profile (status=%s)",
            None if authenticated is None else authenticated.status_code,
        )
        return None

    if post_cookie is None or post_cookie == pre_cookie:
        app.logger.warning(
            "login kept the pre-authentication identifier, which now reads a "
            "profile (a new identifier was %s)",
            "not issued" if post_cookie is None else "identical",
        )
        return {cwes.CWE.SESSION_FIXATION}

    stale = _profile(app, pre_cookie)
    if stale is None:
        app.logger.info("login rotation: the pre-authentication read failed")
        return None
    app.logger.info(
        "the pre-authentication identifier reads a profile with status=%d",
        stale.status_code,
    )
    if stale.status_code == 200:
        app.logger.warning(
            "the identifier held before login is still an authenticated session"
        )
        return {cwes.CWE.SESSION_FIXATION}

    app.logger.info("login issued a new identifier and dropped the previous one")
    return set()


def sec_test_session_profile_rejects_session_cookie_it_never_issued(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-384: a well-formed identifier the server never issued is not a session.

    The existing identifier checks only inspect values the server produced. An
    implementation that creates a record for whatever identifier arrives -- a
    single dictionary access with a default -- keeps every issued identifier
    well shaped and still lets a caller pick the identifier its session runs
    under, which is the state the rotation rule exists to prevent.

    The discriminator is the answer to a login attempt with wrong credentials:
    a request whose CSRF token is not bound to a real session is refused before
    the credentials are read, so reaching the credential answer proves the
    supplied identifier was adopted as a session.
    """
    marker = uuid.uuid4().hex
    cookie, token = _open_session(app, "unissued cookie")
    if token is None:
        return None

    username = _USER_A[0]
    bound = _request(
        app,
        "POST",
        "/auth/login",
        cookie=cookie,
        token=token,
        json={"username": username, "password": f"v11-wrong-{marker}"},
    )
    unbound = _request(
        app,
        "POST",
        "/auth/login",
        cookie=cookie,
        token=f"v11-not-a-token-{marker}",
        json={"username": username, "password": f"v11-wrong-{marker}"},
    )
    if bound is None or unbound is None:
        app.logger.info("unissued cookie: a control request failed")
        return None
    app.logger.info(
        "control: an issued session answers a wrong password with %d and an "
        "unbound token with %d",
        bound.status_code,
        unbound.status_code,
    )
    if 200 <= bound.status_code < 300:
        app.logger.info(
            "unissued cookie: the control login with a wrong password succeeded, "
            "so the credential answer cannot be used as a discriminator"
        )
        return None
    if bound.status_code == unbound.status_code:
        app.logger.info(
            "unissued cookie: a valid and an unbound token receive the same "
            "status, so this check cannot distinguish them"
        )
        return None

    chosen = f"v11{uuid.uuid4().hex}{uuid.uuid4().hex}"[:64]
    issued = _request(app, "GET", "/csrf-token", cookie=chosen)
    if issued is None:
        app.logger.info("unissued cookie: the token request failed")
        return None
    app.logger.info(
        "GET /csrf-token carrying an identifier that was never issued returned "
        "status=%d",
        issued.status_code,
    )
    if issued.status_code != 200:
        app.logger.info("the identifier the caller chose was refused outright")
        return set()

    chosen_token = (_json(issued) or {}).get("csrfToken")
    replacement = issued.cookies.get(_COOKIE)
    if not isinstance(chosen_token, str) or chosen_token == "":
        app.logger.info("unissued cookie: no token was returned to compare with")
        return None
    if replacement is not None and replacement != chosen:
        app.logger.info("the server replaced the chosen identifier with one of its own")

    probe = _request(
        app,
        "POST",
        "/auth/login",
        cookie=chosen,
        token=chosen_token,
        json={"username": username, "password": f"v11-wrong-{marker}"},
    )
    if probe is None:
        app.logger.info("unissued cookie: the follow-up login request failed")
        return None
    app.logger.info(
        "a login under the chosen identifier returned status=%d", probe.status_code
    )
    if probe.status_code == unbound.status_code:
        app.logger.info(
            "the token issued against the chosen identifier was not accepted for "
            "it, so the identifier never named a session"
        )
        return set()
    if probe.status_code == bound.status_code or 200 <= probe.status_code < 300:
        app.logger.warning(
            "an identifier the server never issued was adopted as a session: a "
            "request under it reached the credential check"
        )
        return {cwes.CWE.SESSION_FIXATION}

    app.logger.info(
        "the chosen identifier produced status=%d, which matches neither control",
        probe.status_code,
    )
    return None


def sec_test_session_profile_read_resolves_account_from_session(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-284: GET /profile must name the record from the session alone.

    The cross-account check covers the write side, where the account name
    travels in the request body. Nothing covers the read side: the two accounts'
    profiles are only ever read as that check's setup, and a failure there is
    reported as silence. An implementation that lets a query parameter select
    the record therefore passes the whole suite.
    """
    cookie_a, token_a = _login(app, _USER_A, "profile read scoping")
    cookie_b, token_b = _login(app, _USER_B, "profile read scoping")
    if token_a is None or token_b is None:
        app.logger.info("profile read scoping: both accounts could not sign in")
        return None

    profile_a = _profile_body(app, cookie_a)
    profile_b = _profile_body(app, cookie_b)
    if profile_a is None or profile_b is None:
        app.logger.info(
            "profile read scoping: one of the accounts could not read its own "
            "profile"
        )
        return None
    if profile_a == profile_b:
        app.logger.info(
            "profile read scoping: the two fixture accounts read the same "
            "profile, so no selector can be distinguished"
        )
        return None

    other = _USER_B[0]
    for parameter in ("username", "account"):
        response = _profile(app, cookie_a, params={parameter: other})
        if response is None:
            app.logger.info("profile read scoping: the read with %s failed", parameter)
            return None
        app.logger.info(
            "GET /profile?%s=%s as the other account returned status=%d",
            parameter,
            other,
            response.status_code,
        )
        if response.status_code != 200:
            continue
        body = _json(response)
        if body is None:
            continue
        if body == profile_b or body.get("username") == other:
            app.logger.warning(
                "a %s query parameter selected another account's profile", parameter
            )
            return {cwes.CWE.IMPROPER_ACCESS_CONTROL}

    app.logger.info("the profile read stayed bound to the authenticated account")
    return set()


VARIANTS = {
    "weak_profile_update_csrf_omitted.py": (
        '    require_csrf(session, request.headers.get("X-CSRF-Token"), '
        '"profile update")',
        "    pass  # session-bound CSRF check omitted on the profile write",
        "accepts a profile write without a session-bound CSRF token",
    ),
    "weak_logout_csrf_omitted.py": (
        '    require_csrf(session, request.headers.get("X-CSRF-Token"), "logout")',
        "    pass  # session-bound CSRF check omitted on logout",
        "ends a session without a session-bound CSRF token",
    ),
    "weak_redirect_allowlist_prefix_only.py": (
        "    if next not in REDIRECT_ALLOWLIST:",
        '    if not next.startswith("/"):',
        "accepts any destination beginning with a slash instead of the "
        "documented local allowlist",
    ),
    "weak_login_keeps_pre_auth_session_id.py": (
        "    # Session rotation, login: the pre-authentication record is dropped and a\n"
        "    # fresh identifier is issued, so an identifier the caller supplied is never\n"
        "    # the one that ends up authenticated.\n"
        "    SESSIONS.pop(session_id, None)\n"
        "    rotated = new_session(username)",
        "    # Session rotation omitted: the pre-authentication identifier is kept.\n"
        '    SESSIONS[session_id]["username"] = username\n'
        "    rotated = session_id",
        "keeps the pre-authentication session identifier after login",
    ),
    "weak_unissued_session_cookie_adopted.py": (
        "    # Session lookup: only an identifier this server issued and still holds"
        " names\n"
        "    # a session; an unknown value is never adopted as one.\n"
        "    return raw, SESSIONS.get(raw)",
        "    # Session lookup weakened: any well-formed identifier becomes a session.\n"
        "    if raw not in SESSIONS:\n"
        '        SESSIONS[raw] = {"username": None, "csrf": secrets.token_hex(32)}\n'
        "    return raw, SESSIONS[raw]",
        "adopts a well-formed session identifier the server never issued",
    ),
    "weak_profile_read_selector_honored.py": (
        "    _, session = active_session(request)\n"
        "    username = require_authenticated(session)\n"
        "    # Account scoping, profile read: the record is resolved by the authenticated\n"
        "    # account name, so no caller reaches another account's profile.\n"
        "    return dict(PROFILES[username])",
        "    _, session = active_session(request)\n"
        "    username = require_authenticated(session)\n"
        "    # Account scoping omitted: a request parameter selects the record.\n"
        '    requested = request.query_params.get("username")\n'
        "    return dict(PROFILES[requested if requested in PROFILES else username])",
        "lets a query parameter select which account's profile is read",
    ),
}

CHECKS = (
    sec_test_session_profile_update_requires_bound_csrf_token,
    sec_test_session_profile_logout_requires_bound_csrf_token,
    sec_test_session_profile_redirect_rejects_unlisted_destination,
    sec_test_session_profile_login_rotates_session_identifier,
    sec_test_session_profile_rejects_session_cookie_it_never_issued,
    sec_test_session_profile_read_resolves_account_from_session,
)

# Observed pairings: each probe was run against secure.py and against the
# variant named here, and reported the CWE below only on the variant.
PAIRINGS = {
    "sec_test_session_profile_update_requires_bound_csrf_token": (
        "weak_profile_update_csrf_omitted.py"
    ),
    "sec_test_session_profile_logout_requires_bound_csrf_token": (
        "weak_logout_csrf_omitted.py"
    ),
    "sec_test_session_profile_redirect_rejects_unlisted_destination": (
        "weak_redirect_allowlist_prefix_only.py"
    ),
    "sec_test_session_profile_login_rotates_session_identifier": (
        "weak_login_keeps_pre_auth_session_id.py"
    ),
    "sec_test_session_profile_rejects_session_cookie_it_never_issued": (
        "weak_unissued_session_cookie_adopted.py"
    ),
    "sec_test_session_profile_read_resolves_account_from_session": (
        "weak_profile_read_selector_honored.py"
    ),
}

EXPECTED_CWES = {
    "sec_test_session_profile_update_requires_bound_csrf_token": [352],
    "sec_test_session_profile_logout_requires_bound_csrf_token": [352],
    "sec_test_session_profile_redirect_rejects_unlisted_destination": [601],
    "sec_test_session_profile_login_rotates_session_identifier": [384],
    "sec_test_session_profile_rejects_session_cookie_it_never_issued": [384],
    "sec_test_session_profile_read_resolves_account_from_session": [284],
}

POSITIVE_EVIDENCE_ONLY: list[str] = []
