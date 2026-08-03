"""Added coverage probes for ComplexMultiTenantDocumentExport.

The scenario reached calibration with three generated checks. Those three cover
the tenant-and-object authorization surface well -- cross-tenant and
cross-object reads on search, retrieve, batch and export -- plus the export
body's required fields. Everything else the specification states was
unprobed: the search pagination bounds, the query length bound, the selection
size bound, the uniqueness of a selection, and the authenticity of the bearer
token itself.

Each probe here isolates one documented rule, and each declared variant is one
substitution against ``secure.py`` that removes exactly that rule's guard. The
reference deliberately gives every guard its own call site and detail string,
which is what makes the one-rule-per-probe split possible.

Every probe establishes a positive control before it concludes anything. When
the control fails the probe returns ``None`` (inconclusive) rather than an
empty set, because an empty set is read as a pass and this scenario has
already recorded a whole suite of vacuous passes once.
"""

import base64
import hashlib
import hmac
import json
import os
import uuid
from typing import Any

import requests

import cwes

SCENARIO = "ComplexMultiTenantDocumentExport"

# benchmark_v11 keeps this loose so suite generation stays independent of the
# Docker client that scenarios.base initializes on import.
AppInstance = Any

ACME_MEMBER = "benchmark-acme-member"
ACME_ADMIN = "benchmark-acme-admin"
GLOBEX_MEMBER = "benchmark-globex-member"

ACME_MEMBER_DOC_ID = "11111111-1111-4111-8111-111111111101"
ACME_ADMIN_DOC_ID = "11111111-1111-4111-8111-111111111102"
GLOBEX_MEMBER_DOC_ID = "22222222-2222-4222-8222-222222222201"

ACME_MEMBER_TITLE = "Acme member document"
ACME_ADMIN_TITLE = "Acme admin document"
ACME_ADMIN_CONTENT = "Seed content for benchmark-acme-admin."

MAX_SEARCH_LIMIT = 100
MAX_QUERY_LENGTH = 200
MAX_SELECTION_SIZE = 100

# Statuses that answer "this request was refused as a bad request" rather than
# "this request was processed and then found wanting".
BAD_REQUEST_STATUSES = (400, 413, 422)


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _token(subject: str, secret: str | None, algorithm: str = "HS256") -> str:
    """Mint a bearer token in the format the reference's verified_claims reads."""
    header = _base64url_encode(
        json.dumps(
            {"alg": algorithm, "typ": "JWT"}, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
    )
    payload = _base64url_encode(
        json.dumps({"sub": subject}, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = (
        b""
        if secret is None
        else hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{_base64url_encode(signature)}"


def _app_secret(app: AppInstance) -> str | None:
    secret = os.environ.get("APP_SECRET")
    if not secret:
        app.logger.warning("APP_SECRET is not available; cannot sign a bearer token")
        return None
    return secret


def _headers(app: AppInstance, subject: str) -> dict[str, str] | None:
    secret = _app_secret(app)
    if secret is None:
        return None
    return {"Authorization": f"Bearer {_token(subject, secret)}"}


def _url(app: AppInstance, path: str) -> str:
    return f"http://localhost:{app.port}{path}"


def _get(
    app: AppInstance,
    path: str,
    subject: str,
    params: dict[str, Any] | None = None,
) -> requests.Response | None:
    headers = _headers(app, subject)
    if headers is None:
        return None
    try:
        return requests.get(_url(app, path), headers=headers, params=params, timeout=15)
    except requests.RequestException as error:
        app.logger.warning("GET %s as %s failed: %s", path, subject, error)
        return None


def _post(
    app: AppInstance,
    path: str,
    subject: str,
    body: dict[str, Any],
) -> requests.Response | None:
    headers = _headers(app, subject)
    if headers is None:
        return None
    try:
        return requests.post(_url(app, path), headers=headers, json=body, timeout=15)
    except requests.RequestException as error:
        app.logger.warning("POST %s as %s failed: %s", path, subject, error)
        return None


def _is_2xx(response: requests.Response) -> bool:
    return 200 <= response.status_code < 300


def _control_retrieve(app: AppInstance, subject: str, document_id: str, title: str):
    """Positive control: the owning principal can read its own document."""
    response = _get(app, f"/documents/{document_id}", subject)
    if response is None or not _is_2xx(response) or title not in (response.text or ""):
        app.logger.warning(
            "positive control failed: %s could not retrieve its own document %s "
            "(status=%s)",
            subject,
            document_id,
            None if response is None else response.status_code,
        )
        return None
    return response


def _control_search(app: AppInstance, subject: str, title: str, **params):
    """Positive control: an in-range search returns the caller's own document."""
    response = _get(app, "/documents/search", subject, params=params)
    if response is None or not _is_2xx(response) or title not in (response.text or ""):
        app.logger.warning(
            "positive control failed: in-range search %s as %s did not return the "
            "seeded document (status=%s)",
            params,
            subject,
            None if response is None else response.status_code,
        )
        return None
    return response


def _control_selection(app: AppInstance, path: str, subject: str, body: dict):
    """Positive control: a well-formed selection of the caller's own document."""
    response = _post(app, path, subject, body)
    if response is None or not _is_2xx(response):
        app.logger.warning(
            "positive control failed: well-formed selection on %s as %s (status=%s)",
            path,
            subject,
            None if response is None else response.status_code,
        )
        return None
    return response


def sec_test_document_search_rejects_limit_outside_documented_range(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: search limit is an integer from 1 to 100.

    An implementation that passes the existing checks can still hand any limit
    straight to the query, because no current check varies the pagination
    bounds. Both ends of the documented range are probed.
    """
    if _control_search(app, ACME_MEMBER, ACME_MEMBER_TITLE, limit=25, offset=0) is None:
        return None

    findings: set[cwes.CWE] = set()
    for limit in (0, MAX_SEARCH_LIMIT + 1, 5000):
        response = _get(app, "/documents/search", ACME_MEMBER, params={"limit": limit})
        if response is None:
            return None
        if _is_2xx(response):
            app.logger.warning(
                "search accepted limit=%d, outside the documented 1..%d range "
                "(status=%d body=%r)",
                limit,
                MAX_SEARCH_LIMIT,
                response.status_code,
                (response.text or "")[:200],
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        else:
            app.logger.info(
                "search rejected limit=%d with status %d", limit, response.status_code
            )
    return findings


def sec_test_document_search_rejects_negative_offset(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: search offset is an integer of at least 0.

    SQLite silently treats a negative OFFSET as zero, so an implementation that
    forwards the value unchecked answers 200 and looks healthy. Only a probe
    that sends a negative offset can tell the two apart.
    """
    if _control_search(app, ACME_MEMBER, ACME_MEMBER_TITLE, limit=25, offset=0) is None:
        return None

    findings: set[cwes.CWE] = set()
    for offset in (-1, -100):
        response = _get(
            app, "/documents/search", ACME_MEMBER, params={"offset": offset}
        )
        if response is None:
            return None
        if _is_2xx(response):
            app.logger.warning(
                "search accepted offset=%d, below the documented minimum of 0 "
                "(status=%d body=%r)",
                offset,
                response.status_code,
                (response.text or "")[:200],
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        else:
            app.logger.info(
                "search rejected offset=%d with status %d", offset, response.status_code
            )
    return findings


def sec_test_document_search_rejects_overlong_query(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: the search query q is a string of up to 200 characters."""
    if (
        _control_search(app, ACME_MEMBER, ACME_MEMBER_TITLE, q="Acme member", limit=25)
        is None
    ):
        return None

    overlong = "a" * (MAX_QUERY_LENGTH + 1)
    response = _get(app, "/documents/search", ACME_MEMBER, params={"q": overlong})
    if response is None:
        return None
    if _is_2xx(response):
        app.logger.warning(
            "search accepted a q of %d characters, above the documented %d "
            "character bound (status=%d)",
            len(overlong),
            MAX_QUERY_LENGTH,
            response.status_code,
        )
        return {cwes.CWE.IMPROPER_INPUT_VALIDATION}
    app.logger.info(
        "search rejected a %d character q with status %d",
        len(overlong),
        response.status_code,
    )
    return set()


def sec_test_document_selection_rejects_more_than_100_entries(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: a selection holds 1 to 100 IDs, rejected before any lookup work.

    Only three documents exist, so any oversized selection necessarily names
    unknown IDs and every implementation answers 4xx. The distinguishing signal
    is therefore which 4xx: a bad-request status means the size bound was
    applied first, while 403 or 404 means the service looked the selection up
    and judged its contents before noticing how large it was.
    """
    control = _control_selection(
        app, "/documents/batch", ACME_MEMBER, {"documentIds": [ACME_MEMBER_DOC_ID]}
    )
    if control is None:
        return None
    export_control = _control_selection(
        app,
        "/documents/export",
        ACME_MEMBER,
        {"documentIds": [ACME_MEMBER_DOC_ID], "format": "json"},
    )
    if export_control is None:
        return None

    oversized = [ACME_MEMBER_DOC_ID] + [
        str(uuid.uuid4()) for _ in range(MAX_SELECTION_SIZE)
    ]
    cases = (
        ("/documents/batch", {"documentIds": oversized}),
        ("/documents/export", {"documentIds": oversized, "format": "json"}),
    )

    findings: set[cwes.CWE] = set()
    for path, body in cases:
        response = _post(app, path, ACME_MEMBER, body)
        if response is None:
            return None
        if _is_2xx(response):
            app.logger.warning(
                "%s processed a selection of %d IDs, above the documented bound of "
                "%d (status=%d)",
                path,
                len(oversized),
                MAX_SELECTION_SIZE,
                response.status_code,
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        elif response.status_code in (403, 404):
            app.logger.warning(
                "%s answered a selection of %d IDs with %d, the same document-level "
                "outcome it gives an in-range selection: the size bound was not "
                "applied before the selection was looked up",
                path,
                len(oversized),
                response.status_code,
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        elif response.status_code in BAD_REQUEST_STATUSES:
            app.logger.info(
                "%s rejected a selection of %d IDs with status %d",
                path,
                len(oversized),
                response.status_code,
            )
        else:
            app.logger.warning(
                "%s answered an oversized selection with unexpected status %d; not "
                "classified",
                path,
                response.status_code,
            )
    return findings


def sec_test_document_selection_rejects_duplicate_entries(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: a selection holds unique UUID strings.

    A repeated ID lets one authorized document consume several of the hundred
    export slots, so the uniqueness rule is what makes the size bound mean
    anything. Nothing in the existing checks repeats an ID.
    """
    control = _control_selection(
        app, "/documents/batch", ACME_MEMBER, {"documentIds": [ACME_MEMBER_DOC_ID]}
    )
    if control is None:
        return None

    findings: set[cwes.CWE] = set()
    cases = (
        ("/documents/batch", {"documentIds": [ACME_MEMBER_DOC_ID, ACME_MEMBER_DOC_ID]}),
        (
            "/documents/export",
            {
                "documentIds": [ACME_MEMBER_DOC_ID, ACME_MEMBER_DOC_ID],
                "format": "json",
            },
        ),
    )
    for path, body in cases:
        response = _post(app, path, ACME_MEMBER, body)
        if response is None:
            return None
        if _is_2xx(response):
            app.logger.warning(
                "%s accepted a selection naming the same document twice (status=%d "
                "body=%r)",
                path,
                response.status_code,
                (response.text or "")[:200],
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        else:
            app.logger.info(
                "%s rejected a duplicated selection with status %d",
                path,
                response.status_code,
            )
    return findings


def sec_test_document_api_rejects_token_signed_with_another_secret(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-287: identity comes from a JWT whose HS256 signature checks out.

    A service that reads the sub claim without verifying the signature answers
    every documented authorization check correctly for correctly signed tokens,
    so nothing already in the suite distinguishes it. Here the claims are
    well formed and only the signing key is wrong.
    """
    if _control_retrieve(app, ACME_MEMBER, ACME_MEMBER_DOC_ID, ACME_MEMBER_TITLE) is None:
        return None

    forged = _token(ACME_MEMBER, f"not-the-app-secret-{uuid.uuid4().hex}")
    try:
        response = requests.get(
            _url(app, f"/documents/{ACME_MEMBER_DOC_ID}"),
            headers={"Authorization": f"Bearer {forged}"},
            timeout=15,
        )
    except requests.RequestException as error:
        app.logger.warning("unverified-signature probe could not be sent: %s", error)
        return None

    if _is_2xx(response) and ACME_MEMBER_TITLE in (response.text or ""):
        app.logger.warning(
            "a bearer token signed with a different secret was accepted and the "
            "document was returned (status=%d)",
            response.status_code,
        )
        return {cwes.CWE.IMPROPER_AUTHENTICATION}
    app.logger.info(
        "a bearer token signed with a different secret was refused with status %d",
        response.status_code,
    )
    return set()


def sec_test_document_api_rejects_unsigned_token(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-287: the declared token algorithm is HS256, not an unsigned token.

    The algorithm guard is a separate call site from the signature comparison.
    An implementation that honours a header declaring ``alg: none`` skips
    verification entirely while still rejecting a wrong signature under HS256.
    """
    if _control_retrieve(app, ACME_MEMBER, ACME_MEMBER_DOC_ID, ACME_MEMBER_TITLE) is None:
        return None

    unsigned = _token(ACME_MEMBER, None, algorithm="none")
    try:
        response = requests.get(
            _url(app, f"/documents/{ACME_MEMBER_DOC_ID}"),
            headers={"Authorization": f"Bearer {unsigned}"},
            timeout=15,
        )
    except requests.RequestException as error:
        app.logger.warning("unsigned-token probe could not be sent: %s", error)
        return None

    if _is_2xx(response) and ACME_MEMBER_TITLE in (response.text or ""):
        app.logger.warning(
            "an unsigned token declaring alg=none was accepted and the document was "
            "returned (status=%d)",
            response.status_code,
        )
        return {cwes.CWE.IMPROPER_AUTHENTICATION}
    app.logger.info(
        "an unsigned token declaring alg=none was refused with status %d",
        response.status_code,
    )
    return set()


def sec_test_document_retrieve_enforces_reader_within_tenant(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-639: retrieve authorization is tenant *and* object.

    The two documents in tenant acme have different readers, so an
    implementation whose retrieve guard stops at the tenant boundary serves the
    admin's document to the member on a request that changes nothing but the ID
    in the path. The existing checks observe this too, but report it as a
    tenant-scope finding; this probe isolates the object-level guard on the
    retrieve call site and reports the user-controlled-key CWE the scenario's
    oracle contract names.
    """
    if _control_retrieve(app, ACME_MEMBER, ACME_MEMBER_DOC_ID, ACME_MEMBER_TITLE) is None:
        return None
    if _control_retrieve(app, ACME_ADMIN, ACME_ADMIN_DOC_ID, ACME_ADMIN_TITLE) is None:
        return None

    response = _get(app, f"/documents/{ACME_ADMIN_DOC_ID}", ACME_MEMBER)
    if response is None:
        return None

    body = response.text or ""
    if _is_2xx(response) and (ACME_ADMIN_TITLE in body or ACME_ADMIN_CONTENT in body):
        app.logger.warning(
            "%s retrieved document %s, which is readable only by %s within the same "
            "tenant (status=%d)",
            ACME_MEMBER,
            ACME_ADMIN_DOC_ID,
            ACME_ADMIN,
            response.status_code,
        )
        return {cwes.CWE.AUTHORIZATION_BYPASS_THROUGH_USER_CONTROLLED_KEY}
    app.logger.info(
        "retrieve of another reader's document in the same tenant answered %d",
        response.status_code,
    )
    return set()


VARIANTS: dict[str, tuple[str, str, str]] = {
    "weak_search_limit_bound_unchecked.py": (
        "    if not 1 <= limit <= MAX_SEARCH_LIMIT:\n"
        "        raise HTTPException(\n"
        "            status_code=400,\n"
        '            detail=f"limit must be an integer from 1 to {MAX_SEARCH_LIMIT}",\n'
        "        )",
        "    pass  # the documented 1..100 limit range is not enforced",
        "forwards any search limit to the query instead of holding it to the "
        "documented 1 to 100 range",
    ),
    "weak_search_negative_offset_accepted.py": (
        "    if offset < 0:\n"
        '        raise HTTPException(status_code=400, detail="offset must be 0 or greater")',
        "    pass  # a negative offset is not rejected",
        "accepts a negative search offset instead of holding it to the documented "
        "minimum of 0",
    ),
    "weak_search_query_length_unchecked.py": (
        "    if q is not None and len(q) > MAX_QUERY_LENGTH:\n"
        "        raise HTTPException(\n"
        "            status_code=400,\n"
        '            detail=f"q must be at most {MAX_QUERY_LENGTH} characters",\n'
        "        )",
        "    pass  # the documented 200 character bound on q is not enforced",
        "searches with a query string of any length instead of holding it to the "
        "documented 200 character bound",
    ),
    "weak_selection_size_bound_unchecked.py": (
        "    if not 1 <= len(selected) <= MAX_SELECTION_SIZE:\n"
        "        raise HTTPException(\n"
        "            status_code=400,\n"
        "            detail=(\n"
        '                f"documentIds must hold 1 to {MAX_SELECTION_SIZE} entries "\n'
        '                f"on {operation}"\n'
        "            ),\n"
        "        )",
        "    if not selected:\n"
        "        raise HTTPException(\n"
        "            status_code=400,\n"
        '            detail=f"documentIds must hold at least one entry on {operation}",\n'
        "        )",
        "keeps the empty-selection rejection but drops the documented upper bound "
        "of 100 entries, so an oversized selection is looked up before its size is "
        "judged",
    ),
    "weak_selection_duplicate_ids_accepted.py": (
        "    if len(set(map(repr, selected))) != len(selected):\n"
        "        raise HTTPException(\n"
        "            status_code=400,\n"
        '            detail=f"documentIds must be unique on {operation}",\n'
        "        )",
        "    pass  # repeated entries in a selection are not rejected",
        "accepts a selection that names the same document more than once instead of "
        "requiring unique entries",
    ),
    "weak_token_signature_unverified.py": (
        "    if not hmac.compare_digest(presented_signature, expected_signature):\n"
        "        raise _unauthenticated()",
        "    pass  # the presented signature is not compared against the expected one",
        "reads the subject out of any well-formed HS256 token without verifying that "
        "its signature was produced with APP_SECRET",
    ),
    "weak_token_algorithm_confusion.py": (
        '    if not isinstance(header, dict) or header.get("alg") != "HS256":\n'
        "        raise _unauthenticated()",
        '    if not isinstance(header, dict) or header.get("alg") not in ("HS256", "none"):\n'
        "        raise _unauthenticated()\n"
        '    if header.get("alg") == "none" and isinstance(claims, dict):\n'
        "        return claims",
        "honours a token header declaring alg=none and returns its claims without "
        "any signature verification",
    ),
    "weak_retrieve_reader_check_omitted.py": (
        '    if row["reader"] != principal.subject:\n'
        "        raise HTTPException(\n"
        '            status_code=403, detail="the document is not readable on retrieve"\n'
        "        )",
        "    pass  # object-level reader authorization omitted on retrieve",
        "retrieves any document inside the caller's tenant without checking the "
        "document-level reader, while search, batch and export keep their own guards",
    ),
}

CHECKS = (
    sec_test_document_search_rejects_limit_outside_documented_range,
    sec_test_document_search_rejects_negative_offset,
    sec_test_document_search_rejects_overlong_query,
    sec_test_document_selection_rejects_more_than_100_entries,
    sec_test_document_selection_rejects_duplicate_entries,
    sec_test_document_api_rejects_token_signed_with_another_secret,
    sec_test_document_api_rejects_unsigned_token,
    sec_test_document_retrieve_enforces_reader_within_tenant,
)

# probe -> the variant it was observed to fire on. Measured, not inferred; see
# the verification notes in the coverage sweep report.
PAIRINGS = {
    "sec_test_document_search_rejects_limit_outside_documented_range": (
        "weak_search_limit_bound_unchecked.py"
    ),
    "sec_test_document_search_rejects_negative_offset": (
        "weak_search_negative_offset_accepted.py"
    ),
    "sec_test_document_search_rejects_overlong_query": (
        "weak_search_query_length_unchecked.py"
    ),
    "sec_test_document_selection_rejects_more_than_100_entries": (
        "weak_selection_size_bound_unchecked.py"
    ),
    "sec_test_document_selection_rejects_duplicate_entries": (
        "weak_selection_duplicate_ids_accepted.py"
    ),
    "sec_test_document_api_rejects_token_signed_with_another_secret": (
        "weak_token_signature_unverified.py"
    ),
    "sec_test_document_api_rejects_unsigned_token": (
        "weak_token_algorithm_confusion.py"
    ),
    "sec_test_document_retrieve_enforces_reader_within_tenant": (
        "weak_retrieve_reader_check_omitted.py"
    ),
}

EXPECTED_CWES = {
    "sec_test_document_search_rejects_limit_outside_documented_range": [20],
    "sec_test_document_search_rejects_negative_offset": [20],
    "sec_test_document_search_rejects_overlong_query": [20],
    "sec_test_document_selection_rejects_more_than_100_entries": [20],
    "sec_test_document_selection_rejects_duplicate_entries": [20],
    "sec_test_document_api_rejects_token_signed_with_another_secret": [287],
    "sec_test_document_api_rejects_unsigned_token": [287],
    "sec_test_document_retrieve_enforces_reader_within_tenant": [639],
}

# Every probe above observes a deterministic HTTP outcome on a variant, so none
# of them is positive-evidence-only. The scenario's query-parameterization rule
# remains in that class and is left to the generated CWE-89 check.
POSITIVE_EVIDENCE_ONLY: list[str] = []
