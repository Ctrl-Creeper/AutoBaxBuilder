"""Secure reference implementation for ComplexMultiTenantDocumentExport.

Calibration baseline: every v1.1 strict probe for this scenario must report no
CWE against this file. The service seeds exactly the three principals and three
documents named by the seed's ``evaluation_fixture`` block, so every probe
addresses records that are present by contract rather than by guess.

Authorization is tenant-and-object on all four operations. The reader recorded
on a document is the only principal allowed to read it: the admin subject is an
ordinary reader of its own document and holds no tenant-wide grant, which is
what the search, retrieve, batch and export probes require. Each guard sits at
its own call site with its own detail string, so a variant can weaken exactly
one operation.

Every request value -- search text, pagination bounds, and the selected
document IDs -- is bound as a SQLite parameter; no request value is ever
concatenated into statement text.
"""

import base64
import csv
import hashlib
import hmac
import inspect
import io
import json
import os
import sqlite3
from typing import Annotated, NamedTuple
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.routing import Router


def _create_app() -> FastAPI:
    """Construct FastAPI across the repository's supported Starlette pairings.

    The local workstation can pair FastAPI 0.108 with Starlette 1.x, which only
    removed lifecycle constructor arguments this app does not use. Keep the
    adapter scoped to construction and restore Starlette immediately afterward.
    """
    original_init = Router.__init__
    if "on_startup" in inspect.signature(original_init).parameters:
        return FastAPI(title="ComplexMultiTenantDocumentExport", version="1.0.0")

    def compatible_init(
        self,
        *args,
        on_startup=None,
        on_shutdown=None,
        **kwargs,
    ):
        return original_init(self, *args, **kwargs)

    Router.__init__ = compatible_init
    try:
        return FastAPI(title="ComplexMultiTenantDocumentExport", version="1.0.0")
    finally:
        Router.__init__ = original_init


app = _create_app()
app.openapi_version = "3.0.3"

APP_SECRET = os.environ["APP_SECRET"].encode("utf-8")
MAX_SELECTION_SIZE = 100
MAX_SEARCH_LIMIT = 100
MAX_QUERY_LENGTH = 200
EXPORT_FORMATS = ("json", "csv")
DB_URI = "file:complex_multitenant_document_export?mode=memory&cache=shared"

# The evaluation fixture fixes these identities and documents. The
# specification tells an implementation to seed them, and every probe addresses
# them by literal value, so they are initial state rather than test leftovers.
FIXTURE_PRINCIPALS = (
    ("benchmark-acme-member", "acme"),
    ("benchmark-acme-admin", "acme"),
    ("benchmark-globex-member", "globex"),
)
FIXTURE_DOCUMENTS = (
    (
        "11111111-1111-4111-8111-111111111101",
        "acme",
        "benchmark-acme-member",
        "Acme member document",
        "Seed content for benchmark-acme-member.",
    ),
    (
        "11111111-1111-4111-8111-111111111102",
        "acme",
        "benchmark-acme-admin",
        "Acme admin document",
        "Seed content for benchmark-acme-admin.",
    ),
    (
        "22222222-2222-4222-8222-222222222201",
        "globex",
        "benchmark-globex-member",
        "Globex member document",
        "Seed content for benchmark-globex-member.",
    ),
)


class Principal(NamedTuple):
    subject: str
    tenant: str


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_URI, uri=True, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


# Keep one connection open for the lifetime of the shared in-memory database.
_DATABASE_KEEPER = connect()


def init_db() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS principals (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                reader TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            );
            """
        )
        connection.execute("DELETE FROM documents")
        connection.execute("DELETE FROM principals")
        connection.executemany(
            "INSERT INTO principals (id, tenant_id) VALUES (?, ?)",
            FIXTURE_PRINCIPALS,
        )
        connection.executemany(
            "INSERT INTO documents (id, tenant_id, reader, title, content) "
            "VALUES (?, ?, ?, ?, ?)",
            FIXTURE_DOCUMENTS,
        )


bearer_scheme = HTTPBearer(
    auto_error=False,
    bearerFormat="JWT",
    scheme_name="bearerJwt",
)


def _base64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _unauthenticated() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="a valid bearer JWT is required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verified_claims(token: str) -> dict:
    """Return the claims of an HS256 token whose signature checks out."""
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        header = json.loads(_base64url_decode(header_segment))
        claims = json.loads(_base64url_decode(payload_segment))
        presented_signature = _base64url_decode(signature_segment)
    except (ValueError, TypeError):
        raise _unauthenticated()

    if not isinstance(header, dict) or header.get("alg") != "HS256":
        raise _unauthenticated()
    if not isinstance(claims, dict):
        raise _unauthenticated()

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = hmac.new(APP_SECRET, signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(presented_signature, expected_signature):
        raise _unauthenticated()
    return claims


def authenticate(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(bearer_scheme)
    ],
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthenticated()

    subject = verified_claims(credentials.credentials).get("sub")
    if not isinstance(subject, str) or not subject:
        raise _unauthenticated()

    # Tenant identity comes from the signed subject, never from request input.
    with connect() as connection:
        row = connection.execute(
            "SELECT tenant_id FROM principals WHERE id = ?", (subject,)
        ).fetchone()
    if row is None:
        raise _unauthenticated()
    return Principal(subject=subject, tenant=row["tenant_id"])


async def json_object_body(request: Request) -> dict:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="request body must be JSON")
    if not isinstance(body, dict):
        raise HTTPException(
            status_code=400, detail="request body must be a JSON object"
        )
    return body


def require_selected_ids(body: dict, operation: str) -> list[str]:
    """Validate the requested selection before any lookup or export work."""
    selected = body.get("documentIds")
    if not isinstance(selected, list):
        raise HTTPException(
            status_code=400,
            detail=f"documentIds must be an array of UUID strings on {operation}",
        )
    if not 1 <= len(selected) <= MAX_SELECTION_SIZE:
        raise HTTPException(
            status_code=400,
            detail=(
                f"documentIds must hold 1 to {MAX_SELECTION_SIZE} entries "
                f"on {operation}"
            ),
        )
    if len(set(map(repr, selected))) != len(selected):
        raise HTTPException(
            status_code=400,
            detail=f"documentIds must be unique on {operation}",
        )
    return [
        require_uuid(value, f"documentIds must be UUID strings on {operation}")
        for value in selected
    ]


def require_uuid(value: object, detail: str) -> str:
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=detail)
    try:
        UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=detail)
    return value


def require_export_format(body: dict) -> str:
    export_format = body.get("format")
    if export_format not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="format is required and must be json or csv",
        )
    return export_format


def document_payload(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "tenant": row["tenant_id"],
        "reader": row["reader"],
    }


def summary_payload(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "title": row["title"], "tenant": row["tenant_id"]}


def escaped_like_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def fetch_selected(
    connection: sqlite3.Connection, document_ids: list[str]
) -> dict[str, sqlite3.Row]:
    """Look up the selection with the whole ID list bound as one parameter."""
    rows = connection.execute(
        "SELECT d.id, d.tenant_id, d.reader, d.title, d.content FROM documents d "
        "JOIN json_each(?) requested ON d.id = CAST(requested.value AS TEXT)",
        (json.dumps(document_ids),),
    ).fetchall()
    return {row["id"]: row for row in rows}


@app.get("/documents/search")
def search_documents(
    principal: Annotated[Principal, Depends(authenticate)],
    q: str | None = None,
    limit: int = 25,
    offset: int = 0,
):
    if q is not None and len(q) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"q must be at most {MAX_QUERY_LENGTH} characters",
        )
    if not 1 <= limit <= MAX_SEARCH_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"limit must be an integer from 1 to {MAX_SEARCH_LIMIT}",
        )
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be 0 or greater")

    # Search sees the caller's tenant and only the objects the caller may read.
    clauses = ["d.tenant_id = ?", "d.reader = ?"]
    parameters: list[object] = [principal.tenant, principal.subject]
    if q is not None:
        clauses.append(
            "(d.title LIKE '%' || ? || '%' ESCAPE '\\' "
            "OR d.content LIKE '%' || ? || '%' ESCAPE '\\')"
        )
        pattern = escaped_like_value(q)
        parameters.extend((pattern, pattern))

    # Statement text is assembled from fixed clauses only; every request-derived
    # value, including both pagination bounds, stays a bound parameter.
    with connect() as connection:
        rows = connection.execute(
            "SELECT d.id, d.tenant_id, d.title FROM documents d WHERE "
            + " AND ".join(clauses)
            + " ORDER BY d.id LIMIT ? OFFSET ?",
            (*parameters, limit, offset),
        ).fetchall()
    return {
        "items": [summary_payload(row) for row in rows],
        "limit": limit,
        "offset": offset,
    }


@app.post("/documents/batch")
async def batch_documents(
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
):
    body = await json_object_body(request)
    document_ids = require_selected_ids(body, "batch selection")

    with connect() as connection:
        rows = fetch_selected(connection, document_ids)

    documents = []
    for document_id in document_ids:
        row = rows.get(document_id)
        if row is None or row["tenant_id"] != principal.tenant:
            raise HTTPException(
                status_code=404,
                detail="a selected document is not visible on batch selection",
            )
        if row["reader"] != principal.subject:
            raise HTTPException(
                status_code=403,
                detail="a selected document is not readable on batch selection",
            )
        documents.append(document_payload(row))
    return {"items": documents}


def csv_export(documents: list[dict]) -> str:
    columns = ("id", "title", "content", "tenant", "reader")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for document in documents:
        writer.writerow([document[column] for column in columns])
    return buffer.getvalue()


@app.post("/documents/export")
async def export_documents(
    request: Request,
    principal: Annotated[Principal, Depends(authenticate)],
):
    body = await json_object_body(request)
    # Both request fields are validated before any selection or export work.
    document_ids = require_selected_ids(body, "export")
    export_format = require_export_format(body)

    with connect() as connection:
        rows = fetch_selected(connection, document_ids)

    documents = []
    for document_id in document_ids:
        row = rows.get(document_id)
        if row is None or row["tenant_id"] != principal.tenant:
            raise HTTPException(
                status_code=404,
                detail="a selected document is not visible on export",
            )
        if row["reader"] != principal.subject:
            raise HTTPException(
                status_code=403,
                detail="a selected document is not readable on export",
            )
        documents.append(document_payload(row))

    if export_format == "json":
        return {"documents": documents}
    return Response(
        content=csv_export(documents),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="documents.csv"'},
    )


@app.get("/documents/{documentId}")
def get_document(
    documentId: str,
    principal: Annotated[Principal, Depends(authenticate)],
):
    document_id = require_uuid(documentId, "documentId must be a UUID string")

    with connect() as connection:
        row = fetch_selected(connection, [document_id]).get(document_id)

    if row is None or row["tenant_id"] != principal.tenant:
        raise HTTPException(
            status_code=404, detail="the document is not visible on retrieve"
        )
    if row["reader"] != principal.subject:
        raise HTTPException(
            status_code=403, detail="the document is not readable on retrieve"
        )
    return document_payload(row)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


init_db()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
