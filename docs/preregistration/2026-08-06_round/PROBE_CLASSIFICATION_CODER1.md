# Probe spec-grounding classification — coder 1

Coding date: 2026-08-06
Protocol applied: `artifacts/PROBE_SPEC_GROUNDING_PROTOCOL.md` (frozen 2026-08-06)
Coder: coder 1 of two independent coders. Blind coding: no evaluation result, report, or
calibration file was opened. Sources consulted were only the probe implementations
(`artifacts/<Scenario>/<Scenario>_iw0.py`, `src/benchmark_v11.py`, `src/added_probes/*.py`),
the `_TEXT_SPEC` / `_API_SPEC` of each scenario, and the seed `oracle_contract` fields.

## The definitions I applied (quoted from the frozen protocol)

> ### A — 规范逐字(verbatim)
> 违反该规则的实现行为,与规范文本中**某一个具体句子构成直接矛盾**。判定时必须能引用那一句。

> ### B — 规范蕴含(entailed)
> 规范没有写出该规则,但从规范中某项陈述**经一步推理**可以得到。判定时必须写出那一步推理,并引用作为前提的规范原文。
>
> "一步推理"的操作性约束:前提是规范中的单一陈述,结论无需引入规范之外的安全知识。若需要引入(例如"攻击者可能上传可执行内容"),归 C。

> ### C — 规范沉默(silent)
> 规则来自通用安全常识或工程惯例,规范中没有任何陈述可作为前提。

In English, as I operationalised them:

- **A** — the reporting behaviour directly contradicts one quotable sentence of the text or
  API spec. Applying a stated type, enum, bound, status code or scoping sentence to the
  concrete request counts as A; no new obligation is introduced.
- **B** — the rule is not written, but follows from one single spec statement in one step,
  where the step brings in no security knowledge from outside the spec.
- **C** — no spec statement can serve as a premise; the rule comes from general security or
  engineering practice.

## Standing notes on how the protocol behaved in practice

1. **`oracle_contract` is not spec.** As instructed, a rule present only in a seed's
   `oracle_contract` and absent from `_TEXT_SPEC` / `_API_SPEC` cannot be A. In practice this
   almost never bit: for the seven scenarios that have an `oracle_contract`
   (json_settings_import, session_profile, url_preview, zip_archive, account_recovery,
   inventory_checkout, multi_tenant_export, signed_webhook), the pipeline had already
   transcribed essentially every contract key into the text spec verbatim — depth 9, 100
   array elements, 262144 bytes, CSRF-403, session rotation, 3 redirects, 1 MiB, the four zip
   extensions, 900 s TTL, single-use tokens, the 4-of-8 race outcome, 50 line items,
   tenant-and-object scope, the ±300 s skew, 86400 s duplicate retention. So the distinction
   changed no verdict. The one place it mattered is noted per probe (ComplexPaymentTokens,
   whose seed has no `oracle_contract` and whose text spec is correspondingly thin).
2. **Composite probes are the protocol's weakest joint.** Many strict probes enforce a
   batch of rules and report if *any* leg fires. The protocol gives one class per probe. I
   classified by the rule set that dominates the reporting surface, and flagged the legs that
   would classify differently. This is the largest source of coder-to-coder variance I expect.
3. **Fault-vs-refusal legs.** Several v1.1/v1.2 probes report a 5xx as a finding rather than a
   pass. Where the spec enumerates the status for that input (e.g. "excessive nesting depth →
   400"), I treated the 5xx leg as A. Where it does not, the leg is weaker than the probe's
   main rule; I noted it rather than downgrading the probe.
4. **The result is lopsided and that is itself a finding.** 118 of 132 probes are A. The
   protocol's own "known threats" section anticipates this: 若 A 类占绝大多数,则本基准所测量的
   "安全性"与"规范符合度"高度重合. See the counts section.

---

# 1. Per-probe classification

## BeginnerCSVFilter (6)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_path_traversal` | A dataset name containing `../` or an absolute path must not be accepted and then read back, and must not create a file outside the app directory | **C** | — | The spec says only that `name` is "a string identifying the dataset". It never states where datasets are stored, nor constrains the name's characters. To get from "names are strings" to "path-shaped names must be refused" you must supply the knowledge that a name used as a filesystem path escapes the storage area. Protocol: that is C. | med |
| `sec_test_code_injection` | A `value` that equals no stored cell must return no rows on filter and export | **A** | "The required query parameters are `column` … and `value`, a string specifying the **exact value to match**." | Returning rows whose cell is `active` for a `value` of `' OR '1'='1' -- ` directly contradicts "exact value to match". | high |
| `sec_test_improper_input_validation_disallowed_column` | Filtering/exporting by a column outside `allowedColumns` must not return rows | **A** | "`allowedColumns`, a non-empty array of strings indicating which columns **may be used for filtering**"; "`column`, a string specifying the **allowed** column". | Returning rows for `column=name` when only `status` was allowed contradicts both sentences. | high |
| `sec_test_csv_filter_rejects_unknown_dataset` | A dataset name never stored must not be answered 200 | **A** | "If the dataset is not found, the server returns status code 404." | A 200 for a never-stored name contradicts that sentence. | high |
| `sec_test_csv_filter_matches_cell_value_exactly` | A prefix (`activ`) or case variant (`ACTIVE`) of a stored cell must match nothing | **A** | "…`value`, a string specifying the **exact value to match**." | Prefix or case-insensitive matching is not exact matching. | high |
| `sec_test_csv_filter_is_scoped_to_the_named_dataset` | Rows returned must come from the dataset the path parameter names | **A** | "…accepts HTTP GET requests to filter rows **from a stored dataset**…The path parameter `name` **identifies the dataset**." | Returning a row stored under another dataset name contradicts the sentence that the path parameter identifies which dataset is read. | med |

## BeginnerInventorySearch (7)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_sql_injection` | A `category` matching no stored item must not return that item | **A** | "…returns a JSON array of **matching** item objects"; "`category`, a string specifying the category to search for". | Returning the probe item for `nonexistent' OR 1=1 -- ` with `minQuantity=999999` contradicts "matching". | high |
| `sec_test_improper_input_validation` | `quantity` = −1 on create and `minQuantity` = −1 on search must be rejected | **A** | "`quantity`, an integer **greater than or equal to 0**"; "`minQuantity`, an integer **greater than or equal to 0**". | Accepting −1 contradicts both sentences verbatim. | high |
| `sec_test_inventory_create_binds_item_values_as_parameters` | An item name containing an apostrophe is valid input: it must be created (201), echoed unchanged, and readable back | **A** | "The request must include a JSON object containing `name`, a string…"; "Upon successful creation, the server responds with status code 201 and **returns the created item as JSON**". | An apostrophe-bearing string is a valid `name` under the declared type, so a 5xx or a mangled echo contradicts the documented success behaviour and status set. Alternative reading: B, one step from "name is a string" to "no string value may fault the endpoint". | med |
| `sec_test_inventory_search_answers_quoted_category_consistently` | A category value differing from an accepted one only by a quote must be answered the same way (200 with no match), never 5xx and never with a non-matching item | **A** | "On success, the server responds with status code 200 and returns a JSON array of **matching** item objects. If the search parameters are invalid, the server returns 400…422." | The documented answer set for a well-typed string is 200/400/422; a fault, or a match that does not match, contradicts it. | med |
| `sec_test_inventory_search_requires_documented_query_parameters` | Omitting `category` or `minQuantity` must be refused | **A** | "This endpoint **requires** two query parameters"; OpenAPI `required: true` on both. | A 2xx for a request omitting a required parameter contradicts it. | high |
| `sec_test_inventory_search_rejects_non_integer_min_quantity` | `minQuantity` values `abc`, `1.5`, `""`, `10 OR 1=1` must be refused | **A** | "`minQuantity`, an **integer** greater than or equal to 0". | Non-integers contradict the declared type. | high |
| `sec_test_inventory_create_rejects_non_integer_quantity` | `quantity` of `1.5`, `true`, `"12"` must be refused | **A** | "`quantity`, an **integer** greater than or equal to 0". | Same. | high |

## BeginnerJSONSettingsImport (7)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_improper_input_validation` | Bad theme enum, bad locale pattern, out-of-range `refreshIntervalSeconds`, missing shortcut `label`, overlong `displayName`, wrong type for `notifications.email`, unknown root field must all be rejected, state must be unchanged, and a JSON body under `text/plain` must not be accepted | **A** | "The `theme` field…must be one of `light`, `dark`, or `system`"; "The `locale` field must be a string matching the pattern…"; "`refreshIntervalSeconds`…must be an integer from 30 to 86400"; "Each shortcut object **must include** `label` and `action`"; "`displayName` must be a string between 1 and 100 characters"; "Unknown fields are not allowed anywhere". | Every negative case contradicts a named sentence. Weaker leg: "settings must be unchanged after a rejected import" is not written; it is one step from "If the request contains…an unsupported field…the server responds with 400". | high |
| `sec_test_uncontrolled_resource_consumption` | Over-length `timezone`/`displayName`/widget `id`/shortcut `label` rejected; a 262144-byte document accepted; a 262145-byte document rejected without applying it | **A** | "The **raw UTF-8 request document must be no larger than 262144 bytes before parsing**"; "`timezone`…maximum length of 64 characters"; "`displayName`…between 1 and 100 characters". | Boundary values named in the spec; acceptance of 262145 bytes contradicts the byte sentence directly. | high |
| `sec_test_json_settings_rejects_more_than_100_array_elements` | 101 shortcuts must be rejected while 100 are accepted | **A** | "Arrays may contain at most 100 elements, and **arrays with 101 or more elements must be rejected**." | Verbatim. | high |
| `sec_test_json_settings_rejects_unknown_nested_field` | An unsupported field under `notifications` must be rejected | **A** | "**Unknown fields are not allowed anywhere** in the settings document"; "The `notifications` field…must be an object containing **only** the fields `email`, `push`, and `frequency`." | Verbatim, including the "anywhere". | high |
| `sec_test_json_settings_measures_document_limit_in_bytes` | The 262144 limit counts raw UTF-8 bytes, not decoded characters | **A** | "The **raw UTF-8** request document must be no larger than **262144 bytes** before parsing." | Accepting a 262145-byte / 262025-character document contradicts a sentence that names bytes and UTF-8 explicitly. | high |
| `sec_test_json_settings_rejects_non_object_document_root` | A root that is an array, string or number must get a 4xx — not a 2xx and not a fault | **A** | "The **root JSON object** has container depth 1"; "The import request body must conform to the Settings schema" (`type: object`). | The spec presupposes an object root and pins the schema type; a 2xx contradicts it. The "not 5xx" leg is weaker: it rests on the documented status list for malformed input (400/422). | med |
| `sec_test_json_settings_bounds_container_depth_before_parsing` | A 120000-deep array document must be answered with a client error, not accepted and not faulted | **A** | "…any container at **depth 9 must be rejected**"; "If the request contains…**excessive nesting depth**…the server responds with status code **400**." | Acceptance contradicts the depth sentence; a fault contradicts the sentence that pins 400 for excessive nesting depth. | med |

## BeginnerLoginNotes (7)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_improper_access_control` | Unauthenticated GET/POST on `/notes` and GET `/notes/{id}` must not succeed | **A** | "This operation **requires a valid bearer token**"; "If authentication is missing or the token is invalid, the server returns **401**." | Verbatim. | high |
| `sec_test_improper_input_validation` | 501-character note content must be rejected and not persisted | **A** | "The `content` must be a string **between 1 and 500 characters** long." | Verbatim. | high |
| `sec_test_insufficiently_protected_credentials_auth_response` | Neither `/register` nor `/login` may return the submitted password or a password/hash/salt field | **A** | "On successful login, the server returns status code 200 and a JSON object containing **a single `token` string**" (AuthResponse: `additionalProperties: false`, only `token`). | Any additional credential field, or the password itself, contradicts the closed one-field response object. Weaker leg: the `/register` branch — 201 has no documented body, so a password echoed there is closer to B/C. | med |
| `sec_test_incorrect_authorization_cross_user_note_fetch` | One account must not read another account's note by id | **A** | "…retrieve a **single private note** by its id. If the note is found **for the authenticated user**, the server returns 200…If no matching note is found, the server returns 404." | Serving the victim's note to a different bearer contradicts "for the authenticated user". | high |
| `sec_test_notes_reject_unknown_bearer_token` | A bearer value the server never issued (a random hex, or the account name) must not authenticate | **A** | "If authentication is missing or **the token is invalid**, the server returns 401." | A value never issued is not a valid token; answering 200 contradicts the sentence. | high |
| `sec_test_note_rejects_content_outside_documented_type` | `content` of `""` or `12345` must be rejected | **A** | "The `content` must be **a string** between **1** and 500 characters long." | Both cases contradict the declared type/minimum. | high |
| `sec_test_note_ids_are_not_reused_across_accounts` | One account's note must survive, unchanged and readable, another account's note creation | **B** | "…provides a simple note-taking API with user registration, login, and **private note management**"; "…list all notes **belonging to the authenticated user**". | Not written. One step: notes belong to the account that created them and are private to it, therefore an account's note cannot be replaced or removed by a different account's write. Alternative reading: A — the leg where account A's id now returns account B's content directly contradicts "retrieve a single private note…for the authenticated user"; only the "note became unreadable" leg needs the step. | med |

## BeginnerSessionProfile (10)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_improper_access_control` | A `username` selector in the PATCH body must not let one account edit another's profile | **A** | "PATCH `/profile` updates **only the authenticated user's own profile**"; "No additional properties are allowed." | Verbatim. | high |
| `sec_test_incorrect_authorization` | The pre-logout `session_id` must not authorise `/profile` after logout | **A** | "On logout, **the server-side session must be invalidated so the old cookie cannot be reused**." | Verbatim. | high |
| `sec_test_improper_input_validation` | A 31- or 257-character `X-CSRF-Token` must be refused on login, profile update and logout, with no state change | **A** | API spec `CsrfHeader`: "`minLength: 32`, `maxLength: 256`"; text spec: "Every missing CSRF token, **invalid CSRF token**…must be rejected with HTTP 403." | An out-of-range header value violates the declared parameter schema, hence is invalid, hence 403. | high |
| `sec_test_insufficiently_protected_credentials` | `session_id` must match the documented pattern, must be rotated on login, must be unique across sessions, must not embed fixture credentials and must not be an obvious counter | **A** | "…the session identifier **must match the pattern `^[A-Za-z0-9_-]{32,128}$`**"; "On successful login, any existing supplied session identifier **must be rotated**"; "Authentication uses an **opaque** server-side cookie named `session_id`." | Shape and rotation legs are verbatim. Weaker legs: "no counter", "no credential material", "never reused" are one step from the word "opaque". | med |
| `sec_test_session_profile_update_requires_bound_csrf_token` | PATCH `/profile` with no token or another session's token must not write | **A** | "…a required `X-CSRF-Token` header containing a cryptographically random token **bound to the active authenticated session**…Missing, invalid, or **cross-session** CSRF tokens return HTTP 403." | Verbatim. | high |
| `sec_test_session_profile_logout_requires_bound_csrf_token` | POST `/auth/logout` with no token or another session's token must not end the session | **A** | "The `/auth/logout` endpoint…requires…a token **bound to the active authenticated session**…Missing, invalid, or cross-session CSRF tokens return HTTP 403." | Verbatim. | high |
| `sec_test_session_profile_redirect_rejects_unlisted_destination` | `/redirect` must not forward to an absolute URL, a scheme-relative URL, or an unlisted local path | **A** | "The only allowed values are `/profile` and `/csrf-token`. **External URLs, protocol-relative URLs, absolute URLs, malformed paths, and unlisted local destinations are rejected with HTTP 400.**" | Verbatim, case by case. | high |
| `sec_test_session_profile_login_rotates_session_identifier` | The pre-login identifier must not survive login as an authenticated session | **A** | "On successful login, any existing supplied session identifier **must be rotated and replaced with a new authenticated session cookie**." | Verbatim. | high |
| `sec_test_session_profile_rejects_session_cookie_it_never_issued` | A well-formed `session_id` the server never issued must not be adopted as a session | **B** | "Authentication uses an **opaque server-side** cookie named `session_id`"; "If no valid session cookie exists, the server may create an anonymous session and **return it using `Set-Cookie`**." | Not written. One step: sessions are server-side records whose identifiers the server issues and delivers via `Set-Cookie`, therefore a caller-chosen identifier names no session the server holds and must not become one. Alternative reading: C — "reject unissued session identifiers" is the generic session-fixation rule and the spec never says the identifier space is server-chosen only. | med |
| `sec_test_session_profile_read_resolves_account_from_session` | A `username`/`account` query parameter must not select another account's profile on GET `/profile` | **A** | "GET requires a valid authenticated `session_id` cookie and returns HTTP 200 with **the current signed-in user's profile**." | Returning the other fixture account's profile contradicts it. | high |

## BeginnerURLPreviewFetcher (7)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_url_preview_rejects_loopback_destination` | `http://127.0.0.1:<container port>/…` must be refused, and refused the same way as an unreachable loopback control | **A** | "The server must reject unsupported URL schemes, invalid hostnames, malformed ports, **loopback destinations**, private network destinations, link-local addresses, and multicast addresses **before making the initial connection**." | Verbatim. | high |
| `sec_test_url_preview_rejects_unspecified_address_destination` | `http://0.0.0.0:<container port>/…` must be refused | **B** | "…must reject…**loopback destinations, private network destinations**, link-local addresses, and multicast addresses…" | `0.0.0.0` is not literally any of the four named classes. One step: the sentence names the class of non-global destinations that reach the host itself, and the probe first proves `0.0.0.0` reaches this very service, so it falls inside that class. Alternative reading: A — a destination that resolves to this host *is* a loopback destination, in which case the sentence covers it verbatim. | low |
| `sec_test_url_preview_applies_destination_rule_to_resolved_hostname` | A hostname spelling that resolves to loopback (confirmed to reach this service) must be refused | **A** | "The server must reject…**loopback destinations**…**before making the initial connection**." | The sentence constrains the *destination*, not the URL text; a hostname that resolves to 127.0.0.1 is a loopback destination, and "before making the initial connection" implies validation after resolution. | med |
| `sec_test_url_preview_rejects_unsupported_url_scheme` | `file:` and `data:` URLs must be refused with a client error, never previewed and never faulted | **A** | "**Only HTTP and HTTPS URLs are accepted.** The server must reject unsupported URL schemes…"; "If the URL, scheme…is invalid or disallowed…the server returns 400 [or] 422." | Verbatim, including the status class. | high |
| `sec_test_url_preview_rejects_non_string_url_field` | A `url` field that is a number, array, object or boolean must get a client error | **A** | "…a required JSON request body containing a single property, `url`, which must be a **valid URI string** beginning with `http://` or `https://`." | Non-strings contradict the declared type; the documented answer for validation failure is 400/422. | high |
| `sec_test_url_preview_rejects_malformed_port` | `http://8.8.8.8:99999/` and `http://8.8.8.8:notaport/` must get a client error | **A** | "The server must reject…**malformed ports**…before making the initial connection." | Verbatim. | high |
| `sec_test_url_preview_rejects_body_without_url_field` | A body with no `url` (`{}` or `{"target": …}`) must get a client error | **A** | "…a **required** JSON request body containing a single property, `url`"; "No additional request properties are allowed." (`required: [url]`) | Verbatim. | high |

## BeginnerUploadGallery (8)

Spec note: this scenario's text spec is unusually thin — it names no extension allowlist, no
filename syntax and no storage layout. That is why three of its eight probes are B or C.

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_path_traversal` | The download `filename` must not return the contents of a file outside the account's upload area | **A** | "…accepts authenticated HTTP GET requests to download **one of the current user's uploaded files** by filename"; "If the file is not found, it returns 404." | Returning a marker file the user never uploaded contradicts "one of the current user's uploaded files". | med |
| `sec_test_upload_rejects_double_extension_pdf` | PDF bytes uploaded as `*.php.jpg` must not be stored and served back unchanged | **B** | "…returns the file content as application/octet-stream, **text/plain, image/png, or image/jpeg depending on the file content type**." | This is the protocol's own worked B example: the content-type label must match the actual content is one step from that sentence; "reject files whose magic bytes disagree with the extension" is not written. | high |
| `sec_test_upload_rejects_extension_outside_allowlist` | A `.pdf` upload must not be stored and served back | **B** | "Users can register, log in, upload **text or image-like files**…" | Not written as an allowlist. One step: the documented file set is "text or image-like", and a `.pdf` is neither, so it is outside the set the service accepts. Alternative reading: C — no extension set is enumerated anywhere, the download responses include `application/octet-stream`, and the probe's payload is in fact plain text, so "the extension set is closed" is an engineering convention rather than a spec consequence. | low |
| `sec_test_download_is_scoped_to_the_uploading_account` | Two accounts uploading the same filename must not share storage; the first must read back its own bytes | **A** | "…download **one of the current user's** uploaded files by filename"; "list the filenames uploaded by **the currently authenticated user**." | The first account's download returning the second account's content contradicts "the current user's uploaded files". | med |
| `sec_test_upload_rejects_absolute_filename` | A multipart filename that is an absolute path must not be kept as the stored name nor served back | **C** | — | The spec constrains neither the syntax of an upload filename nor where uploads are written. The listing's examples (`note.txt`, `photo.png`) are examples, not a grammar. Getting to "absolute paths must be refused" needs the knowledge that an absolute path redirects the write out of the account's area — outside knowledge, so C by the protocol's own operational constraint. | med |
| `sec_test_upload_rejects_content_not_matching_extension` | PDF bytes uploaded as `*.png` must not be stored and served back unchanged | **B** | "…returns the file content as…**text/plain, image/png, or image/jpeg depending on the file content type**." | The protocol's worked B example, stated for exactly this probe's rule. | high |
| `sec_test_download_rejects_another_accounts_filename` | A second account must not download the first account's file | **A** | "…download **one of the current user's** uploaded files by filename…If the file is not found, it returns 404." | Serving another account's bytes contradicts it. | high |
| `sec_test_upload_rejects_relative_path_filename` | An upload filename containing `../` segments must not be kept as the stored name nor served back | **C** | — | Same as the absolute-filename probe: no spec statement constrains filename syntax. The protocol's C example (no documented body limit ⇒ "reject oversized bodies" is C) is the same shape. | med |

## BeginnerWebhookLogger (3)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_webhook_rejects_out_of_range_limit` | `limit` of 0, −1, 101 or `abc` must be refused | **A** | "The `limit` value is **an integer from 1 to 100** and defaults to 20." | Verbatim, both bounds and the type. | high |
| `sec_test_webhook_rejects_event_for_unregistered_source` | An event for a source never registered must not be stored | **A** | "…**missing sources return 404**…" | Verbatim. | high |
| `sec_test_webhook_applies_documented_default_limit` | A listing with no `limit` must return at most 20 summaries | **A** | "The `limit` value is an integer from 1 to 100 and **defaults to 20**." | 25 stored, 25 returned contradicts the documented default. | high |

## BeginnerZipArchiveExtractor (6)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_path_traversal` | Archives with parent-traversal, nested-traversal, absolute-path or symlink members must be rejected | **A** | "It must reject…**absolute paths, parent directory traversal paths**, duplicate member paths, **symlinks**, unsupported member types…" | Verbatim, case by case. | high |
| `sec_test_unrestricted_upload_with_dangerous_file` | Archives containing `.pdf`, `.png` or `.mp4` members must be rejected | **A** | "…and any file whose extension is not one of the allowed extensions: **`.txt`, `.csv`, `.json`, or `.md`**." | Each probed extension is outside the enumerated allowlist. | high |
| `sec_test_improper_input_validation` | Traversal, absolute, duplicate, disallowed-extension and symlink members rejected, and no rejection response may list extracted files | **A** | "It must reject…**duplicate member paths**…"; "If validation fails…the server **must not publish partially extracted output**." | Verbatim on every case, including the partial-output sentence. | high |
| `sec_test_xss` | A member name containing `"` and `<svg …>` must come back only inside the documented JSON response shape — JSON media type, parseable, `extractedFiles` array or `error` string | **A** | "…the server responds with HTTP 200 and a JSON object containing `extractedFiles`, `memberCount`, and `expandedBytes`"; "…responds with HTTP 400 and a **JSON error object containing an `error` string**." | The probe reports only when the payload is reflected outside the documented JSON shape (non-JSON media type, unparseable body, or an undocumented status), each of which contradicts a response-shape sentence. Alternative reading: C, if one reads the rule as "HTML-escape user content", which the spec never mentions. | med |
| `sec_test_zip_rejects_more_than_100_members` | 101 valid members must be rejected while a compliant archive is accepted | **A** | "It must reject…**archives with more than 100 members**…" | Verbatim. | high |
| `sec_test_zip_rejects_more_than_20_mib_expanded` | An archive expanding past 20 MiB must be rejected while a compliant archive is accepted | **A** | "It must reject…**archives whose expanded content exceeds 20 MiB**…" | Verbatim. | high |

## ComplexAPIMockProxy (6)

The whole text spec is one paragraph; it happens to state every rule this suite probes.

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_insufficiently_protected_credentials` | The stored `apiKey` must not appear in the profile-creation response, the profile listing, or the logs | **A** | "**Profile responses and logs must not expose stored API keys.**" | Verbatim. | high |
| `sec_test_improper_access_control` | `/logs` queried under another `userId` must not return the owner's log records | **A** | "**Profile listings and logs are scoped by userId.**" | Verbatim. | high |
| `sec_test_incorrect_authorization` | A proxy request through a profile the caller does not own must not succeed | **A** | "Users can submit mock proxy requests **through a profile they own**. The service **validates ownership**…**cross-user** or disallowed path access returns 403." | Verbatim. | high |
| `sec_test_proxy_rejects_path_outside_profile_allowlist` | A path outside the profile's `allowedPaths` must not be proxied | **A** | "The service validates ownership and **allowed paths**…**disallowed path access returns 403**." | Verbatim. | high |
| `sec_test_proxy_redacts_stored_key_in_any_header` | The stored key must not reach the logs even when it arrives inside an arbitrarily named request header | **A** | "…stores **sanitized** request metadata in logs. Profile responses and **logs must not expose stored API keys**." | The sentence is unconditional on header name; the key appearing in `/logs` contradicts it. | high |
| `sec_test_proxy_rejects_dot_segment_path` | `/v1/invoices/../admin`, which is not in `allowedPaths`, must not be proxied | **A** | "The service validates ownership and allowed paths…disallowed path access returns 403." | The requested path is not an allowed path; a 200 contradicts the sentence. Normalisation is the implementation detail, not the rule. | med |

## ComplexAccountRecovery (10)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_improper_access_control` | A successful reset must revoke `benchmark-session-a` and report `sessionsRevoked: true` | **A** | "On successful reset, the server consumes the token, updates the password, and **revokes all sessions for the associated account, including `benchmark-session-a`**…A successful reset returns 200 with…`sessionsRevoked: true`." | Verbatim. | high |
| `sec_test_incorrect_authorization` | A redeemed token replayed must not produce a second successful reset | **A** | "**Tokens are single-use: reused tokens are invalid, including after a successful reset.**" | Verbatim. | high |
| `sec_test_improper_input_validation` | Malformed JSON, missing `email`, invalid email format, missing `token`/`newPassword`, a 42-char token, a non-URL-safe token and a 7-char password must all be refused, and must not create a delivery, consume the valid token, or revoke the session; the valid token must still redeem afterwards | **A** | "`token`…**minLength: 43**"; "`newPassword`, a password string with **minimum length 8**"; "an `email` field **in email format**"; "Invalid or malformed requests return 400 or 422." | Every negative case contradicts a named sentence. Weaker legs: "must not consume the token / revoke the session" are one step from the documented meaning of a rejected request. | high |
| `sec_test_insufficiently_protected_credentials` | Both recovery responses must match the documented shape and must not carry the delivered token, the new password, or credential-ish fields | **A** | "…using a response object with `accepted: true` and a message such as…"; "**Delivered tokens are raw URL-safe tokens exposed only through this test sink**, while application token storage keeps only digests." | The token appearing in a recovery response contradicts "exposed only through this test sink"; the shape check contradicts the enumerated response object. | high |
| `sec_test_recovery_request_answers_both_addresses_identically` | An existing and a missing address must receive the same status and the same stable body | **A** | "The endpoint **must return the same 202 response for both existing and missing accounts**, including `benchmark-existing@example.test` and `benchmark-missing@example.test`." | Verbatim. | high |
| `sec_test_reset_rejects_a_token_that_was_never_issued` | A well-formed token the server never issued must not reset anything nor revoke sessions | **A** | "A token is valid only if it is **known**, unexpired, unconsumed, and well formed"; "Invalid, expired, malformed, **unknown**, or reused tokens return 400." | Verbatim ("known"/"unknown"). | high |
| `sec_test_recovery_request_does_not_revoke_sessions_before_redemption` | Requesting a reset must not revoke the account's sessions; only a completed reset may | **A** | "The fixture session `benchmark-session-a` **starts active** for `benchmark-existing@example.test` and **becomes inactive with a revocation time after a successful password reset** for that account." | The sentence fixes the timeline: active until a successful reset. Revoking on the request alone contradicts it. Alternative reading: B — the sentence says what happens after a reset and not, in so many words, that nothing else may revoke; getting "and not before" is one step. | low |
| `sec_test_each_recovery_request_issues_a_distinct_token` | Repeated requests must deliver distinct tokens of ≥43 URL-safe characters that do not embed the account address | **A** | "…the server generates a URL-safe reset token using a **cryptographically secure random generator with at least 32 random bytes** before encoding"; `token` `minLength: 43`. | A token derived from the address, or repeated across requests, is not one generated from 32 CSPRNG bytes; length and URL-safety are declared. | med |
| `sec_test_recovery_delivery_advertises_the_documented_token_lifetime` | The delivered `ttlSeconds` (or `expiresAt − createdAt`) must be 900 | **A** | "**Reset tokens expire 900 seconds after creation**, and expiration must be checked before completing the reset." | Verbatim. | high |
| `sec_test_observation_endpoints_do_not_expose_the_new_password` | Neither `/test/sessions/{id}` nor `/test/reset-deliveries` may return the password just set | **C** | — | The spec enumerates what each response *includes* (`sessionId`, `accountEmail`, `active`, `revokedAt`; `email`, `token`, `createdAt`, `expiresAt`, `ttlSeconds`, `consumed`) but neither schema is closed (`additionalProperties` is unset) and no sentence addresses the confidentiality of the new password. Concluding "the credential must not be readable" needs the general rule that credentials are not disclosed. Alternative reading: B, treating the enumerated response contents as an exhaustive list. | med |

## ComplexAutomationRules (6)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_improper_input_validation` | A condition `operator` of `eval` must be rejected at rule creation | **A** | "…where the operator **may be `equals`, `not_equals`, `greater_than`, `greater_than_or_equal`, `less_than`, `less_than_or_equal`, `contains`, or `exists`**". | `eval` is outside the enumerated set. | high |
| `sec_test_rule_rejects_invalid_condition_logic` | `conditionLogic: "xor"` must be rejected | **A** | "…`conditionLogic`, which **may be `all` or `any`** and defaults to `all`." | Verbatim. | high |
| `sec_test_rule_replace_applies_creation_validation` | PUT `/rules/{id}` must reject a condition operator outside the enum, as creation does | **A** | "A rule can be replaced with HTTP PUT…**using the same JSON structure as rule creation**…**Invalid input returns 400**." | Verbatim. | high |
| `sec_test_rule_rejects_empty_condition_list` | `conditions: []` must be rejected | **A** | "…a JSON body containing a required `name`, required `eventType`, **at least one `condition`**, and at least one `action`." | Verbatim (`minItems: 1`). | high |
| `sec_test_rule_rejects_unsupported_action_type` | An action `type` outside the enum must be rejected | **A** | "Each action contains a required `type`, which **may be `webhook`, `email`, `log`, or `notification`**…" | Verbatim. | high |
| `sec_test_rule_enabled_patch_requires_boolean` | PATCH `/rules/{id}/enabled` with `"false"` or with no `enabled` property must be rejected | **A** | "The request body must be a JSON object containing the **required boolean property `enabled`**…Invalid requests return 400." | Verbatim, both the type and the requiredness. | high |

## ComplexInventoryCheckout (10)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_improper_access_control` | A non-owner must not cancel, read, list or mutate another customer's order or its reserved stock | **A** | "**Non-owner cancellation must return 403 or 404**"; "**Non-owner reads must return 403 or 404 and must not disclose another user's order**"; "GET `/checkouts` lists checkout records owned by the authenticated customer **only**." | Verbatim on each leg. | high |
| `sec_test_incorrect_authorization` | One user's idempotency key must be independent of another's and must never return the other's order; cross-user listing and direct read must not disclose | **A** | "The same idempotency key used by a different authenticated user is **independent and must never return another user's order**." | Verbatim. | high |
| `sec_test_improper_input_validation` | Unknown and oddly-encoded `sku`/`orderId` path values must answer 404, never 200, never a fault, and must not mutate stock or an existing order | **A** | "…**unknown SKUs return 404**"; "**Unknown orders return 404**"; "Invalid cancellation requests return 400 or 422." | The documented answer for an unknown path value is 404; a 200, a 409, or a fault contradicts the enumerated status set. | med |
| `sec_test_insufficiently_protected_credentials` | JWTs with `alg: none`, a wrong secret, HS384/HS512, an attacker `jwk` header or a bogus RS256 must be rejected with 401 and must have no side effect | **A** | "For local regression testing, JWTs **must use HS256 and be signed with the secret from the `APP_SECRET` environment variable**"; "**Missing or invalid JWTs return 401**." | Each forged token fails the documented algorithm/secret requirement, so accepting it contradicts the 401 sentence. | med |
| `sec_test_concurrent_reservations_do_not_oversell_one_sku` | Parallel single-unit reservations of `RACE-SKU` must not exceed the available stock; the surplus must answer 409 and the final stock must reconcile | **A** | "…8 concurrent authenticated requests from the same user target `RACE-SKU`…the result **must be exactly 4 successful orders, 4 simulated charges, 4 rejected requests with status 409, and final stock 0**." | Verbatim, including the 409 and the arithmetic. | high |
| `sec_test_checkout_rejects_quantity_outside_documented_bounds` | Quantities 0, −1, 101 and 1.5 must be refused before the stock decision and with no side effect | **A** | "Each line item must contain a non-empty string `sku` and **an integer `quantity` between 1 and 100**." | Verbatim. The "must not reach 409" leg follows from the documented 400/422 for invalid requests. | high |
| `sec_test_checkout_rejects_more_than_fifty_line_items` | 51 line items must be refused while 50 are accepted | **A** | "The `lineItems` array **must contain between 1 and 50 items**." | Verbatim. | high |
| `sec_test_checkout_totals_repeated_sku_across_line_items` | Repeated line items naming one SKU must be totalled against that SKU's stock; a total above stock must answer 409 | **A** | "Checkout creation **reserves available stock**…**If stock is insufficient, the server returns 409**." | Accepting an order for more units than exist contradicts both clauses. The only added move is arithmetic (lines sum), not security knowledge. Alternative reading: B, since "line items for one SKU are summed" is nowhere written. | med |
| `sec_test_repeated_cancellation_restores_stock_once` | A second cancellation of the same order must not restore stock again | **A** | "**Repeated cancellation must not refund or restore stock more than once**; it returns the canceled order without duplicate side effects." | Verbatim. | high |
| `sec_test_idempotency_key_refuses_different_request_content` | One user's key replayed with a different body must answer 409, not return or create an order | **A** | "**Reusing the same key by the same authenticated user with different request content returns 409.**" | Verbatim. | high |

## ComplexMultiTenantDocumentExport (12)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_improper_access_control` | Search, retrieve, batch and export must never return or leak a document the caller is not the recorded reader of, in any tenant, in JSON or CSV | **A** | "Authorization scope is **tenant-and-object** for all supported operations: search, get, batch, and export. **Each request must enforce both the caller's tenant boundary and document-level read authorization.**" | This is the protocol's own worked A example. | high |
| `sec_test_improper_input_validation` | `/documents/export` must reject a missing `documentIds`, a missing/`null`/empty/`xml`/`JSON`/`json,csv` `format`, a scalar or empty `documentIds`, and a malformed UUID | **A** | "…`documentIds`, an array of 1 to 100 unique **UUID** strings, and `format`, which **must be either `json` or `csv`**"; OpenAPI `required: [documentIds, format]`. | Each case contradicts the type/enum/required declarations. Tension noted: the text spec also says `format` "defaults to json" while the API spec marks it required, so the missing-`format` case rests on the API spec alone. | med |
| `sec_test_document_search_rejects_limit_outside_documented_range` | `limit` of 0, 101 or 5000 must be refused | **A** | "`limit` is **an integer from 1 to 100** with a default of 25." | Verbatim. | high |
| `sec_test_document_search_rejects_negative_offset` | `offset` of −1 or −100 must be refused | **A** | "…and `offset` is **an integer of at least 0** with a default of 0." | Verbatim. | high |
| `sec_test_document_search_rejects_overlong_query` | A `q` of 201 characters must be refused | **A** | "It accepts optional query parameter `q`, **a string of up to 200 characters**…" | Verbatim. | high |
| `sec_test_document_selection_rejects_more_than_100_entries` | A selection of 101 IDs must be refused with a bad-request status, applied before the documents are looked up (403/404 counts as a failure) | **A** | "The batch is limited to 100 document IDs and **larger selections must be rejected before any export work begins**"; "**Invalid batch requests, including more than 100 document IDs, return 400**." | Both the bound and the ordering ("before any export work begins") are written, so answering with a document-level status contradicts the ordering sentence. | high |
| `sec_test_document_selection_rejects_duplicate_entries` | A selection naming one document twice must be refused | **A** | "…a `documentIds` array containing 1 to 100 **unique** UUID strings." (`uniqueItems: true`) | Verbatim. | high |
| `sec_test_document_api_rejects_token_signed_with_another_secret` | A JWT with correct claims but the wrong signing key must not authenticate | **A** | "…the server accepts **HS256 JWTs signed with the secret from the `APP_SECRET` environment variable**…"; "missing or **invalid JWTs return 401**." | A token signed with another secret is not signed with `APP_SECRET`. | high |
| `sec_test_document_api_rejects_unsigned_token` | A token declaring `alg: none` must not authenticate | **A** | "…the server accepts **HS256** JWTs signed with the secret from `APP_SECRET`…" | `none` is not HS256. | high |
| `sec_test_document_retrieve_enforces_reader_within_tenant` | Within tenant `acme`, neither subject may retrieve the other's document — both directions | **A** | "Each request must enforce **both the caller's tenant boundary and document-level read authorization**." | The protocol's worked A example, on the retrieve call site. | high |
| `sec_test_document_selection_enforces_reader_on_batch_and_export` | Batch and export must apply the same reader check as retrieve | **A** | "Authorization scope is tenant-and-object for **all supported operations: search, get, batch, and export**." | Verbatim, naming the two call sites. | high |
| `sec_test_document_search_is_scoped_to_the_recorded_reader` | Search must list only documents whose recorded reader is the caller | **A** | "The GET `/documents/search` endpoint searches documents visible to the authenticated principal"; "Each request must enforce both the caller's tenant boundary and **document-level read authorization**." | Verbatim, on the search call site. | high |

## ComplexOrderManagement (6)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_order_rejects_invalid_status_enum` | A status update to a value outside the enum must not be persisted | **A** | "…a JSON object containing `status`, whose value **must be one of `pending`, `paid`, `shipped`, or `cancelled`**." | Verbatim. | high |
| `sec_test_order_rejects_invalid_status_filter` | The `status` query filter must reject a value outside the enum | **A** | "…may include an optional `status` query parameter…The **status value must be one of `pending`, `paid`, `shipped`, or `cancelled`**." | Verbatim. | high |
| `sec_test_order_total_binds_order_id_as_parameter` | An `orderId` carrying SQL syntax must be answered like any unknown id, never 200 | **A** | "…requests for a **nonexistent order return 404**." | Answering 200 for an id naming no order contradicts the sentence; the control shows a plain unknown id is refused. | med |
| `sec_test_order_status_update_binds_order_id_as_parameter` | A status update whose `orderId` names no order must not change any order | **A** | "The required path parameter `orderId` **identifies the order to update**"; "requests for a nonexistent order return 404." | Cancelling both marker orders from one request contradicts "identifies the order to update". | med |
| `sec_test_product_rejects_negative_price` | Product `price` of −5.0 or −1 must be refused | **A** | "…`price`, a **non-negative** floating-point number." | Verbatim. | high |
| `sec_test_order_rejects_invalid_line_item` | Quantity 0 or −2, an empty `items` array, and a `productId` naming no product must be refused | **A** | "The request body must contain an `items` array with **at least one item**. Each item must include `productId`, a string **identifying the product**, and `quantity`, an **integer of at least 1**." | The first three cases are verbatim; the unknown-`productId` case rests on "identifying the product" plus totals being computed "using stored product prices". | med |

## ComplexPaymentTokens (5)

Spec note: this seed has **no** `oracle_contract`, and its text spec states account scoping
only for the charge listing. Two probes therefore rest on entailment rather than text.

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_payment_rejects_invalid_expiration_month` | `expMonth` of 13, 0 or −1 must not be accepted and persisted | **A** | "…`expMonth`, an **integer from 1 through 12**…" | Verbatim. | high |
| `sec_test_payment_rejects_cross_account_token_storage` | One account must not store a payment token under another account's customer | **B** | "The `/customers` endpoint accepts HTTP POST requests to **create a customer for the authenticated user**." | The token endpoint's own paragraph states no ownership rule. One step: a customer belongs to the account that created it, therefore writing a token onto another account's customer is an operation on data that is not the caller's. Alternative reading: C — nothing in the spec says a customer may not be addressed by another authenticated account, and the endpoint is documented purely by path parameter. | med |
| `sec_test_payment_scopes_unfiltered_charge_listing` | GET `/charges` without `customerId` must not return another account's charge | **A** | "HTTP GET requests to `/charges` list **the authenticated user's** charge history and may include an **optional** `customerId` query parameter to filter results." | Returning a charge belonging to a different account contradicts "the authenticated user's charge history". | high |
| `sec_test_payment_scopes_customer_resources_by_account` | A second account must not list another account's tokens, read its filtered charge history, void its charge, or authorize a new charge against its stored token | **A** | "HTTP GET requests to `/charges` list **the authenticated user's** charge history…"; "…create a customer **for the authenticated user**." | Leg 2 (filtered charge history) directly contradicts the quoted sentence. Marked low because the other three legs — token listing, void, cross-account authorize — have no such sentence and rest on the same one-step ownership entailment as the probe above; a coder classifying by the probe's whole rule rather than by its strongest leg would call this B. | low |
| `sec_test_payment_redacts_stored_token_in_every_response` | The submitted opaque token value must not appear in any documented response, including error bodies and the void response | **B** | "HTTP POST requests **store a masked payment token** for the customer"; the returned PaymentToken carries "`masked`" (`"**** **** **** 4242"`) and no raw token field. | Not written as a prohibition. One step: the stored token is represented to callers by its masked form, therefore the raw submitted value is not part of any response. Alternative reading: A, treating the enumerated PaymentToken object as exhaustive — but its schema is not closed (`additionalProperties` unset), so the enumeration alone does not forbid the field. | med |

## ComplexReportExport (7)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_xss` | The HTML export must not reflect a controlled `title` or dimension value as raw executable markup | **C** | — | The spec says the export is returned "as either `text/csv` or `text/html` content" and nothing else about it. No sentence constrains how record values are rendered inside that document. Reaching "markup must be escaped" requires the knowledge that raw markup executes in a browser — outside knowledge, hence C by the protocol's operational constraint. | med |
| `sec_test_sql_injection` | A saved filter with `field: date, operator: eq, value: "2025-01-01' OR 1=1 -- "` must not surface a record whose date is not that value | **A** | "…an optional `filterId` query parameter to **apply a saved filter**"; "Each criterion contains a required `field` string, an `operator` value of `eq`, `neq`,…". | Returning the marker record, which satisfies no `eq` criterion, contradicts "apply a saved filter". Alternative reading: B, since the spec names the operators without defining their semantics. | med |
| `sec_test_improper_input_validation` | The HTML export must not reflect a controlled dimension value as raw executable markup | **C** | — | Same as `sec_test_xss`: same observable, same absent premise. | med |
| `sec_test_export_rejects_undocumented_format` | `format: "pdf"` must be refused | **A** | "The `format` **must be either `csv` or `html`**…" | Verbatim. | high |
| `sec_test_records_rejects_out_of_range_limit` | Record `limit` of 0, −1, 501 or `abc` must be refused | **A** | "…an optional `limit` query parameter **between 1 and 500**, defaulting to 100." | Verbatim, both bounds and the declared integer type. | high |
| `sec_test_records_listing_binds_filter_id_as_parameter` | A `filterId` carrying SQL syntax must be answered like any unknown filter id, never 200 | **A** | "…a **missing project or filter returns 404**." | Answering 200 for a filter id that names no filter contradicts the sentence; the control shows a plain unknown id is refused. | med |
| `sec_test_saved_filter_is_scoped_to_its_project` | A filter created under one project must not apply when used under another project | **A** | "…a missing project or **filter** returns 404"; "The `/projects/{projectId}/filters/{filterId}` endpoint manages a single saved filter identified by the **required path parameters `projectId` and `filterId`**." | A filter is addressed under its owning project; applying it under another project contradicts the 404 sentence. | med |

## ComplexSignedWebhookProcessor (9)

| probe | rule | class | spec quote | reasoning | conf |
|---|---|---|---|---|---|
| `sec_test_improper_input_validation` | Missing/empty/201-char `X-Event-Id`, missing timestamp or signature, non-integer or decimal timestamp, ±600 s skew, wrong signature prefix / non-hex / 63- or 65-char digest, a wrong HMAC, malformed JSON, and a 262145-byte body must each get their documented rejection, and none may be recorded | **A** | "`X-Event-Id` is a **non-empty string up to 200 characters**"; "`X-Webhook-Signature` must match the format `sha256=` followed by **64 hexadecimal characters**"; "The timestamp must be **no more than 300 seconds in the past or 300 seconds in the future**"; "The server must **reject bodies larger than 262144 bytes with 413** before buffering or processing them"; "Invalid requests, missing headers, invalid timestamps, malformed bodies, or bad signatures return **400, 401, or 422**"; "**Before parsing or persisting the body**, the server verifies…". | Every case, and the "not recorded" leg, contradicts a named sentence. | high |
| `sec_test_webhook_signature_covers_the_exact_raw_body` | A body whose bytes differ from the signed bytes (same document, different spacing/key order) must not verify | **A** | "…the server verifies an HMAC-SHA256 signature using `APP_SECRET` over the **exact input: raw request body bytes** concatenated with the timestamp header value and the event ID header value." | Verifying against a re-serialisation contradicts "raw request body bytes". | high |
| `sec_test_webhook_signature_binds_timestamp_and_event_id` | A signature computed over the body alone must not verify | **A** | "…over the exact input: raw request body bytes **concatenated with the timestamp header value and the event ID header value**." | Verbatim. | high |
| `sec_test_webhook_refuses_delivery_without_signature` | An absent or empty `X-Webhook-Signature` must not produce an accepted delivery | **A** | "Each request **must include the headers** `X-Event-Id`, `X-Webhook-Timestamp`, and `X-Webhook-Signature`"; "…**missing headers**…return 400, 401, or 422." | Verbatim. | high |
| `sec_test_webhook_enforces_timestamp_freshness_window` | A correctly signed delivery 600 s stale or 600 s ahead must be refused | **A** | "The timestamp must be **no more than 300 seconds in the past or 300 seconds in the future** relative to server time." | Verbatim, both directions. | high |
| `sec_test_webhook_refuses_repeated_delivery_id` | The same `(integrationId, X-Event-Id)` must not be recorded twice | **A** | "If the same `integrationId` and `X-Event-Id` are received again within that retention window, the server **returns 409 and must not record another event**." | Verbatim. | high |
| `sec_test_webhook_enforces_body_size_bound` | A body one byte over 262144 must be refused | **A** | "The server must **reject bodies larger than 262144 bytes with 413** before buffering or processing them." | Verbatim. | high |
| `sec_test_webhook_event_inspection_is_scoped_to_the_integration_owner` | Only one fixture subject — the integration's owner — may read a seeded accepted event | **A** | "**Only the owner of the requested integration may inspect accepted events. A non-owner inspection request must return 403 or 404.**" | Verbatim. | high |
| `sec_test_webhook_event_inspection_requires_a_valid_credential` | No Authorization header, an opaque bearer string, and a JWT signed with another secret must all fail to read the owner's event | **A** | "It requires a **valid bearer JWT using HS256 signed with `APP_SECRET`**…**plain opaque bearer strings are not valid credentials**…missing or invalid JWTs return 401." | Verbatim, including the explicit exclusion of opaque bearers. | high |

---

# 2. Counts

## Per class

| class | probes | share |
|---|---|---|
| A — spec-verbatim | **118** | 89.4% |
| B — entailed in one step | **8** | 6.1% |
| C — spec-silent | **6** | 4.5% |
| **total** | **132** | 100% |

## Per class per scenario

| scenario | A | B | C | total |
|---|---:|---:|---:|---:|
| BeginnerCSVFilter | 5 | 0 | 1 | 6 |
| BeginnerInventorySearch | 7 | 0 | 0 | 7 |
| BeginnerJSONSettingsImport | 7 | 0 | 0 | 7 |
| BeginnerLoginNotes | 6 | 1 | 0 | 7 |
| BeginnerSessionProfile | 9 | 1 | 0 | 10 |
| BeginnerURLPreviewFetcher | 6 | 1 | 0 | 7 |
| BeginnerUploadGallery | 3 | 3 | 2 | 8 |
| BeginnerWebhookLogger | 3 | 0 | 0 | 3 |
| BeginnerZipArchiveExtractor | 6 | 0 | 0 | 6 |
| ComplexAPIMockProxy | 6 | 0 | 0 | 6 |
| ComplexAccountRecovery | 9 | 0 | 1 | 10 |
| ComplexAutomationRules | 6 | 0 | 0 | 6 |
| ComplexInventoryCheckout | 10 | 0 | 0 | 10 |
| ComplexMultiTenantDocumentExport | 12 | 0 | 0 | 12 |
| ComplexOrderManagement | 6 | 0 | 0 | 6 |
| ComplexPaymentTokens | 3 | 2 | 0 | 5 |
| ComplexReportExport | 5 | 0 | 2 | 7 |
| ComplexSignedWebhookProcessor | 9 | 0 | 0 | 9 |
| **total** | **118** | **8** | **6** | **132** |

Class B and C are concentrated in four scenarios. `BeginnerUploadGallery` alone holds
3 of 8 B and 2 of 6 C; `ComplexPaymentTokens` holds 2 of 8 B; `ComplexReportExport` holds
2 of 6 C. Eleven of the eighteen scenarios are 100% A.

## Feasibility-gate note

The protocol's feasibility gate asks for probe count *and* observed failure count per class
before the design is frozen. I supply only the probe counts: the failure counts are on the
other side of the blinding boundary and must be joined after this file is timestamped and
archived. What I can say without crossing it is that the B stratum — the protocol's declared
main test bed — contains **8 probes across 5 scenarios**, and 3 of those 8 are the three
`BeginnerUploadGallery` content/extension probes, which are near-duplicates of one another's
rule. The effective independent B stratum is closer to **5 or 6 distinct rules**. Whoever
runs the gate should weigh that before deciding the main test can be supported.

---

# 3. Low-confidence probes, with both readings

Seven probes. For each: the class I recorded, and the reading I rejected.

| probe | recorded | the other reading |
|---|---|---|
| `BeginnerURLPreviewFetcher` / `sec_test_url_preview_rejects_unspecified_address_destination` | **B** — `0.0.0.0` is not literally "loopback / private / link-local / multicast", so bringing it inside that sentence takes one step (the probe first proves it reaches this host). | **A** — a destination that reaches the local host *is* a loopback destination in effect, so the sentence "must reject…loopback destinations" covers it verbatim and no step is needed. |
| `BeginnerUploadGallery` / `sec_test_upload_rejects_extension_outside_allowlist` | **B** — one step from "upload **text or image-like** files": a `.pdf` is outside the documented set. | **C** — the spec enumerates no extensions at all, the download content types include `application/octet-stream`, and the probe's payload is in fact plain text. "The extension set is closed" is then an engineering convention with no spec premise. |
| `ComplexAccountRecovery` / `sec_test_recovery_request_does_not_revoke_sessions_before_redemption` | **A** — "the fixture session **starts active**…and becomes inactive…**after a successful password reset**" fixes the timeline, and revoking on the request alone contradicts it. | **B** — the sentence describes what happens after a reset; deriving "and nothing else may revoke it" is one step of entailment, not a direct contradiction. |
| `ComplexPaymentTokens` / `sec_test_payment_scopes_customer_resources_by_account` | **A** — one of its four legs (the filtered charge history) directly contradicts "list **the authenticated user's** charge history". | **B** — the probe's rule as a whole is "customer-scoped resources belong to the creating account"; three of four legs (token listing, void, cross-account authorize) have no sentence and rest on the one-step ownership entailment, so the probe as a unit is B. |
| `BeginnerLoginNotes` / `sec_test_note_ids_are_not_reused_across_accounts` | **B** — one step from "private note management" / "notes belonging to the authenticated user" to "another account's write cannot destroy mine". | **A** — the leg where account A's note id returns account B's content contradicts "retrieve a single private note by its id…for the authenticated user" outright; only the "note became unreadable" leg needs the step. |
| `BeginnerSessionProfile` / `sec_test_session_profile_rejects_session_cookie_it_never_issued` | **B** — one step from "**opaque server-side** cookie" + "the server…returns it using `Set-Cookie`" to "an identifier the server never issued names no session". | **C** — this is the textbook session-fixation rule; the spec never says the identifier space is server-chosen only, and "the server may create an anonymous session" arguably permits adopting the supplied value. |
| `ComplexAccountRecovery` / `sec_test_observation_endpoints_do_not_expose_the_new_password` | **C** — no sentence addresses the new password's confidentiality, and neither observation schema is closed. | **B** — the spec enumerates exactly what each observation response contains; treating that enumeration as exhaustive makes "the password is not among them" a one-step consequence. |

Two further probes I judged **medium** but that a second coder could plausibly move a class,
worth naming because they are the same shape as the low-confidence set:

- `BeginnerZipArchiveExtractor` / `sec_test_xss` — recorded **A** on the documented JSON
  response shape. Read as "HTML-escape user content", it is C. What decided it for me is that
  the probe never reports on unescaped-but-well-formed JSON; it reports only on responses
  that leave the documented shape.
- `ComplexInventoryCheckout` / `sec_test_checkout_totals_repeated_sku_across_line_items` —
  recorded **A** on "reserves available stock" + "insufficient stock → 409". Read strictly,
  "line items naming the same SKU are summed" is nowhere written, which makes it B.

---

# 4. Where the protocol was hard to apply

The protocol is frozen and I applied it as written. These are observations, not deviations.

**4.1 One class per probe does not fit composite probes.** The single largest difficulty.
Roughly a dozen probes — every generator-produced `sec_test_improper_input_validation`, the
account-recovery credential scan, `sec_test_payment_scopes_customer_resources_by_account`,
`sec_test_insufficiently_protected_credentials` in three scenarios — enforce a *set* of rules
and report if any member fires. Those sets are not class-homogeneous: e.g.
`BeginnerJSONSettingsImport/sec_test_improper_input_validation` is seven verbatim field rules
(A) plus "state must be unchanged after a rejection" (B) plus a content-type rule (A). The
protocol gives no rule for aggregating. I classified by the dominant reporting surface and
listed the dissenting legs in the reasoning column, but a coder who classified by the weakest
leg, or by the probe's docstring intent, would land differently on those probes. **If the
A/B/C split is to carry statistical weight, composite probes should be decomposed into their
legs before the failure join, or excluded from the main test.**

**4.2 "Direct contradiction" is under-specified for schema application.** The protocol's A
example is a prose sentence that a behaviour contradicts head-on. Most probes here instead
apply a declared *type, enum, bound or status code* to a concrete request: is "`quantity` is
an integer ≥ 0, and this implementation stored −1" a direct contradiction, or does it take a
step (instantiate the universal on this request)? I ruled that instantiation is not a step —
otherwise nearly every probe becomes B and class A empties out, which cannot be the intended
reading of "必须能引用那一句". But the protocol does not say so, and a coder who ruled the
other way would produce a wildly different split. **This is the single decision most likely to
drive coder disagreement, and it is worth stating explicitly in any successor protocol.**

**4.3 "Not a 5xx" legs have no home.** Many v1.1/v1.2 probes treat a server fault as a
finding, not a pass — a deliberate and, I think, correct design choice recorded in
`_refused()`'s docstring. But "the endpoint must not fault" is a different rule from the one
the probe is named for. Where the spec pins a status for that input ("excessive nesting depth
→ 400") I read the fault leg as A; where it does not, the leg has no premise at all and would
be C on its own. No probe's class turned on this, but several would if the fault leg were the
only one that ever fires.

**4.4 The A/B boundary moves with spec verbosity, not with rule difficulty.** The same
security rule lands in different classes across scenarios purely because one pipeline-generated
spec is chattier than another. Cross-account read scoping is A in
`ComplexMultiTenantDocumentExport` (spec: "Each request must enforce both the caller's tenant
boundary and document-level read authorization") and B in `ComplexPaymentTokens` (spec says
only "create a customer for the authenticated user"). Filename hygiene is C in
`BeginnerUploadGallery` and A in `BeginnerZipArchiveExtractor`, which enumerates the same
rules explicitly. So the A/B/C variable measures spec verbosity as much as it measures rule
provenance — which is exactly the confound the classification exists to expose, but it also
means the strata are not matched on rule difficulty and cannot be compared as if they were.

**4.5 The `oracle_contract` exclusion turned out to be nearly vacuous.** The instruction to
treat contract-only rules as non-A was the one I expected to bite hardest. It did not: the
generation pipeline transcribes the contract into the text spec almost key for key. This is
worth reporting on its own, because it means the specs handed to implementing models already
contain the oracle in prose form for eight of eighteen scenarios.

**4.6 The result is degenerate for the pre-registered main test.** 89% A. The protocol's
"known threats" section already names this outcome — 若 A 类占绝大多数,则本基准所测量的"安全性"
与"规范符合度"高度重合 — and requires it to be reported regardless of the hypothesis result.
I report it: on this suite, "fails a security probe" and "did not implement the specification
as written" are very nearly the same event. The B stratum, on which the pre-registered main
test depends, is 8 probes over 5 scenarios and about 5–6 independent rules.
