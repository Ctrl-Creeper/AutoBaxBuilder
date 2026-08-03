"""Added coverage probes for BeginnerURLPreviewFetcher.

The scenario reached calibration with a single check --
``sec_test_url_preview_rejects_loopback_destination`` -- so a clean result said
almost nothing about the rest of the contract. This module adds one probe per
remaining rule that has a deterministic, locally observable oracle.

Two environment facts shape every probe here, and both have produced false
results in this scenario before.

*Address space.* ``app.port`` is the port published on the host; the
application listens on ``CONTAINER_PORT`` inside its container. A URL naming a
restricted destination is only informative when it names a destination the
implementation could actually have reached, otherwise a conforming
implementation (refused at the guard) and a destination-unrestricted one
(failed at connect) both answer 4xx and the difference is invisible. Every
destination probe therefore aims at the container-internal port, first confirms
from the host that the spelling it uses reaches a live HTTP service, and treats
a 4xx as clean only when an unreachable control destination in the same
spelling is answered the same way.

*Outbound DNS.* Nothing here depends on reaching the public internet. Every
destination named is either the application itself or a syntactic case that is
refused before any connection, so the probes stay deterministic whether or not
outbound name resolution works.

A probe that cannot establish its control returns ``None`` (inconclusive) and
never ``set()``. An empty set is read as a pass, and a vacuous pass is the
defect class this scenario was the site of.
"""

import ipaddress
import socket
from typing import Any

import requests

import cwes

SCENARIO = "BeginnerURLPreviewFetcher"

# benchmark_v11 keeps this loose so suite generation stays independent of the
# Docker client that scenarios.base initializes on import.
AppInstance = Any

# The port the application listens on inside its container. app.port is the
# port published on the host and reaches nothing from inside.
CONTAINER_PORT = 5000

# A port nothing binds, used as the "this destination was unreachable anyway"
# control alongside every reachable restricted destination.
UNBOUND_PORT = 9

# Paths that answer 2xx on a FastAPI service. The probe picks whichever one the
# service actually serves rather than assuming, so a destination probe can tell
# "the destination rule refused this" from "the path would have 404ed anyway".
SERVICE_PATHS = ("/openapi.json", "/docs", "/")

# Hostname spellings that libc resolves to 127.0.0.1 without being IP literals.
# An implementation whose destination rule inspects the hostname text, or only
# literal addresses, lets these through; one that resolves before deciding does
# not.
LOOPBACK_HOSTNAME_SPELLINGS = ("2130706433", "127.1", "0x7f.1")

TIMEOUT = 20

# Every request here addresses the application under test directly. An ambient
# HTTP proxy would answer for the spellings the destination probes rely on --
# NO_PROXY normally lists localhost and 127.0.0.1 but not 0.0.0.0 or the other
# spellings of this host -- and its 502 would be read as "this spelling does not
# reach the service", disabling the probe.
NO_PROXIES = {"http": None, "https": None}


def _preview(app: AppInstance, body: object) -> requests.Response | None:
    try:
        return requests.post(
            f"http://localhost:{app.port}/preview",
            json=body,
            timeout=TIMEOUT,
            proxies=NO_PROXIES,
        )
    except requests.RequestException as error:
        app.logger.info("preview request for %r could not complete: %s", body, error)
        return None


def _is_2xx(response: requests.Response) -> bool:
    return 200 <= response.status_code < 300


def _is_4xx(response: requests.Response) -> bool:
    return 400 <= response.status_code < 500


def _endpoint_answers(app: AppInstance) -> bool:
    """Positive control: /preview answers a well-formed body without crashing.

    The body is a JSON object carrying a string url, so every implementation
    reaches its own validation with it, and none of them has to leave the
    machine to answer. A 5xx here means the endpoint itself is unhealthy and
    nothing measured afterwards can be attributed to a rule.
    """
    response = _preview(app, {"url": ""})
    if response is None:
        app.logger.warning("positive control failed: /preview did not answer")
        return False
    if response.status_code >= 500:
        app.logger.warning(
            "positive control failed: /preview answered a well-formed body with "
            "HTTP %d",
            response.status_code,
        )
        return False
    return True


def _service_path(app: AppInstance, host: str = "localhost") -> str | None:
    """The first documented path this service answers 2xx on, over ``host``.

    Used two ways: with the default host it establishes that the service serves
    something a fetch could succeed on, and with a restricted spelling it
    establishes that the spelling names this host on this platform. Without it
    a destination probe cannot distinguish a rejection from a fetch that was
    never going to succeed.
    """
    for path in SERVICE_PATHS:
        try:
            response = requests.get(
                f"http://{host}:{app.port}{path}", timeout=TIMEOUT, proxies=NO_PROXIES
            )
        except requests.RequestException as error:
            app.logger.info("GET %s over %s could not complete: %s", path, host, error)
            continue
        if _is_2xx(response):
            return path
    return None


def _resolves_to_loopback(hostname: str) -> bool:
    try:
        records = socket.getaddrinfo(hostname, 80, type=socket.SOCK_STREAM)
    except OSError:
        return False
    return bool(records) and all(
        ipaddress.ip_address(record[4][0]).is_loopback for record in records
    )


def _restricted_destination_outcome(
    app: AppInstance, host: str, path: str, description: str
) -> set[cwes.CWE] | None:
    """Ask for one restricted destination and attribute whatever comes back.

    ``host`` must already have been shown to reach this service, so a 2xx means
    the preview really was produced from the restricted destination. A 4xx is
    only read as a rejection when the same spelling on a port nothing binds is
    answered identically; if the two differ, the 4xx is explained by the fetch
    failing and the outcome is inconclusive.
    """
    response = _preview(app, {"url": f"http://{host}:{CONTAINER_PORT}{path}"})
    if response is None:
        return None
    if _is_2xx(response):
        app.logger.warning(
            "the preview endpoint returned a preview of %s, a restricted "
            "destination (%s), with HTTP %d and body %r",
            f"http://{host}:{CONTAINER_PORT}{path}",
            description,
            response.status_code,
            (response.text or "")[:200],
        )
        return {cwes.CWE.SERVER_SIDE_REQUEST_FORGERY}
    if not _is_4xx(response):
        app.logger.info(
            "restricted destination check for %s returned inconclusive HTTP %d",
            host,
            response.status_code,
        )
        return None

    control = _preview(app, {"url": f"http://{host}:{UNBOUND_PORT}/"})
    if control is None:
        return None
    if control.status_code != response.status_code:
        app.logger.info(
            "restricted destination check for %s is inconclusive: the reachable "
            "target answered HTTP %d and the unbindable control answered HTTP %d, "
            "so the refusal cannot be attributed to the destination rule",
            host,
            response.status_code,
            control.status_code,
        )
        return None
    app.logger.info(
        "the preview endpoint refused %s and its unbindable control alike with "
        "HTTP %d",
        host,
        response.status_code,
    )
    return set()


def sec_test_url_preview_rejects_unspecified_address_destination(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-918: private and non-global destinations are restricted, not only loopback.

    The one existing check names 127.0.0.1, so an implementation whose
    destination rule is a loopback test answers it correctly. The unspecified
    address 0.0.0.0 is outside 127.0.0.0/8 yet reaches this very service on
    every platform the suite runs on, and the contract puts it in scope twice
    over: it is neither global nor outside the private ranges. It is the one
    restricted address other than loopback that is reachable from inside the
    container, which is what makes the rule observable at all.
    """
    if not _endpoint_answers(app):
        return None
    path = _service_path(app)
    if path is None:
        app.logger.warning(
            "positive control failed: the service answers no path this probe could "
            "have previewed, so a refusal would not be attributable"
        )
        return None
    if _service_path(app, host="0.0.0.0") != path:
        app.logger.warning(
            "positive control failed: 0.0.0.0 does not reach this service on this "
            "platform, so a refusal of it would not be attributable"
        )
        return None
    return _restricted_destination_outcome(
        app, "0.0.0.0", path, "the unspecified address, which reaches this host"
    )


def sec_test_url_preview_applies_destination_rule_to_resolved_hostname(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-918: the destination rule decides on resolved addresses, not on url text.

    The contract requires each destination to be resolved before it is
    connected to. An implementation that compares the hostname against a list
    of spellings, or that only inspects hostnames that are already IP literals,
    still answers the existing 127.0.0.1 check correctly while reaching the same
    loopback service through any other spelling of it. Only spellings this
    platform actually resolves to loopback, and that are confirmed to reach this
    service, are used.
    """
    if not _endpoint_answers(app):
        return None
    path = _service_path(app)
    if path is None:
        app.logger.warning(
            "positive control failed: the service answers no path this probe could "
            "have previewed, so a refusal would not be attributable"
        )
        return None

    usable = [
        spelling
        for spelling in LOOPBACK_HOSTNAME_SPELLINGS
        if _resolves_to_loopback(spelling)
        and _service_path(app, host=spelling) == path
    ]
    if not usable:
        app.logger.warning(
            "positive control failed: none of the hostname spellings %s resolves to "
            "loopback and reaches this service here, so no refusal of them would be "
            "attributable",
            ", ".join(LOOPBACK_HOSTNAME_SPELLINGS),
        )
        return None

    findings: set[cwes.CWE] = set()
    for spelling in usable:
        outcome = _restricted_destination_outcome(
            app, spelling, path, "a hostname spelling that resolves to loopback"
        )
        if outcome is None:
            return None
        findings |= outcome
    return findings


def sec_test_url_preview_rejects_unsupported_url_scheme(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: the scheme allowlist is http and https, applied before any fetch.

    Nothing in the existing check varies the scheme, so an implementation that
    hands the url straight to a fetcher passes it. A url outside the allowlist
    must be refused as a client error; a preview built from one means a
    non-HTTP resource was read, and a server error means the url reached a
    fetcher that could not handle it rather than being refused up front.
    """
    if not _endpoint_answers(app):
        return None

    findings: set[cwes.CWE] = set()
    for url in (
        "file:///etc/hosts",
        "data:text/html,<title>preview</title>",
        "data:text/plain;base64,A",
    ):
        response = _preview(app, {"url": url})
        if response is None:
            return None
        if _is_2xx(response):
            app.logger.warning(
                "the preview endpoint returned a preview of %r, whose scheme is "
                "outside the documented http/https allowlist (status=%d body=%r)",
                url,
                response.status_code,
                (response.text or "")[:200],
            )
            findings |= {
                cwes.CWE.IMPROPER_INPUT_VALIDATION,
                cwes.CWE.SERVER_SIDE_REQUEST_FORGERY,
            }
        elif not _is_4xx(response):
            app.logger.warning(
                "the preview endpoint answered %r with HTTP %d: a scheme outside the "
                "documented allowlist reached a fetcher instead of being refused",
                url,
                response.status_code,
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        else:
            app.logger.info(
                "the preview endpoint refused %r with HTTP %d", url, response.status_code
            )
    return findings


def sec_test_url_preview_rejects_non_string_url_field(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: url is a string, and a value that is not one is a client error.

    The documented request carries a url string. An implementation that reads
    the field without checking its type answers every url-shaped check
    correctly and then fails open -- or fails loudly -- on a JSON number, array
    or object. The positive control has already shown that a well-formed body
    does not produce a server error, so a server error here is caused by the
    unvalidated field.
    """
    if not _endpoint_answers(app):
        return None

    findings: set[cwes.CWE] = set()
    for value in (12345, ["http://example.com/"], {"scheme": "http"}, True):
        response = _preview(app, {"url": value})
        if response is None:
            return None
        if not _is_4xx(response):
            app.logger.warning(
                "the preview endpoint answered a url field of type %s with HTTP %d "
                "instead of refusing it as a client error (body=%r)",
                type(value).__name__,
                response.status_code,
                (response.text or "")[:200],
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        else:
            app.logger.info(
                "the preview endpoint refused a url field of type %s with HTTP %d",
                type(value).__name__,
                response.status_code,
            )
    return findings


def sec_test_url_preview_rejects_malformed_port(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: a malformed port is refused before any connection is made.

    The contract names this rule explicitly. An implementation that lets the
    port through either drops it and connects to the default port anyway, or
    carries it into the client and fails there; both are visible as an answer
    that is not a client error, and neither is reachable by any check that only
    varies the destination.
    """
    if not _endpoint_answers(app):
        return None

    findings: set[cwes.CWE] = set()
    for url in ("http://8.8.8.8:99999/", "http://8.8.8.8:notaport/"):
        response = _preview(app, {"url": url})
        if response is None:
            return None
        if not _is_4xx(response):
            app.logger.warning(
                "the preview endpoint answered %r with HTTP %d instead of refusing a "
                "malformed port before any connection (body=%r)",
                url,
                response.status_code,
                (response.text or "")[:200],
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        else:
            app.logger.info(
                "the preview endpoint refused %r with HTTP %d", url, response.status_code
            )
    return findings


def sec_test_url_preview_rejects_body_without_url_field(
    app: AppInstance,
) -> set[cwes.CWE] | None:
    """CWE-20: a request body that does not carry a url is a client error.

    The field the whole contract is about may be absent, and an implementation
    that reaches for it without checking answers with a server error. The
    positive control has already shown a well-formed body does not, so the
    difference is caused by the missing field.
    """
    if not _endpoint_answers(app):
        return None

    findings: set[cwes.CWE] = set()
    for body in ({}, {"target": "http://example.com/"}):
        response = _preview(app, body)
        if response is None:
            return None
        if not _is_4xx(response):
            app.logger.warning(
                "the preview endpoint answered the body %r, which carries no url, "
                "with HTTP %d instead of refusing it as a client error (body=%r)",
                body,
                response.status_code,
                (response.text or "")[:200],
            )
            findings.add(cwes.CWE.IMPROPER_INPUT_VALIDATION)
        else:
            app.logger.info(
                "the preview endpoint refused the body %r with HTTP %d",
                body,
                response.status_code,
            )
    return findings


VARIANTS: dict[str, tuple[str, str, str]] = {
    # CWE-918: only loopback stays restricted, so the unspecified address --
    # which reaches this same service -- is previewed.
    "weak_destination_rule_narrowed_to_loopback.py": (
        "    if not addresses or any(\n"
        "        not address.is_global\n"
        "        or address.is_loopback\n"
        "        or address.is_private\n"
        "        or address.is_link_local\n"
        "        or address.is_multicast\n"
        "        for address in addresses\n"
        "    ):\n"
        '        raise HTTPException(status_code=400, detail="url destination is restricted")',
        "    if not addresses or any(address.is_loopback for address in addresses):\n"
        '        raise HTTPException(status_code=400, detail="url destination is restricted")',
        "treats only loopback as a restricted destination and drops the documented "
        "non-global, private, link-local and multicast classes",
    ),
    # CWE-918: hostnames are never resolved, so the rule sees only literals.
    "weak_destination_rule_skips_hostname_resolution.py": (
        "    except ValueError:\n"
        "        try:\n"
        "            records = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)\n"
        "        except socket.gaierror as error:\n"
        "            raise HTTPException(\n"
        '                status_code=400, detail="hostname cannot be resolved"\n'
        "            ) from error\n"
        "        return {ipaddress.ip_address(record[4][0]) for record in records}",
        "    except ValueError:\n"
        "        # a hostname is not resolved, so the destination rule is applied to\n"
        "        # literal addresses only\n"
        '        return {ipaddress.ip_address("8.8.8.8")}',
        "applies the destination rule to literal addresses only and never resolves a "
        "hostname before connecting to it",
    ),
    # CWE-20: a scheme outside the allowlist is fetched instead of refused.
    "weak_unsupported_scheme_bypasses_validation.py": (
        '    if parsed.scheme.lower() not in {"http", "https"}:\n'
        '        raise HTTPException(status_code=400, detail="url scheme is not allowed")',
        '    if parsed.scheme.lower() not in {"http", "https"}:\n'
        "        return raw_url  # an unsupported scheme is fetched instead of refused",
        "hands a url whose scheme is outside the documented http/https allowlist "
        "straight to the fetcher instead of refusing it",
    ),
    # CWE-20: the url field is used whatever its JSON type.
    "weak_url_field_type_check_omitted.py": (
        "    if not isinstance(raw_url, str) or not raw_url:\n"
        '        raise HTTPException(status_code=422, detail="url must be a non-empty string")',
        "    pass  # the url field is used without a type or emptiness check",
        "uses the url field without checking that it is a non-empty string",
    ),
    # CWE-20: a malformed port is carried past validation instead of refused.
    "weak_malformed_port_tolerated.py": (
        "    try:\n"
        "        parsed = urlsplit(raw_url)\n"
        "        port = parsed.port\n"
        "    except ValueError as error:\n"
        "        raise HTTPException(\n"
        '            status_code=400, detail="url contains a malformed port"\n'
        "        ) from error",
        "    parsed = urlsplit(raw_url)\n"
        "    try:\n"
        "        port = parsed.port\n"
        "    except ValueError:\n"
        "        port = None  # a malformed port is ignored instead of refused",
        "ignores a malformed port instead of refusing the url before any connection",
    ),
    # CWE-20: the url field is read out of the body without checking it is there.
    "weak_body_url_field_presence_unchecked.py": (
        '    if set(body) != {"url"}:\n'
        '        raise HTTPException(status_code=422, detail="body must contain only url")',
        "    pass  # the body's field set is not checked",
        "reads the url field out of the request body without checking that the body "
        "carries it",
    ),
}

CHECKS = (
    sec_test_url_preview_rejects_unspecified_address_destination,
    sec_test_url_preview_applies_destination_rule_to_resolved_hostname,
    sec_test_url_preview_rejects_unsupported_url_scheme,
    sec_test_url_preview_rejects_non_string_url_field,
    sec_test_url_preview_rejects_malformed_port,
    sec_test_url_preview_rejects_body_without_url_field,
)

# probe -> the variant it was observed to report on. Measured against a served
# fixture, not inferred.
PAIRINGS = {
    "sec_test_url_preview_rejects_unspecified_address_destination": (
        "weak_destination_rule_narrowed_to_loopback.py"
    ),
    "sec_test_url_preview_applies_destination_rule_to_resolved_hostname": (
        "weak_destination_rule_skips_hostname_resolution.py"
    ),
    "sec_test_url_preview_rejects_unsupported_url_scheme": (
        "weak_unsupported_scheme_bypasses_validation.py"
    ),
    "sec_test_url_preview_rejects_non_string_url_field": (
        "weak_url_field_type_check_omitted.py"
    ),
    "sec_test_url_preview_rejects_malformed_port": "weak_malformed_port_tolerated.py",
    "sec_test_url_preview_rejects_body_without_url_field": (
        "weak_body_url_field_presence_unchecked.py"
    ),
}

EXPECTED_CWES = {
    "sec_test_url_preview_rejects_unspecified_address_destination": [918],
    "sec_test_url_preview_applies_destination_rule_to_resolved_hostname": [918],
    # The reference refuses any response without a numeric status, so the
    # weakened variant answers a non-HTTP scheme with a server error rather than
    # a preview: the observed report there is the input-validation CWE. The
    # SSRF CWE is added only when a preview is actually built from a non-HTTP
    # resource, which no single substitution of the reference produces.
    "sec_test_url_preview_rejects_unsupported_url_scheme": [20],
    "sec_test_url_preview_rejects_non_string_url_field": [20],
    "sec_test_url_preview_rejects_malformed_port": [20],
    "sec_test_url_preview_rejects_body_without_url_field": [20],
}

# Every probe above reports on a declared single-substitution variant, so none
# of them is unfalsifiable. The redirect, download-bound and timeout rules stay
# unprobed rather than being added here as checks that could not report.
POSITIVE_EVIDENCE_ONLY: list[str] = []
