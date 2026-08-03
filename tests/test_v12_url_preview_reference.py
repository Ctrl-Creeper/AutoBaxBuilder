import ast
import importlib.util
import sys
import unittest
from functools import lru_cache
from pathlib import Path
from email.message import Message

try:
    import pytest
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
except ModuleNotFoundError as error:
    raise unittest.SkipTest(
        "optional host-side FastAPI reference dependencies are not installed"
    ) from error


ROOT = Path(__file__).resolve().parents[1]
SECURE_PATH = (
    ROOT / "fixtures" / "reference_v1_1" / "BeginnerURLPreviewFetcher" / "secure.py"
)


def test_reference_uses_only_available_http_runtime_dependencies():
    tree = ast.parse(SECURE_PATH.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.partition(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )

    assert "requests" not in imported_roots


@lru_cache(maxsize=1)
def load_reference():
    module_name = "beginner_url_preview_fetcher_secure"
    spec = importlib.util.spec_from_file_location(module_name, SECURE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class StubResponse:
    def __init__(self, status, body=b"", headers=None):
        self.status = status
        self._body = body
        self._offset = 0
        self.headers = Message()
        for name, value in (headers or {}).items():
            self.headers[name] = value

    def getcode(self):
        return self.status

    def read(self, size=-1):
        if size < 0:
            size = len(self._body) - self._offset
        chunk = self._body[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    def close(self):
        pass


class StubOpener:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request.full_url, timeout))
        return next(self.responses)


@pytest.mark.parametrize(
    "target",
    [
        "file:///etc/hosts",
        "ftp://example.com/file",
        "http://localhost/",
        "http://localhost./",
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://169.254.1.1/",
        "http://[::1]/",
        "http://224.0.0.1/",
        "http://example.com:invalid/",
    ],
)
def test_restricted_or_malformed_targets_are_rejected_without_connecting(target):
    reference = load_reference()
    with pytest.raises(HTTPException) as raised:
        reference.validate_target(target)
    assert raised.value.status_code in {400, 422}


def test_preview_request_shape_is_closed_before_fetching(monkeypatch):
    reference = load_reference()
    client = TestClient(reference.app)

    assert client.post("/preview", data="not-json").status_code == 415
    assert client.post("/preview", json={}).status_code == 422
    assert (
        client.post(
            "/preview", json={"url": "http://127.0.0.1/", "extra": True}
        ).status_code
        == 422
    )


def test_public_success_shape_can_be_checked_with_a_local_fetch_stub(monkeypatch):
    reference = load_reference()
    expected = {
        "requestedUrl": "https://example.test/",
        "finalUrl": "https://example.test/",
        "title": "Fixture",
        "metadata": {"description": "Local fixture"},
        "redirectsFollowed": 0,
        "bytesDownloaded": 64,
    }
    monkeypatch.setattr(reference, "validate_target", lambda value: value)
    monkeypatch.setattr(reference, "fetch_preview", lambda value: expected)

    response = TestClient(reference.app).post(
        "/preview", json={"url": "https://example.test/"}
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_redirect_target_is_rechecked_before_the_next_request(monkeypatch):
    reference = load_reference()
    opener = StubOpener(
        [
            StubResponse(302, headers={"Location": "https://next.example/page"}),
            StubResponse(
                200,
                b"<title>Checked</title>",
                {"Content-Type": "text/html; charset=utf-8"},
            ),
        ]
    )
    checked = []
    monkeypatch.setattr(reference, "build_http_opener", lambda: opener)
    monkeypatch.setattr(
        reference, "validate_target", lambda target: checked.append(target) or target
    )

    result = reference.fetch_preview("https://start.example/")

    assert checked == ["https://start.example/", "https://next.example/page"]
    assert [url for url, _ in opener.calls] == checked
    assert all(
        0 < timeout <= reference.CONNECT_TIMEOUT_SECONDS for _, timeout in opener.calls
    )
    assert result["redirectsFollowed"] == 1
    assert result["title"] == "Checked"


def test_download_stops_at_the_documented_byte_limit(monkeypatch):
    reference = load_reference()
    opener = StubOpener([StubResponse(200, b"x" * (reference.MAX_DOWNLOAD_BYTES + 1))])
    monkeypatch.setattr(reference, "build_http_opener", lambda: opener)
    monkeypatch.setattr(reference, "validate_target", lambda target: target)

    with pytest.raises(HTTPException) as raised:
        reference.fetch_preview("https://large.example/")

    assert raised.value.status_code == 413


def test_declared_numeric_bounds_are_exact():
    reference = load_reference()
    assert reference.MAX_REDIRECTS == 3
    assert reference.MAX_DOWNLOAD_BYTES == 1_048_576
    assert reference.CONNECT_TIMEOUT_SECONDS == 2
    assert reference.TOTAL_TIMEOUT_SECONDS == 5
