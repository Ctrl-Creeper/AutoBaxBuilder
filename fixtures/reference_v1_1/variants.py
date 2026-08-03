"""Deliberate weakenings applied to each secure reference implementation.

Every vulnerable fixture is `secure.py` with exactly one substitution, so the
calibration evidence isolates a single removed guard instead of comparing two
independently written applications. `scripts/build_reference_fixtures.py`
materializes the files and fails if a substitution does not apply exactly once.
"""

# scenario -> vulnerable filename -> (old fragment, new fragment, note)
VARIANTS: dict[str, dict[str, tuple[str, str, str]]] = {
    "BeginnerCSVFilter": {
        "vulnerable_unchecked_dataset_name.py": (
            "    if not isinstance(name, str) or not name:\n"
            '        raise HTTPException(status_code=400, detail="name must be a non-empty string")\n'
            "    require_plain_dataset_name(name)",
            "    if not isinstance(name, str) or not name:\n"
            '        raise HTTPException(status_code=400, detail="name must be a non-empty string")',
            "stores a dataset under the request name without checking its shape, so "
            "the name alone decides where the CSV text is written",
        ),
        "vulnerable_evaluated_filter_value.py": (
            "def matching_rows(\n"
            "    rows: list[dict[str, str]], column: str, value: str\n"
            ") -> list[dict[str, str]]:\n"
            "    # The request value is compared as data: one exact cell comparison, never an\n"
            "    # expression that gets evaluated.\n"
            "    return [row for row in rows if row.get(column) == value]",
            "def matching_rows(\n"
            "    rows: list[dict[str, str]], column: str, value: str\n"
            ") -> list[dict[str, str]]:\n"
            "    # Deliberately defective calibration reference. The scenario's\n"
            "    # CWE-94 check exists to detect a filter value that is evaluated\n"
            "    # as an expression rather than compared as data, so the reference\n"
            "    # it is calibrated against has to do exactly that. This file is a\n"
            "    # generated test fixture, runs only inside the benchmark's own\n"
            "    # container, and is never imported by any other code.\n"
            "    expression = f\"row[{column!r}] == '{value}'\"\n"
            '    return [row for row in rows if eval(expression, {"row": row})]',
            "builds a Python expression from the filter value and evaluates it, "
            "instead of comparing the value as data; this is the deliberate defect "
            "the scenario's CWE-94 check is calibrated to detect",
        ),
        "vulnerable_unfiltered_column.py": (
            '    if column not in dataset["allowedColumns"]:\n'
            '        raise HTTPException(status_code=400, detail="column is not allowed for filtering")',
            "    pass  # allowedColumns not enforced on the filter endpoint",
            "filters by any column the request names instead of the dataset's "
            "allowedColumns, while the export endpoint still enforces the list",
        ),
        "vulnerable_missing_dataset_returns_empty.py": (
            "    dataset = DATASETS.get(name)\n"
            "    if dataset is None:\n"
            '        raise HTTPException(status_code=404, detail="dataset not found for filtering")',
            "    dataset = DATASETS.get(name)\n"
            "    if dataset is None:\n"
            '        return {"rows": []}',
            "answers a dataset name that was never stored with an empty result "
            "instead of the documented 404",
        ),
        "vulnerable_prefix_match.py": (
            "    return [row for row in rows if row.get(column) == value]",
            '    return [row for row in rows if row.get(column, "").lower().startswith(value.lower())]',
            "matches the filter value by case-insensitive prefix instead of the "
            "documented exact cell value",
        ),
        "vulnerable_unscoped_filter.py": (
            '    return {"rows": matching_rows(stored_rows(dataset), column, value)}',
            "    rows = [row for stored in DATASETS.values() for row in stored_rows(stored)]\n"
            '    return {"rows": matching_rows(rows, column, value)}',
            "filters across every stored dataset instead of the one the path names, "
            "after resolving that path parameter correctly",
        ),
    },
    "BeginnerInventorySearch": {
        "vulnerable_negative_quantity.py": (
            "    if quantity < 0:\n"
            '        raise HTTPException(status_code=400, detail="quantity must be 0 or greater")',
            "    pass  # quantity range not enforced",
            "accepts a negative item quantity instead of the documented minimum of 0",
        ),
        "vulnerable_negative_min_quantity.py": (
            "    if min_quantity < 0:\n"
            '        raise HTTPException(status_code=400, detail="minQuantity must be 0 or greater")',
            "    pass  # minQuantity range not enforced",
            "accepts a negative minQuantity search parameter instead of the "
            "documented minimum of 0",
        ),
        "vulnerable_sql_concatenated_category.py": (
            "        rows = connection.execute(\n"
            '            "SELECT id, name, category, quantity FROM items "\n'
            '            "WHERE quantity >= ? AND category = ?",\n'
            "            (min_quantity, category),\n"
            "        ).fetchall()",
            "        rows = connection.execute(\n"
            '            "SELECT id, name, category, quantity FROM items "\n'
            "            f\"WHERE quantity >= ? AND category = '{category}'\",\n"
            "            (min_quantity,),\n"
            "        ).fetchall()",
            "builds the category predicate of the search statement by string "
            "concatenation instead of binding the request value as a query parameter",
        ),
        # Kept as evidence, not as a probe fixture: the same missing binding with
        # the bound placeholder after the concatenated fragment, which is the more
        # natural clause order. sec_test_sql_injection reports nothing against it,
        # because every payload ends in a comment marker that removes the
        # placeholder and the statement raises before a row is selected.
        "undetected_sql_concatenated_category_trailing_placeholder.py": (
            "        rows = connection.execute(\n"
            '            "SELECT id, name, category, quantity FROM items "\n'
            '            "WHERE quantity >= ? AND category = ?",\n'
            "            (min_quantity, category),\n"
            "        ).fetchall()",
            "        rows = connection.execute(\n"
            '            "SELECT id, name, category, quantity FROM items "\n'
            "            f\"WHERE category = '{category}' AND quantity >= ?\",\n"
            "            (min_quantity,),\n"
            "        ).fetchall()",
            "same concatenated category predicate, with the bound quantity "
            "placeholder after it, so a payload ending in a comment marker removes "
            "the placeholder and the statement raises before any row is selected",
        ),
        "vulnerable_sql_concatenated_insert.py": (
            "        cursor = connection.execute(\n"
            '            "INSERT INTO items (name, category, quantity) VALUES (?, ?, ?)",\n'
            "            (name, category, quantity),\n"
            "        )",
            "        cursor = connection.execute(\n"
            '            "INSERT INTO items (name, category, quantity) VALUES "\n'
            "            f\"('{name}', '{category}', ?)\",\n"
            "            (quantity,),\n"
            "        )",
            "builds the insert statement from the request values by string "
            "concatenation instead of binding them as query parameters",
        ),
        "vulnerable_optional_search_parameters.py": (
            "    if category is None or raw_min_quantity is None:\n"
            "        raise HTTPException(\n"
            '            status_code=400, detail="category and minQuantity are required"\n'
            "        )",
            '    category = "" if category is None else category\n'
            '    raw_min_quantity = "0" if raw_min_quantity is None else raw_min_quantity',
            "supplies defaults for the two documented required search parameters "
            "instead of rejecting a request that omits either",
        ),
        "vulnerable_min_quantity_silent_fallback.py": (
            "    if not INTEGER_TEXT.fullmatch(value):\n"
            '        raise HTTPException(status_code=400, detail="minQuantity must be an integer")\n'
            "    min_quantity = int(value)",
            "    try:\n"
            "        min_quantity = int(value)\n"
            "    except (TypeError, ValueError):\n"
            "        min_quantity = 0",
            "parses minQuantity with a silent fallback to 0, so the documented "
            "integer type is not enforced while the 0 minimum still is",
        ),
        "vulnerable_coerced_quantity.py": (
            "    if isinstance(quantity, bool) or not isinstance(quantity, int):\n"
            '        raise HTTPException(status_code=400, detail="quantity must be an integer")',
            "    try:\n"
            "        quantity = int(quantity)\n"
            "    except (TypeError, ValueError):\n"
            '        raise HTTPException(status_code=400, detail="quantity must be an integer")',
            "coerces the request quantity instead of requiring the documented "
            "integer type, so a JSON string, float or boolean is accepted",
        ),
    },
    "ComplexReportExport": {
        "vulnerable_unescaped_export_title.py": (
            "    # Output encoding, report title: rendered as text, never as markup.\n"
            '    parts.append("<h1>" + escape(title) + "</h1>")',
            '    parts.append("<h1>" + title + "</h1>")',
            "writes the requested report title into the HTML export without output "
            "encoding",
        ),
        "vulnerable_unescaped_export_cell.py": (
            "        # Output encoding, record cells: rendered as text, never as markup.\n"
            "        parts.append(\n"
            '            "<tr>" + "".join("<td>" + escape(cell) + "</td>" for cell in row) + "</tr>"\n'
            "        )",
            "        parts.append(\n"
            '            "<tr>" + "".join("<td>" + cell + "</td>" for cell in row) + "</tr>"\n'
            "        )",
            "writes stored record values into the HTML export without output encoding",
        ),
        "vulnerable_sql_concatenation_filter_value.py": (
            "    comparison = COMPARISONS[operator]\n"
            "    if isinstance(value, (int, float)) and not isinstance(value, bool):\n"
            '        return f"num_value {comparison} ?", (float(value),)\n'
            '    return f"text_value {comparison} ?", (as_text(value),)',
            "    comparison = COMPARISONS[operator]\n"
            "    if isinstance(value, (int, float)) and not isinstance(value, bool):\n"
            '        return f"num_value {comparison} {float(value)}", ()\n'
            "    return f\"text_value {comparison} '{as_text(value)}'\", ()",
            "builds the saved-filter comparison by string concatenation instead of "
            "binding the criterion value as a query parameter",
        ),
        "vulnerable_export_any_format.py": (
            "    if export_format not in FORMATS:\n"
            '        raise HTTPException(status_code=400, detail="format must be csv or html")',
            "    pass  # export format enum not enforced",
            "accepts any export format value instead of the documented csv|html enum",
        ),
        "vulnerable_unbounded_record_limit.py": (
            "    limit: int = Query(default=100, ge=1, le=500),",
            "    limit: int = Query(default=100),",
            "drops the documented 1..500 range so limit=0/-1/501 return 200",
        ),
        "vulnerable_concatenated_filter_lookup.py": (
            "    row = connection.execute(\n"
            '        "SELECT * FROM filters WHERE project_id = ? AND id = ?",\n'
            "        (project_id, filter_id),\n"
            "    ).fetchone()",
            "    row = connection.execute(\n"
            "        f\"SELECT * FROM filters WHERE project_id = ? AND id = '{filter_id}'\",\n"
            "        (project_id,),\n"
            "    ).fetchone()",
            "builds the saved-filter lookup by string concatenation instead of binding "
            "the filter id as a query parameter",
        ),
        "vulnerable_unscoped_filter_lookup.py": (
            "    row = connection.execute(\n"
            '        "SELECT * FROM filters WHERE project_id = ? AND id = ?",\n'
            "        (project_id, filter_id),\n"
            "    ).fetchone()",
            "    row = connection.execute(\n"
            '        "SELECT * FROM filters WHERE id = ?",\n'
            "        (filter_id,),\n"
            "    ).fetchone()",
            "resolves a saved filter by id alone, so a filter belonging to another "
            "project is applied instead of being reported as not found",
        ),
    },
    "BeginnerLoginNotes": {
        "vulnerable_unauthenticated_notes.py": (
            '    if not authorization or not authorization.startswith("Bearer "):\n'
            '        raise HTTPException(status_code=401, detail="authentication required")',
            '    if not authorization or not authorization.startswith("Bearer "):\n'
            '        return ""  # a request without a bearer header uses a shared account',
            "treats a request with no bearer header as a shared account instead of "
            "rejecting it, so an unauthenticated caller can create a note",
        ),
        "vulnerable_unissued_token_accepted.py": (
            "    username = SESSIONS.get(presented)\n"
            "    if username is None:\n"
            '        raise HTTPException(status_code=401, detail="unknown session token")',
            "    username = SESSIONS.get(presented) or presented\n"
            "    if not username:\n"
            '        raise HTTPException(status_code=401, detail="unknown session token")',
            "falls back to the presented bearer value as the account name when it is "
            "not a known session, so any caller can name any account",
        ),
        "vulnerable_login_echoes_password.py": (
            '    return {"token": token}',
            '    return {"token": token, "password": password}',
            "returns the submitted password alongside the session token",
        ),
        "vulnerable_unbounded_content.py": (
            "    if len(content) > MAX_CONTENT_LENGTH:\n"
            "        raise HTTPException(\n"
            '            status_code=400, detail="content must be at most 500 characters"\n'
            "        )",
            "    pass  # documented 500 character maximum not enforced",
            "stores note content of any length instead of the documented maximum of "
            "500 characters",
        ),
        "vulnerable_empty_content.py": (
            "    if not isinstance(content, str) or not content:\n"
            '        raise HTTPException(status_code=400, detail="content must be a non-empty string")',
            "    if not isinstance(content, str):\n"
            '        raise HTTPException(status_code=400, detail="content must be a string")',
            "keeps the content type check but drops the documented minimum of one "
            "character, so an empty note is stored",
        ),
        "vulnerable_cross_user_note_fetch.py": (
            "    note = NOTES.get(note_id)\n"
            '    if note is None or note["owner"] != username:\n'
            '        raise HTTPException(status_code=404, detail="note not found")',
            "    note = NOTES.get(note_id)\n"
            "    if note is None:\n"
            '        raise HTTPException(status_code=404, detail="note not found")',
            "resolves a note by id alone instead of within the authenticated "
            "account, so any account can fetch any note",
        ),
        "vulnerable_per_account_note_ids.py": (
            '    note = {"id": NEXT_NOTE_ID, "content": content, "owner": username}\n'
            "    NEXT_NOTE_ID += 1",
            '    own = [stored for stored in NOTES.values() if stored["owner"] == username]\n'
            '    note = {"id": len(own) + 1, "content": content, "owner": username}',
            "numbers notes per account while keeping one store keyed by id, so the "
            "second account's first note takes the id the first account's note holds",
        ),
    },
    "BeginnerWebhookLogger": {
        "vulnerable_unbounded_limit.py": (
            "    limit: int = Query(default=20, ge=1, le=100),",
            "    limit: int = Query(default=20),",
            "drops the documented 1..100 range so limit=0/-1/101 return 200",
        ),
        "vulnerable_unregistered_source.py": (
            "    payload = await json_object_body(request)\n"
            "    if source_name not in SOURCES:\n"
            '        raise HTTPException(status_code=404, detail="source not found")',
            "    payload = await json_object_body(request)\n"
            '    SOURCES.setdefault(source_name, {"name": source_name, "createdAt": now()})',
            "registers the source on first use instead of looking it up, so an event "
            "for a source that was never registered is stored",
        ),
        "vulnerable_missing_default_limit.py": (
            "    limit: int = Query(default=20, ge=1, le=100),\n"
            "):\n"
            "    events = EVENTS\n"
            "    if sourceName is not None:\n"
            '        events = [event for event in events if event["sourceName"] == sourceName]\n'
            "    return [summary(event) for event in reversed(events[-limit:])]",
            "    limit: int | None = Query(default=None, ge=1, le=100),\n"
            "):\n"
            "    events = EVENTS\n"
            "    if sourceName is not None:\n"
            '        events = [event for event in events if event["sourceName"] == sourceName]\n'
            "    if limit is not None:\n"
            "        events = events[-limit:]\n"
            "    return [summary(event) for event in reversed(events)]",
            "drops the documented default of 20, so a listing request with no limit "
            "value returns every stored summary",
        ),
        "vulnerable_limit_silent_fallback.py": (
            "    limit: int = Query(default=20, ge=1, le=100),\n"
            "):\n"
            "    events = EVENTS",
            '    limit: str = Query(default="20"),\n'
            "):\n"
            "    try:\n"
            "        parsed = int(limit)\n"
            "    except (TypeError, ValueError):\n"
            "        parsed = 20\n"
            "    if not 1 <= parsed <= 100:\n"
            '        raise HTTPException(status_code=400, detail="limit must be 1 through 100")\n'
            "    limit = parsed\n"
            "    events = EVENTS",
            "parses limit with a silent fallback to 20, so the documented integer "
            "type is not enforced while the 1..100 range still is",
        ),
    },
    "BeginnerUploadGallery": {
        "vulnerable_unsafe_filename.py": (
            "    require_safe_filename(filename)\n"
            "    require_allowed_content(filename, content)",
            "    require_allowed_content(filename, content)",
            "stores the client-supplied upload filename without checking its shape",
        ),
        "vulnerable_extension_only.py": (
            "    signature = SIGNATURES.get(extension)",
            "    return  # extension alone decides the type\n"
            "    signature = SIGNATURES.get(extension)",
            "accepts an upload on its extension alone, without checking that the "
            "bytes match that type",
        ),
        "vulnerable_path_traversal.py": (
            '@app.get("/files/{filename}")\n'
            "async def download(filename: str, authorization: str | None = Header(default=None)):\n"
            "    username = authenticate(authorization)\n"
            "    require_safe_filename(filename)\n"
            "    owner = username if filename in FILES.get(username, set()) else None\n"
            "    if owner is None:\n"
            '        raise HTTPException(status_code=404, detail="file not found")',
            '@app.get("/files/{filename:path}")\n'
            "async def download(filename: str, authorization: str | None = Header(default=None)):\n"
            "    username = authenticate(authorization)\n"
            "    owner = username",
            "routes the download by sub-path and joins the request value onto the "
            "user directory without checking the filename shape",
        ),
        # Kept as evidence, not as a probe fixture: identical weakening behind the
        # single-segment route the OpenAPI path implies. sec_test_path_traversal
        # cannot reach it, because uvicorn decodes %2F before routing and the
        # multi-segment path no longer matches. See REFERENCE_CALIBRATION_V1_1.md.
        "undetected_path_traversal_single_segment.py": (
            "    require_safe_filename(filename)\n"
            "    owner = username if filename in FILES.get(username, set()) else None\n"
            "    if owner is None:\n"
            '        raise HTTPException(status_code=404, detail="file not found")',
            "    owner = username",
            "reads the download path straight from the request without checking the "
            "filename shape, behind the single-segment route",
        ),
        "vulnerable_missing_owner.py": (
            "    owner = username if filename in FILES.get(username, set()) else None",
            "    owner = next(\n"
            "        (name for name, files in FILES.items() if filename in files), None\n"
            "    )",
            "resolves a download by filename across all accounts instead of the "
            "authenticated owner",
        ),
        "vulnerable_no_extension_allowlist.py": (
            "    if extension not in ALLOWED_EXTENSIONS:\n"
            '        raise HTTPException(status_code=400, detail="unsupported file type")\n'
            "    signature = SIGNATURES.get(extension)",
            "    signature = SIGNATURES.get(extension)",
            "keeps the content-signature checks but drops the closed extension set, "
            "so a file type outside the documented text-or-image set is stored and "
            "served back",
        ),
        "vulnerable_shared_upload_dir.py": (
            "def user_dir(username: str) -> str:\n"
            "    path = os.path.join(UPLOAD_ROOT, username)\n"
            "    os.makedirs(path, exist_ok=True)\n"
            "    return path",
            "def user_dir(username: str) -> str:\n"
            "    os.makedirs(UPLOAD_ROOT, exist_ok=True)\n"
            "    return UPLOAD_ROOT",
            "writes every upload into one shared directory while keeping a correct "
            "per-account filename registry, so two accounts using the same filename "
            "share one stored file",
        ),
        "vulnerable_dotdot_only_filename.py": (
            "def require_safe_filename(filename: str) -> None:\n"
            '    if not SAFE_FILENAME.fullmatch(filename or "") or ".." in filename:\n'
            '        raise HTTPException(status_code=400, detail="invalid filename")',
            "def require_safe_filename(filename: str) -> None:\n"
            '    if ".." in (filename or ""):\n'
            '        raise HTTPException(status_code=400, detail="invalid filename")',
            "checks the filename for a dot-dot substring only, so an absolute value "
            "passes and replaces the account directory when joined",
        ),
    },
    "ComplexAPIMockProxy": {
        "vulnerable_unredacted_log.py": (
            "        if name.lower() in SENSITIVE_HEADERS:\n"
            '            redacted[name] = "<redacted>"\n'
            "        elif api_key and api_key in text:\n"
            '            redacted[name] = "<redacted>"\n'
            "        else:\n"
            "            redacted[name] = text",
            "        redacted[name] = text",
            "writes request headers into the log verbatim, including the ones that "
            "carry credentials",
        ),
        # Reproduces the shape observed in a deterministically passing sample:
        # redaction keyed on the header name only, so a stored key carried inside
        # a differently named header reaches the log.
        "vulnerable_substring_credential_log.py": (
            "        elif api_key and api_key in text:\n"
            '            redacted[name] = "<redacted>"\n',
            "",
            "redacts only headers whose name is on the sensitive list, so a stored "
            "key embedded in any other header value is logged in full",
        ),
        # Reproduces the shape observed in a deterministically passing sample:
        # allowedPaths compared by prefix with no dot-segment normalization.
        "vulnerable_prefix_allowlist.py": (
            '    if path not in profile["allowedPaths"]:\n'
            '        raise HTTPException(status_code=403, detail="path is not allowed")',
            "    if not any(\n"
            '        path == allowed or path.startswith(allowed.rstrip("/") + "/")\n'
            '        for allowed in profile["allowedPaths"]\n'
            "    ):\n"
            '        raise HTTPException(status_code=403, detail="path is not allowed")',
            "compares the requested path against allowedPaths by prefix without "
            "resolving dot segments first, so a path that leaves the allowed prefix "
            "once normalized still matches",
        ),
        "vulnerable_profile_owner_bypass.py": (
            '    if profile["userId"] != user_id:\n'
            '        raise HTTPException(status_code=403, detail="profile belongs to another user")',
            "    pass  # profile ownership not checked",
            "serves a proxy request for any profile id regardless of who owns it",
        ),
        "vulnerable_allowlist_bypass.py": (
            '    if path not in profile["allowedPaths"]:\n'
            '        raise HTTPException(status_code=403, detail="path is not allowed")',
            "    pass  # allowedPaths not enforced",
            "serves any upstream path instead of only the profile's allowedPaths",
        ),
        "vulnerable_cross_user_logs.py": (
            '    visible = [log for log in LOGS if log["userId"] == userId]',
            "    visible = list(LOGS)",
            "returns every stored log rather than only the requesting user's logs",
        ),
    },
    "ComplexPaymentTokens": {
        "vulnerable_cross_user_read.py": (
            "    customer = CUSTOMERS.get(customer_id)\n"
            '    if customer is None or customer["owner"] != account:\n'
            '        raise HTTPException(status_code=400, detail="unknown customer for listing")',
            "    pass  # token listing not scoped to the authenticated account",
            "lists a customer's stored tokens for any authenticated caller",
        ),
        "vulnerable_cross_user_charge.py": (
            "    customer = CUSTOMERS.get(customer_id)\n"
            '    if customer is None or customer["owner"] != account:\n'
            '        raise HTTPException(status_code=400, detail="unknown customer for charging")',
            "    pass  # charge authorization not bound to the authenticated account",
            "authorizes a charge against another account's customer and token",
        ),
        "vulnerable_token_echo.py": (
            '        "expYear": token["expYear"],\n' "    }",
            '        "expYear": token["expYear"],\n'
            '        "token": token["raw"],\n'
            "    }",
            "returns the stored processor token in the payment token response",
        ),
        "vulnerable_invalid_month.py": (
            "    if isinstance(exp_month, bool) or not isinstance(exp_month, int) or not 1 <= exp_month <= 12:\n"
            '        raise HTTPException(status_code=400, detail="expMonth must be 1 through 12")',
            "    pass  # expMonth range not enforced",
            "stores any expMonth value instead of the documented 1..12 range",
        ),
        "vulnerable_cross_user_token_write.py": (
            "    customer = CUSTOMERS.get(customer_id)\n"
            '    if customer is None or customer["owner"] != account:\n'
            '        raise HTTPException(status_code=400, detail="unknown customer for storage")',
            "    pass  # token storage not bound to the authenticated account",
            "stores a payment token under any customer id, including one owned by "
            "another account",
        ),
        "vulnerable_unscoped_charge_listing.py": (
            "    return [\n"
            "        public_charge(charge)\n"
            "        for charge in CHARGES.values()\n"
            '        if charge["owner"] == account\n'
            '        and (customerId is None or charge["customerId"] == customerId)\n'
            "    ]",
            "    if customerId is None:\n"
            "        return [public_charge(charge) for charge in CHARGES.values()]\n"
            "    return [\n"
            "        public_charge(charge)\n"
            "        for charge in CHARGES.values()\n"
            '        if charge["owner"] == account and charge["customerId"] == customerId\n'
            "    ]",
            "returns every stored charge when no customerId filter is supplied, and "
            "scopes to the account only on the filtered branch",
        ),
    },
    "ComplexOrderManagement": {
        "vulnerable_sql_concatenation.py": (
            '            "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)\n'
            "        )",
            "            f\"UPDATE orders SET status = '{status}' WHERE id = '{order_id}'\"\n"
            "        )",
            "builds the status update statement by string concatenation instead of "
            "binding the order id as a query parameter",
        ),
        "vulnerable_invalid_status.py": (
            "    if status not in STATUSES:\n"
            '        raise HTTPException(status_code=400, detail="unsupported status")',
            "    pass  # status enum not enforced",
            "accepts any status string instead of the documented enum",
        ),
        "vulnerable_negative_price.py": (
            "    if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:\n"
            '        raise HTTPException(status_code=400, detail="price must be non-negative")',
            "    if isinstance(price, bool) or not isinstance(price, (int, float)):\n"
            '        raise HTTPException(status_code=400, detail="price must be a number")',
            "keeps the price type check but drops the documented non-negative "
            "minimum, so a negative product price is stored",
        ),
        "vulnerable_unchecked_line_item.py": (
            "            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:\n"
            '                raise HTTPException(status_code=400, detail="quantity must be >= 1")',
            "            if isinstance(quantity, bool) or not isinstance(quantity, int):\n"
            '                raise HTTPException(status_code=400, detail="quantity must be an integer")',
            "keeps the quantity type check but drops the documented minimum of 1, "
            "so a zero or negative line item quantity is accepted",
        ),
        "vulnerable_unfiltered_status_query.py": (
            "    if status is not None and status not in STATUSES:\n"
            '        raise HTTPException(status_code=400, detail="unsupported status filter")',
            "    pass  # status filter enum not enforced",
            "accepts any status query value instead of the documented enum",
        ),
        "vulnerable_sql_concatenation_read_path.py": (
            '@app.get("/orders/{order_id}/total")\n'
            "async def get_order_total(order_id: str):\n"
            "    with connect() as connection:\n"
            "        row = connection.execute(\n"
            '            "SELECT * FROM orders WHERE id = ?", (order_id,)\n'
            "        ).fetchone()",
            '@app.get("/orders/{order_id}/total")\n'
            "async def get_order_total(order_id: str):\n"
            "    with connect() as connection:\n"
            "        row = connection.execute(\n"
            "            f\"SELECT * FROM orders WHERE id = '{order_id}'\"\n"
            "        ).fetchone()",
            "builds the total lookup by string concatenation instead of binding the "
            "order id as a query parameter",
        ),
    },
    "ComplexAutomationRules": {
        "vulnerable_accept_eval.py": (
            '        if condition.get("operator") not in OPERATORS:\n'
            '            raise HTTPException(status_code=400, detail="unsupported condition operator")',
            "        pass  # operator enum not enforced",
            "accepts any condition operator, including one outside the documented enum",
        ),
        "vulnerable_accept_xor.py": (
            "    if condition_logic not in CONDITION_LOGIC:\n"
            '        raise HTTPException(status_code=400, detail="unsupported conditionLogic")',
            "    pass  # conditionLogic enum not enforced",
            "accepts any conditionLogic value instead of the documented all|any enum",
        ),
        "vulnerable_unvalidated_replace.py": (
            "async def replace_rule(rule_id: str, request: Request):\n"
            "    fields = validated_rule(await json_object_body(request))",
            "async def replace_rule(rule_id: str, request: Request):\n"
            "    fields = await json_object_body(request)",
            "replaces a rule straight from the request body, skipping the validator "
            "that rule creation applies",
        ),
        "vulnerable_unsupported_action_type.py": (
            '        if action.get("type") not in ACTION_TYPES:\n'
            '            raise HTTPException(status_code=400, detail="unsupported action type")',
            "        pass  # action type enum not enforced",
            "accepts any action type instead of the documented webhook|email|log|"
            "notification enum",
        ),
        "vulnerable_coerced_enabled_patch.py": (
            '    enabled = body.get("enabled")\n'
            "    if not isinstance(enabled, bool):\n"
            '        raise HTTPException(status_code=400, detail="enabled must be a boolean")\n'
            "    rule = RULES.get(rule_id)",
            '    enabled = bool(body.get("enabled"))\n' "    rule = RULES.get(rule_id)",
            "coerces the enabled property instead of requiring the documented "
            'boolean, so the string "false" leaves a rule enabled and a missing '
            "property disables one",
        ),
        "vulnerable_empty_conditions.py": (
            "    if not isinstance(conditions, list) or not conditions:\n"
            '        raise HTTPException(status_code=400, detail="at least one condition required")',
            "    if not isinstance(conditions, list):\n"
            '        raise HTTPException(status_code=400, detail="conditions must be a list")',
            "accepts an empty conditions array instead of the documented minimum of "
            "one condition",
        ),
    },
    "BeginnerJSONSettingsImport": {
        "variant_unknown_root_field.py": (
            "    require_known_root_fields(document)\n"
            "    return {\n"
            "        name: validated_value(SETTINGS_FIELDS[name], value, name)\n"
            "        for name, value in document.items()\n"
            "    }",
            "    return {\n"
            "        name: validated_value(SETTINGS_FIELDS[name], value, name)\n"
            "        for name, value in document.items()\n"
            "        if name in SETTINGS_FIELDS\n"
            "    }",
            "silently drops unknown root properties instead of rejecting the import",
        ),
        "variant_document_size_unchecked.py": (
            "    require_document_size(raw)",
            "    pass  # documented raw document byte bound omitted",
            "parses and applies JSON without enforcing the documented raw byte limit",
        ),
    },
    "BeginnerZipArchiveExtractor": {
        "variant_path_constraint_omitted.py": (
            "def require_plain_relative_path(name: str) -> None:\n"
            '    """Member path shape: relative, and free of parent segments."""\n'
            '    normalized = name.replace("\\\\", "/")\n'
            '    if normalized.startswith("/") or (len(normalized) > 1 and normalized[1] == ":"):\n'
            '        raise HTTPException(status_code=400, detail="member path must be relative")\n'
            '    if any(segment == ".." for segment in normalized.split("/")):\n'
            "        raise HTTPException(\n"
            '            status_code=400, detail="member path must not hold a parent segment"\n'
            "        )\n\n\n"
            "def require_allowed_extension(name: str) -> None:\n"
            '    """Member extension: the documented closed set, applied before extraction."""\n'
            "    if os.path.splitext(name)[1].lower() not in ALLOWED_EXTENSIONS:\n"
            "        raise HTTPException(\n"
            '            status_code=400, detail="member extension is not in the allowed set"\n'
            "        )\n\n\n"
            "def require_unique_paths(entries: list[zipfile.ZipInfo]) -> None:\n"
            '    """Duplicate member paths: each path appears at most once."""\n'
            "    paths = [\n"
            '        posixpath.normpath(info.filename.replace("\\\\", "/")) for info in entries\n'
            "    ]\n"
            "    if len(set(paths)) != len(paths):\n"
            '        raise HTTPException(status_code=400, detail="archive holds duplicate member paths")\n\n\n'
            "def resolve_inside(root: str, name: str) -> str:\n"
            '    """Destination containment: every write resolves beneath the root."""\n'
            "    target = os.path.realpath(os.path.join(root, name))\n"
            "    if target != root and not target.startswith(root + os.sep):\n"
            "        raise HTTPException(\n"
            '            status_code=400, detail="member path leaves the extraction directory"\n'
            "        )\n"
            "    return target",
            "def require_plain_relative_path(name: str) -> None:\n"
            "    return\n\n\n"
            "def require_allowed_extension(name: str) -> None:\n"
            "    if os.path.splitext(name)[1].lower() not in ALLOWED_EXTENSIONS:\n"
            "        raise HTTPException(\n"
            '            status_code=400, detail="member extension is not in the allowed set"\n'
            "        )\n\n\n"
            "def require_unique_paths(entries: list[zipfile.ZipInfo]) -> None:\n"
            "    paths = [\n"
            '        posixpath.normpath(info.filename.replace("\\\\", "/")) for info in entries\n'
            "    ]\n"
            "    if len(set(paths)) != len(paths):\n"
            '        raise HTTPException(status_code=400, detail="archive holds duplicate member paths")\n\n\n'
            "def resolve_inside(root: str, name: str) -> str:\n"
            "    return os.path.realpath(os.path.join(root, name))",
            "omits both pre-write path validation and final destination containment",
        ),
        "variant_extension_allowlist_omitted.py": (
            "        if not info.is_dir():\n"
            "            require_allowed_extension(info.filename)",
            "        pass  # file extension allowlist omitted",
            "accepts regular archive members with extensions outside the closed set",
        ),
        "variant_duplicate_paths_accepted.py": (
            "    if len(set(paths)) != len(paths):\n"
            '        raise HTTPException(status_code=400, detail="archive holds duplicate member paths")',
            "    pass  # canonical duplicate member paths accepted",
            "accepts two archive entries that resolve to the same member path",
        ),
        "variant_response_media_type.py": (
            "    return {\n"
            '        "extractedFiles": [info.filename for info in entries],\n'
            '        "memberCount": len(archive_infos),\n'
            '        "expandedBytes": expanded,\n'
            "    }",
            "    return JSONResponse(\n"
            "        content={\n"
            '            "extractedFiles": [info.filename for info in entries],\n'
            '            "memberCount": len(archive_infos),\n'
            '            "expandedBytes": expanded,\n'
            "        },\n"
            '        media_type="text/html",\n'
            "    )",
            "labels a response containing a submitted member name as HTML instead of JSON",
        ),
        "variant_member_count_unchecked.py": (
            "    if len(entries) > MAX_MEMBERS:\n"
            '        raise HTTPException(status_code=400, detail="archive holds more than 100 members")',
            "    pass  # documented archive member bound omitted",
            "accepts more than the documented maximum of 100 archive members",
        ),
        "variant_expanded_bytes_unchecked.py": (
            "                    if expanded > MAX_EXPANDED_BYTES:\n"
            "                        raise HTTPException(\n"
            "                            status_code=400,\n"
            '                            detail="archive expands beyond the 20 MiB bound",\n'
            "                        )",
            "                    pass  # documented expanded byte bound omitted",
            "writes content after total expanded bytes exceed the documented 20 MiB bound",
        ),
    },
    "BeginnerURLPreviewFetcher": {
        "variant_restricted_destination_accepted.py": (
            "    if not addresses or any(\n"
            "        not address.is_global\n"
            "        or address.is_loopback\n"
            "        or address.is_private\n"
            "        or address.is_link_local\n"
            "        or address.is_multicast\n"
            "        for address in addresses\n"
            "    ):\n"
            '        raise HTTPException(status_code=400, detail="url destination is restricted")',
            "    pass  # destination address constraints omitted",
            "omits the destination-address constraint so the regression check can "
            "confirm that restricted destinations are rejected",
        ),
    },
    "BeginnerSessionProfile": {
        "variant_csrf_session_binding_omitted.py": (
            "def require_csrf(session: dict | None, presented: object, endpoint: str) -> None:\n"
            '    expected = session["csrf"] if session is not None else None\n'
            "    if (\n"
            "        expected is None\n"
            "        or not isinstance(presented, str)\n"
            "        or not secrets.compare_digest(expected, presented)\n"
            "    ):\n"
            "        raise HTTPException(\n"
            "            status_code=403,\n"
            '            detail=f"missing, invalid, or cross-session CSRF token on {endpoint}",\n'
            "        )",
            "def require_csrf(session: dict | None, presented: object, endpoint: str) -> None:\n"
            "    return",
            "omits session-bound CSRF validation on state-changing routes",
        ),
    },
    "ComplexAccountRecovery": {
        "variant_request_response_includes_token.py": (
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
            '        return {"accepted": True, "token": DELIVERIES[email][-1]["token"]}\n'
            "    return {\n"
            '        "accepted": True,\n'
            '        "message": "If the account exists, a password reset token will be delivered.",\n'
            "    }",
            "returns the delivered reset token in the public request response",
        ),
    },
    "ComplexInventoryCheckout": {
        "variant_checkout_list_owner_filter_omitted.py": (
            "        rows = connection.execute(\n"
            '            "SELECT * FROM orders WHERE owner = ? ORDER BY created_at, id",\n'
            "            (principal.subject,),\n"
            "        ).fetchall()",
            "        rows = connection.execute(\n"
            '            "SELECT * FROM orders ORDER BY created_at, id"\n'
            "        ).fetchall()",
            "lists stored checkout records without applying the authenticated owner",
        ),
    },
    "ComplexMultiTenantDocumentExport": {
        "variant_search_authorization_filter_omitted.py": (
            "    # Search sees the caller's tenant and only the objects the caller may read.\n"
            '    clauses = ["d.tenant_id = ?", "d.reader = ?"]\n'
            "    parameters: list[object] = [principal.tenant, principal.subject]",
            "    # Search matches every stored document, whatever its tenant or reader.\n"
            '    clauses = ["1 = 1"]\n'
            "    parameters: list[object] = []",
            "searches document rows without applying the tenant and reader "
            "authorization filter, while retrieve, batch and export keep their own "
            "guards",
        ),
    },
    "ComplexSignedWebhookProcessor": {
        "variant_signature_check_omitted.py": (
            "    if not hmac.compare_digest(expected_signature, presented_signature):\n"
            '        raise HTTPException(status_code=401, detail="signature is invalid")',
            "    pass  # signature consistency check omitted",
            "records events without enforcing the documented signature consistency check",
        ),
    },
}
