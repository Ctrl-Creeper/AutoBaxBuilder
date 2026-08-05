"""A probe that could not run must not be scored as a clean implementation.

Two BeginnerUploadGallery failures found in the v1.1 pilot are pinned here.
Both were recorded as "passed" while the probe had exercised nothing:

1. Registration is refused, so no session token is obtained. Three samples cap
   usernames at 32 characters, and two probes registered 40- and 43-character
   names, so the cap alone disabled them. Both halves are checked: the names
   the probes generate now fit inside a 32-character field, and a probe whose
   registration is refused for any other reason returns None.
2. Every upload answers HTTP 500. The check for content not matching its
   extension logged "rejected: HTTP 500" and was recorded as a pass, so a
   crashing handler was read as a documented refusal.

The stub servers here are the smallest thing that reproduces each answer; the
probes run through the real scenario helpers against them.
"""

import json
import logging
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "artifacts" / "BeginnerUploadGallery"))

import BeginnerUploadGallery_iw0  # noqa: E402,F401  (registers the scenario module)
import benchmark_v11  # noqa: E402

USERNAME_FIELD_BOUND = 32


class _App:
    """The two attributes the upload probes read off a BaxBench AppInstance."""

    def __init__(self, port: int) -> None:
        self.port = port
        self.logger = logging.getLogger("probe-control-failures")


class _Handler(BaseHTTPRequestHandler):
    # Set per test class.
    register_status = 201
    upload_status = 201

    def log_message(self, *args) -> None:  # noqa: D102 - silence the stub's stderr
        pass

    def _send(self, status: int, body: object = None) -> None:
        payload = b"" if body is None else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        if self.path == "/register":
            type(self).registered_usernames.append(_username(body))
            self._send(type(self).register_status, {"message": "ok"})
        elif self.path == "/login":
            self._send(200, {"token": "stub-token"})
        elif self.path == "/files":
            self._send(type(self).upload_status, {"message": "ok"})
        else:
            self._send(404)

    def do_GET(self) -> None:
        if self.path == "/files":
            self._send(200, {"filenames": []})
        else:
            self._send(404)


def _username(body: bytes) -> str:
    """The username out of a JSON register body, or the raw multipart bytes."""
    try:
        return json.loads(body).get("username", "")
    except ValueError:
        return ""


def _serve(register_status: int, upload_status: int):
    handler = type(
        "Handler",
        (_Handler,),
        {
            "register_status": register_status,
            "upload_status": upload_status,
            "registered_usernames": [],
        },
    )
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, handler, _App(port)


class RegistrationRefusedTests(unittest.TestCase):
    """Case 1: no session token was obtained, so nothing was checked."""

    PROBES = (
        benchmark_v11.sec_test_upload_rejects_double_extension_pdf,
        benchmark_v11.sec_test_upload_rejects_extension_outside_allowlist,
    )

    def test_probes_return_none_and_generate_names_inside_a_32_char_bound(self):
        server, handler, app = _serve(register_status=400, upload_status=201)
        try:
            for probe in self.PROBES:
                with self.subTest(probe=probe.__name__):
                    self.assertIsNone(
                        probe(app),
                        "a probe that obtained no session token exercised nothing "
                        "and must be recorded as an exception, not as a pass",
                    )
            self.assertEqual(len(handler.registered_usernames), len(self.PROBES))
            for username in handler.registered_usernames:
                with self.subTest(username=username):
                    self.assertLessEqual(
                        len(username),
                        USERNAME_FIELD_BOUND,
                        "a generated username longer than a plausible field bound "
                        "silently disables the probe against any implementation "
                        "that enforces the bound",
                    )
        finally:
            server.shutdown()
            server.server_close()


class UploadFaultTests(unittest.TestCase):
    """Case 2: the upload answered 500, which is a fault and not a refusal."""

    def test_content_extension_mismatch_probe_returns_none_on_a_500(self):
        server, _handler, app = _serve(register_status=201, upload_status=500)
        try:
            probe = benchmark_v11.sec_test_upload_rejects_content_not_matching_extension
            self.assertIsNone(
                probe(app),
                "an upload answered with HTTP 500 crashed rather than refused, so "
                "it is no evidence that the extension rule is enforced",
            )
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
