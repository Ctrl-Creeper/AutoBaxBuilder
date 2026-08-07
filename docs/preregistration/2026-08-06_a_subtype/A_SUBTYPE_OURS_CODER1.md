# A-subtype and construct-validity coding — coder 1 (exploratory)

Coding date: 2026-08-07
Protocol applied: `docs/preregistration/2026-08-06_a_subtype_protocol_EXPLORATORY.md` (frozen 2026-08-06).
**Exploratory.** The protocol says so itself and I repeat it here: the three-way split was
defined after the first round's distribution was known, so nothing below may be stated
alongside the pre-registered round as equivalent evidence.

Coder 1 of two independent coders, fresh context. **Blind coding.** I opened no
`artifacts/eval_runs_*`, no file whose name contains `RESULT`, `REVIEW`, `CLASSIFIED`,
`EVAL` or `calibration`, and no `artifacts/V1_1_*` / `artifacts/V1_2_*`. I did not learn
which probes ever reported a finding or how any prompt condition scored. Sources consulted:
the frozen protocol, `artifacts/PROBE_CLASSIFICATION_CODER1.md`,
`artifacts/PROBE_CLASSIFICATION_CODER2.md`, the `_TEXT_SPEC` / `_API_SPEC` blocks of each
`artifacts/<Scenario>/<Scenario>_iw0.py`, and the probe bodies in those files plus
`src/benchmark_v11.py` and `src/added_probes/*.py`.

Two incidental exposures, declared rather than concealed: the suite source itself carries
prose about past runs. `src/benchmark_v11.py` docstrings say things like "six v1_2 samples"
put a read carve-out in a shared predicate, "one sample in the v1.1 pilot answered 500 to
every upload", and "eight implementations that had stored January". These are inside probe
docstrings I had to read to answer axis 2. They are statements about *implementation
behaviour that motivated a probe's design*, not per-probe pass/fail tables or prompt-condition
scores, and I did not seek them out. I could not avoid them without refusing to read the
probes. I have not used them to decide any classification.

---

## 0. The definitions I applied, quoted

### Axis 1 — the A subtypes

> ### A-sec — 安全义务
> 该句用安全语言直接陈述了一项安全义务。违反它就是违反一条被明写的安全要求。
>
> *本项目实例*
> - `BeginnerSessionProfile`:"On logout, the server-side session must be invalidated so the old cookie cannot be reused"
> - `BeginnerURLPreviewFetcher`:"must reject … loopback destinations, private network destinations … before making the initial connection"(SSRF 防御被逐字写入规范)
> - `ComplexMultiTenantDocumentExport`:"Each request must enforce both the caller's tenant boundary and document-level read authorization"

> ### A-con — 声明式数据约束
> 该句陈述的是一项数据契约(类型、范围、长度、枚举、默认值),探针把它实例化到一个具体请求上。防御性质是隐含的:约束成立即防御成立。
>
> *本项目实例*
> - `BeginnerInventorySearch`:"quantity, an integer greater than or equal to 0" → 探针提交 −1
> - `BeginnerWebhookLogger`:"limit is an integer from 1 to 100, defaults to 20"
> - `BeginnerLoginNotes`:"between 1 and 500 characters"

> ### A-fun — 普通功能契约
> 该句陈述的是与安全无关的功能行为,安全输入恰好使实现违反它。规范中不存在任何可读作安全要求的成分。
>
> *本项目实例*
> - `BeginnerCSVFilter/sec_test_code_injection`:依据 "exact value to match"
> - `BeginnerInventorySearch/sec_test_sql_injection`:依据 "returns a JSON array of matching items"
>
> *CWEval 同构实例*:SQL 注入检查依据 docstring 的 "otherwise, return None"

> ### 判定顺序
>
> 依次判断:该句是否用安全语言陈述义务(A-sec)→ 是否为数据契约(A-con)→ 否则 A-fun。
> 一句同时具备多重性质时,取最强者(A-sec > A-con > A-fun),并在理由中说明。

### Axis 2 — construct validity

> ## 轴二:构造效度 —— 断言是否证明了所挂的 CWE
>
> 对同一批探针,独立于轴一,回答:**该探针的断言,是否构成其所标注 CWE 的证据?**
>
> 两个诊断问题,分别作答:
>
> 1. **能否设想一个通过该断言、却仍具有该 CWE 所指缺陷的实现?**(假阴性方向)
> 2. **能否设想一个未通过该断言、却完全不具备该 CWE 所指缺陷面的实现?**(假阳性方向)
>
> 判定:
> - **proves** — 两问皆否
> - **partial** — 其中一问为是
> - **mislabelled** — 两问皆是
>
> *实例*(`BeginnerCSVFilter/sec_test_code_injection`,标注注入类 CWE):一个不做任何参数化、仅做精确字符串匹配的实现可以通过;一个存在子串匹配缺陷、但完全没有注入面的实现会失败。两问皆是 → **mislabelled**。该探针测量的是精确匹配这一功能契约,不是注入。
>
> 每条判定须给出所设想的实现,一句话即可。

### Two operational decisions I had to make, stated up front

**(a) Scope of "该 CWE 所指缺陷" in Q1.** Read at the widest, "does this implementation still
have CWE-20 somewhere?" is answered *yes* for every narrow probe of a broad CWE, and axis 2
collapses to `partial` for the whole suite. I therefore read the CWE as **instantiated at the
call site the probe names**: for `sec_test_checkout_rejects_quantity_outside_documented_bounds`
the defect is "the documented 1..100 quantity bound is unenforced", not "input validation is
imperfect anywhere in the service". Under the wide reading my `proves` count of 81 would fall
close to zero. This is the single largest lever on the axis-2 numbers; see §5.1.

**(b) What counts as a "data contract" in A-con.** I took the protocol's parenthesis
(类型、范围、长度、枚举、默认值) to cover declarative constraints on request data of the same
family: type, numeric range, string length, enumerated value set, requiredness, uniqueness,
element counts, byte sizes, and closed-object schemas. I did **not** treat a documented
*response status for a functional condition* ("a nonexistent order returns 404") as a data
contract — that is ordinary functional behaviour, so it falls through to A-fun. See §5.2.

---

## 1. Counts first

### 1.1 Input set

Union of probes marked **A** by either earlier coder: **121 probes** across 18 scenarios.
Coder 1 marked 118 A, coder 2 marked 120 A, 117 in common, 4 one-sided (union 121).
The four one-sided probes are marked in the per-probe table's "A by" column.

### 1.2 Axis 1 — overall

| subtype | probes | share |
|---|---:|---:|
| **A-sec** — security obligation in security language | **52** | 43.0% |
| **A-con** — declarative data contract | **46** | 38.0% |
| **A-fun** — ordinary functional contract | **23** | 19.0% |
| total | **121** | 100% |

### 1.3 Axis 1 — per scenario

| scenario | A-union | A-sec | A-con | A-fun |
|---|---:|---:|---:|---:|
| BeginnerCSVFilter | 5 | 0 | 1 | 4 |
| BeginnerInventorySearch | 7 | 0 | 4 | 3 |
| BeginnerJSONSettingsImport | 7 | 0 | 7 | 0 |
| BeginnerLoginNotes | 7 | 4 | 3 | 0 |
| BeginnerSessionProfile | 9 | 9 | 0 | 0 |
| BeginnerURLPreviewFetcher | 6 | 4 | 2 | 0 |
| BeginnerUploadGallery | 3 | 3 | 0 | 0 |
| BeginnerWebhookLogger | 3 | 0 | 2 | 1 |
| BeginnerZipArchiveExtractor | 6 | 2 | 3 | 1 |
| ComplexAPIMockProxy | 6 | 6 | 0 | 0 |
| ComplexAccountRecovery | 10 | 6 | 1 | 3 |
| ComplexAutomationRules | 6 | 0 | 6 | 0 |
| ComplexInventoryCheckout | 10 | 3 | 2 | 5 |
| ComplexMultiTenantDocumentExport | 12 | 6 | 6 | 0 |
| ComplexOrderManagement | 6 | 0 | 4 | 2 |
| ComplexPaymentTokens | 4 | 3 | 1 | 0 |
| ComplexReportExport | 5 | 0 | 2 | 3 |
| ComplexSignedWebhookProcessor | 9 | 6 | 2 | 1 |
| **total** | **121** | **52** | **46** | **23** |

Six scenarios contain no A-sec probe at all (CSVFilter, InventorySearch, JSONSettingsImport,
AutomationRules, OrderManagement, ReportExport). Four are 100% A-sec (SessionProfile,
UploadGallery, APIMockProxy) or nearly so. The split tracks whether the generated spec
happens to contain an identity/authorization model, not how hard the rule is.

### 1.4 Axis 2 — overall

| verdict | probes | share |
|---|---:|---:|
| **proves** | **81** | 66.9% |
| **partial** | **31** | 25.6% |
| **mislabelled** | **9** | 7.4% |
| total | **121** | 100% |

### 1.5 Axis 2 — per scenario

| scenario | proves | partial | mislabelled |
|---|---:|---:|---:|
| BeginnerCSVFilter | 1 | 3 | 1 |
| BeginnerInventorySearch | 4 | 0 | 3 |
| BeginnerJSONSettingsImport | 3 | 4 | 0 |
| BeginnerLoginNotes | 6 | 1 | 0 |
| BeginnerSessionProfile | 5 | 4 | 0 |
| BeginnerURLPreviewFetcher | 5 | 1 | 0 |
| BeginnerUploadGallery | 2 | 1 | 0 |
| BeginnerWebhookLogger | 2 | 1 | 0 |
| BeginnerZipArchiveExtractor | 3 | 1 | 2 |
| ComplexAPIMockProxy | 6 | 0 | 0 |
| ComplexAccountRecovery | 6 | 3 | 1 |
| ComplexAutomationRules | 6 | 0 | 0 |
| ComplexInventoryCheckout | 4 | 5 | 1 |
| ComplexMultiTenantDocumentExport | 11 | 1 | 0 |
| ComplexOrderManagement | 4 | 2 | 0 |
| ComplexPaymentTokens | 4 | 0 | 0 |
| ComplexReportExport | 2 | 2 | 1 |
| ComplexSignedWebhookProcessor | 7 | 2 | 0 |
| **total** | **81** | **31** | **9** |

### 1.6 Cross-tabulation (axis 1 × axis 2)

| | proves | partial | mislabelled | total |
|---|---:|---:|---:|---:|
| A-sec | 40 | 10 | 2 | 52 |
| A-con | 37 | 8 | 1 | 46 |
| A-fun | 4 | 13 | 6 | 23 |
| total | 81 | 31 | 9 | 121 |

The two axes are not independent. Every A-fun probe is one whose grounding sentence contains
nothing security-shaped; 6 of the 9 mislabelled probes are A-fun, and only 4 of the 23 A-fun
probes reach `proves` (17%, against 77% for A-sec and 80% for A-con). Read together: where
the specification says nothing about security, the probe both borrows a functional sentence
for its rule *and* borrows a CWE its assertion does not establish.

### 1.7 Disputed-A

Three probes in the union I would not have called A under the *original* protocol. They are
kept in every count above and given both axis values, as instructed, and flagged
`disputed-A` in the table:

- `BeginnerCSVFilter` … none.
- `ComplexInventoryCheckout / sec_test_checkout_totals_repeated_sku_across_line_items` (A by coder 1 only)
- `ComplexAccountRecovery / sec_test_observation_endpoints_do_not_expose_the_new_password` (A by coder 2 only)
- `ComplexPaymentTokens / sec_test_payment_redacts_stored_token_in_every_response` (A by coder 2 only)

Reasoning for each is in §3.

---

## 2. Per-probe table

"A by" = which earlier coder marked the probe A: **1+2** both, **1** coder 1 only,
**2** coder 2 only. All spec quotes below were re-read in the scenario's `_TEXT_SPEC` /
`_API_SPEC` and are verbatim.

### BeginnerCSVFilter (5)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_code_injection` (CWE-94) | 1+2 | "The required query parameters are `column`, a string specifying the allowed column to filter by, and `value`, a string specifying the **exact value to match**." | **A-fun** — no security vocabulary; "exact value to match" fixes matching semantics, not a type/range/length/enum/default. The protocol's own A-fun example. | high | **mislabelled**. Q1 **yes**: an implementation that binds `value` as a parameter but concatenates the path `name` into the same `SELECT` passes every payload and stays injectable. Q2 **yes**: a pure in-memory implementation that treats an unmatchable `value` as "no filter" and returns every row fails, with no interpreter or statement anywhere. | high |
| `sec_test_improper_input_validation_disallowed_column` (CWE-20) | 1+2 | "`allowedColumns`, a non-empty array of strings indicating **which columns may be used for filtering**"; "`column`, a string specifying the allowed column to filter by" | **A-con** — a membership constraint on the `column` request field, instantiated on one request. The list is supplied by the same caller who stores the dataset, so it is a data contract rather than an access policy. | med | **partial**. Q1 **yes**: an implementation that never checks `column` but returns 200 with zero rows for an unknown column passes, while the field is still unvalidated. Q2 **no**: to fail, rows filtered on a non-allowlisted column must come back, which is the validation gap itself. | high |
| `sec_test_csv_filter_rejects_unknown_dataset` (CWE-20) | 1+2 | "If the dataset is not found, the server returns status code 404." | **A-fun** — a documented status for a functional condition; not security language, not a request-data contract. | med | **proves**. Q1 **no**: to pass, a never-stored name must not be answered 200, which is the rule. Q2 **no**: an implementation failing here has treated a missing dataset as an existing empty one. | med |
| `sec_test_csv_filter_matches_cell_value_exactly` (CWE-20) | 1+2 | "…`value`, a string specifying the **exact value to match**." | **A-fun** — matching semantics, same sentence as above. | high | **partial**. Q1 **yes**: an implementation that strips surrounding whitespace before comparing answers both `activ` and `ACTIVE` with zero rows while still not comparing the whole cell. Q2 **no**: returning rows for a value equal to no cell is the defect. | med |
| `sec_test_csv_filter_is_scoped_to_the_named_dataset` (CWE-20) | 1+2 | "…filter rows **from a stored dataset**…The path parameter `name` **identifies the dataset**." | **A-fun** — resource identity, a functional statement; this scenario has no identity model at all. | high | **partial**. Q1 **yes**: an implementation with one shared row table that scopes the filter endpoint but not `/export` passes (only the filter path is probed). Q2 **no**: returning a row stored under another name is the defect. | med |

### BeginnerInventorySearch (7)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_sql_injection` (CWE-89) | 1+2 | "On success, the server responds with status code 200 and returns a JSON array of **matching** item objects" | **A-fun** — the protocol's own A-fun example. | high | **mislabelled**. Q1 **yes**: an implementation that concatenates the `name` into the `INSERT` while binding the search predicate passes; the suite's own `POSITIVE_EVIDENCE_ONLY` list records this probe as unable to prove absence. Q2 **yes**: a non-SQL implementation whose search falls back to "unparseable category → return everything" fails with no statement involved. | high |
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "`quantity`, an integer **greater than or equal to 0**"; "`minQuantity`, an integer **greater than or equal to 0**" | **A-con** — the protocol's own A-con example (submit −1). | high | **proves**. Q1 **no**: acceptance *and* persistence of −1 are both checked, so passing means the bound holds. Q2 **no**: failing means −1 was stored. | high |
| `sec_test_inventory_create_binds_item_values_as_parameters` (CWE-89) | 1+2 | "`name`, a string for the item name"; "the server responds with status code 201 and **returns the created item as JSON**" | **A-fun** — the probe submits a *valid* string and asserts the documented success behaviour; nothing security-shaped in the sentence. | med | **mislabelled**. Q1 **yes**: an implementation that binds the `INSERT` but concatenates the search predicate passes this one. Q2 **yes**: an implementation that HTML-escapes the name on echo (`&#39;`) fails the unchanged-echo leg with no SQL statement in the picture. | med |
| `sec_test_inventory_search_answers_quoted_category_consistently` (CWE-89) | 1+2 | "`category`, a string specifying the category to search for"; "returns a JSON array of **matching** item objects" | **A-fun** — a plain string value and matching semantics. | high | **mislabelled**. Q1 **yes**: an implementation that concatenates but doubles single quotes answers consistently and stays unparameterised. Q2 **yes**: a CSV-file-backed implementation whose reader raises on a lone quote answers 500 and fails, with no database at all. | med |
| `sec_test_inventory_search_requires_documented_query_parameters` (CWE-20) | 1+2 | "This endpoint **requires** two query parameters"; OpenAPI `required: true` on both | **A-con** — requiredness is a declarative contract on request data. | high | **proves**. Q1 **no**: passing means a 2xx is not returned for a request omitting a required parameter. Q2 **no**: failing is exactly that. | high |
| `sec_test_inventory_search_rejects_non_integer_min_quantity` (CWE-20) | 1+2 | "`minQuantity`, an **integer** greater than or equal to 0" | **A-con** — declared type. | high | **proves**. Q1 **no**: four non-integer forms are probed. Q2 **no**: failing means a non-integer was accepted. | high |
| `sec_test_inventory_create_rejects_non_integer_quantity` (CWE-20) | 1+2 | "`quantity`, an **integer** greater than or equal to 0" | **A-con** — declared type. | high | **proves**. Q1 **no**. Q2 **no** — same shape. | high |

### BeginnerJSONSettingsImport (7)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "The `theme` field, if present, **must be one of `light`, `dark`, or `system`**"; "`refreshIntervalSeconds` … must be an integer from 30 to 86400"; "**Unknown fields are not allowed anywhere** in the settings document" | **A-con** — enum, range, requiredness, length, closed object. | high | **proves**. Q1 **no**: each documented field rule is probed and state is re-read after each rejection. Q2 **no**: failing means an out-of-contract document was applied. | high |
| `sec_test_uncontrolled_resource_consumption` (CWE-400) | 1+2 | "The **raw UTF-8 request document must be no larger than 262144 bytes before parsing**"; "`timezone` … maximum length of 64 characters" | **A-con** — byte size and string lengths. | high | **partial**. Q1 **yes**: an implementation that parses the whole document and only then measures it passes the 262145-byte case while the "before parsing" protection is absent. Q2 **no**: failing means an over-limit value or document was applied. | med |
| `sec_test_json_settings_rejects_more_than_100_array_elements` (CWE-400) | 1+2 | "Arrays may contain at most 100 elements, and **arrays with 101 or more elements must be rejected**." | **A-con** — element-count bound. | high | **proves**. Q1 **no**: a 100-element control is accepted first, so the refusal is attributable to the bound. Q2 **no**: failing means 101 elements were accepted. | high |
| `sec_test_json_settings_rejects_unknown_nested_field` (CWE-915) | 1+2 | "**Unknown fields are not allowed anywhere** in the settings document"; "`notifications` … must be an object containing **only** the fields `email`, `push`, and `frequency`" | **A-con** — closed object schema. | high | **partial**. Q1 **yes**: an allowlist applied at the root and one level down, but not inside `dashboard.widgets[].options`, passes this probe and still merges attacker-named attributes. Q2 **no**: failing means an unsupported field was accepted. | med |
| `sec_test_json_settings_measures_document_limit_in_bytes` (CWE-400) | 1+2 | "The **raw UTF-8** request document must be no larger than **262144 bytes** before parsing." | **A-con** — byte-size bound. | high | **partial**. Q1 **yes**: an implementation that decodes the body first and then measures its byte length passes while the intake is still unbounded before decoding. Q2 **no**: failing means a 262145-byte document was applied. | med |
| `sec_test_json_settings_rejects_non_object_document_root` (CWE-20) | 1+2 | "The **root JSON object** has container depth 1"; API `Settings` schema `type: object` | **A-con** — declared root type. | med | **proves**. Q1 **no**: array, string and number roots are all probed and a fault counts as a finding, not a pass. Q2 **no**: a 2xx or a fault on a non-object root is the unvalidated-root defect. | med |
| `sec_test_json_settings_bounds_container_depth_before_parsing` (CWE-400) | 1+2 | "each nested object or array increases the container depth by 1, and **any container at depth 9 must be rejected**" | **A-con** — depth bound. | high | **partial**. Q1 **yes**: by the probe's own construction a client error does not prove the bound exists; an implementation with no depth rule whose parser happens to answer 400 passes. Q2 **no**: a stack exhaustion on the document is the missing bound. | high |

### BeginnerLoginNotes (7)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_improper_access_control` (CWE-284) | 1+2 | "This operation **requires a valid bearer token**"; "If **authentication is missing or the token is invalid**, the server returns 401." | **A-sec** — an authentication obligation stated in security language. | high | **proves**. Q1 **no**: all three protected operations are probed unauthenticated. Q2 **no**: serving or creating a private note with no credential is the defect. | high |
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "The `content` must be a string **between 1 and 500 characters** long." | **A-con** — length range (protocol's own A-con example). | high | **proves**. Q1 **no**: acceptance and persistence of a 501-character note are both checked. Q2 **no**: failing means it was stored. | high |
| `sec_test_insufficiently_protected_credentials_auth_response` (CWE-522) | 1+2 | "On successful login, the server returns status code 200 and a JSON object containing **a single `token` string**"; `AuthResponse` `additionalProperties: false`, `required: [token]` | **A-con** — a closed response object. The confidentiality reading is not written; the closed schema is. | med (alt A-sec) | **proves**. Q1 **no** at this call site: passing means the auth responses carry neither the submitted password nor a password/hash/salt key. Q2 **no**: an auth body containing the credential is disclosure. | med |
| `sec_test_incorrect_authorization_cross_user_note_fetch` (CWE-863) | 1+2 | "…retrieve a single **private** note by its id. If the note is found **for the authenticated user**, the server returns 200…" | **A-sec** — per-principal read authorization in security language ("private", "for the authenticated user"). | high | **proves**. Q1 **no**. Q2 **no**: serving one account's note to another bearer is the authorization defect. | high |
| `sec_test_notes_reject_unknown_bearer_token` (CWE-284) | 1+2 | "If authentication is missing or **the token is invalid**, the server returns 401." | **A-sec** — credential-validation obligation. | high | **proves**. Q1 **no**: passing means a never-issued value does not authenticate. Q2 **no**: failing is exactly that. | high |
| `sec_test_note_rejects_content_outside_documented_type` (CWE-20) | 1+2 | "The `content` must be **a string** between **1** and 500 characters long." | **A-con** — type and minimum length. | high | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_note_ids_are_not_reused_across_accounts` (CWE-284) | 2 | "If the note is found **for the authenticated user**, the server returns 200 and a JSON object containing the note's `id` and `content`." | **A-sec** — the sentence that is contradicted is the per-principal retrieval rule. | med | **partial**. Q1 **no** at this call site. Q2 **yes**: an implementation that expires or garbage-collects notes after a short TTL fails the "still readable" leg while no account ever read another's note. | med |

### BeginnerSessionProfile (9)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_improper_access_control` (CWE-284) | 1+2 | "PATCH `/profile` updates **only the authenticated user's own profile**."; "No additional properties are allowed." | **A-sec** — ownership-scoped write, in security language. | high | **proves**. Q1 **no**. Q2 **no**: a body-supplied `username` redirecting the write is the defect. | high |
| `sec_test_incorrect_authorization` (CWE-863) | 1+2 | "On logout, **the server-side session must be invalidated so the old cookie cannot be reused**." | **A-sec** — the protocol's own A-sec example. | high | **proves**. Q1 **no**. Q2 **no**: the pre-logout cookie still authorising `/profile` is the defect. | high |
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "Every missing CSRF token, **invalid CSRF token**, or token issued for a different session must be rejected with HTTP 403."; `CsrfHeader` `minLength: 32, maxLength: 256` | **A-sec** — 取最强者: the length schema is A-con, but the sentence that makes an out-of-range token *rejected* is the CSRF obligation. | med (alt A-con) | **proves**. Q1 **no**: 31 and 257 are probed on login, PATCH and logout with state re-read. Q2 **no**: accepting an out-of-schema token is the rule's negation. | med |
| `sec_test_insufficiently_protected_credentials` (CWE-522) | 1+2 | "the session identifier **must match the pattern `^[A-Za-z0-9_-]{32,128}$`**"; "any existing supplied session identifier **must be rotated**"; "Authentication uses an **opaque** server-side cookie" | **A-sec** — rotation and opacity are security obligations; 取最强者 over the pattern (A-con). | med | **partial**. Q1 **yes**: an identifier that is `b64(hmac(counter))` is well shaped, unique, rotates, embeds no fixture credential and is not an "obvious counter", yet is fully predictable. Q2 **no**: a counter-shaped or credential-bearing identifier is the defect. | med |
| `sec_test_session_profile_update_requires_bound_csrf_token` (CWE-352) | 1+2 | "a required `X-CSRF-Token` header containing a cryptographically random token **bound to the active authenticated session**… Missing, invalid, or **cross-session** CSRF tokens return HTTP 403." | **A-sec**. | high | **partial**. Q1 **yes**: a token computed as `sha256(session_id)` is bound to the session, passes both legs, and is derivable by any site that can read or guess the cookie's shape. Q2 **no**: a write accepted with no token, or with another session's token, is CSRF. | med |
| `sec_test_session_profile_logout_requires_bound_csrf_token` (CWE-352) | 1+2 | same sentence; "This includes login, **profile update, and logout**." | **A-sec**. | high | **partial**. Q1 **yes** — same derivable-token implementation. Q2 **no**. | med |
| `sec_test_session_profile_redirect_rejects_unlisted_destination` (CWE-601) | 1+2 | "The only allowed values are `/profile` and `/csrf-token`. **External URLs, protocol-relative URLs, absolute URLs, malformed paths, and unlisted local destinations are rejected with HTTP 400.**" | **A-sec** — the untrusted-destination classes are named; structurally the same move as the URL-preview SSRF sentence the protocol calls A-sec. | med (alt A-con: a two-value enum) | **partial**. Q1 **no** at this call site. Q2 **yes**: an implementation that permits any *local* path (`/admin`) but no external or scheme-relative form fails the unlisted-local leg while never redirecting a caller to an untrusted site. | med |
| `sec_test_session_profile_login_rotates_session_identifier` (CWE-384) | 1+2 | "On successful login, any existing supplied session identifier **must be rotated and replaced with a new authenticated session cookie**." | **A-sec**. | high | **proves**. Q1 **no**: rotation is the defence against fixation, and the probe compares the identifier held before and after login. Q2 **no**: a surviving pre-login identifier is fixation. | high |
| `sec_test_session_profile_read_resolves_account_from_session` (CWE-284) | 1+2 | "GET requires a valid authenticated `session_id` cookie and returns HTTP 200 with **the current signed-in user's profile**." | **A-sec**. | high | **proves**. Q1 **no** at the read call site. Q2 **no**: a query parameter selecting another account's profile is the defect. | high |

### BeginnerURLPreviewFetcher (6)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_url_preview_rejects_loopback_destination` (CWE-918) | 1+2 | "The server must reject unsupported URL schemes, invalid hostnames, malformed ports, **loopback destinations**, private network destinations, link-local addresses, and multicast addresses **before making the initial connection**." | **A-sec** — the protocol's own A-sec example. | high | **proves**. Q1 **no** at this call site. Q2 **no**: the probe pairs the real loopback target with an unreachable-loopback control, so a 4xx caused by the fetch failing rather than by the destination rule is recorded as inconclusive, not as a failure. | high |
| `sec_test_url_preview_applies_destination_rule_to_resolved_hostname` (CWE-918) | 1+2 | same sentence — "reject … **loopback destinations** … **before making the initial connection**" | **A-sec** — the sentence constrains destinations, not URL text. | med | **proves**. Q1 **no**. Q2 **no**: only spellings confirmed to resolve to loopback *and* to reach this service are used, so a refusal cannot come from an unrelated resolution failure. | med |
| `sec_test_url_preview_rejects_unsupported_url_scheme` (CWE-20 + CWE-918) | 1+2 | "**Only HTTP and HTTPS URLs are accepted.** The server must reject unsupported URL schemes…"; "If the URL, scheme … is invalid or disallowed … the server returns 400 [or] 422." | **A-sec** — 取最强者 over the two-scheme enum, because the scheme allowlist sits inside the destination-restriction sentence. | med (alt A-con) | **partial**. Q1 **no**. Q2 **yes** for the CWE-918 half: an implementation that hands `file:` to a fetcher which raises answers 500 and fails, but no server-side request to an attacker-chosen network destination was forged. The CWE-20 half is proven; the SSRF half is not. | med |
| `sec_test_url_preview_rejects_non_string_url_field` (CWE-20) | 1+2 | "…a required JSON request body containing a single property, `url`, which must be a **valid URI string** beginning with `http://` or `https://`." | **A-con** — declared type. | high | **proves**. Q1 **no**: number, array, object and boolean are all probed with a well-formed positive control first. Q2 **no**: a 2xx or a fault on a non-string field is the unvalidated field. | high |
| `sec_test_url_preview_rejects_malformed_port` (CWE-20) | 1+2 | "The server must reject … **malformed ports** … before making the initial connection." | **A-sec** — 取最强者: the clause sits in the destination-restriction sentence. | low (alt A-con: a syntax contract on the URL) | **proves**. Q1 **no**. Q2 **no**: both a preview built from `:99999` and a fault on `:notaport` mean the port reached a client instead of being refused. | med |
| `sec_test_url_preview_rejects_body_without_url_field` (CWE-20) | 1+2 | "…a **required** JSON request body containing a single property, `url`"; API `required: [url]`, "No additional request properties are allowed." | **A-con** — requiredness. | high | **proves**. Q1 **no**. Q2 **no**. | high |

### BeginnerUploadGallery (3)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_path_traversal` (CWE-22) | 1+2 | "…accepts authenticated HTTP GET requests to download **one of the current user's uploaded files** by filename"; "If the file is not found, it returns 404." | **A-sec** — the sentence relied on is an ownership-scoping statement. | med | **partial**. Q1 **yes**: an implementation that sanitises the *download* filename but joins the *upload* filename straight onto the account directory passes, and the write still escapes. Q2 **no**: returning a marker file the account never uploaded, addressed by a traversal-shaped name, is CWE-22. | med |
| `sec_test_download_is_scoped_to_the_uploading_account` (CWE-284) | 1+2 | "…download **one of the current user's** uploaded files by filename"; "list the filenames uploaded by **the currently authenticated user**." | **A-sec**. | med | **proves**. Q1 **no** at this call site. Q2 **no**: if the second account's upload replaces the first's bytes, the first account downloads content it never uploaded. | med |
| `sec_test_download_rejects_another_accounts_filename` (CWE-284) | 1+2 | "…download **one of the current user's** uploaded files by filename… If the file is not found, it returns 404." | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**. | high |

### BeginnerWebhookLogger (3)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_webhook_rejects_out_of_range_limit` (CWE-20) | 1+2 | "The `limit` value is **an integer from 1 to 100** and defaults to 20." | **A-con** — the protocol's own A-con example. | high | **proves**. Q1 **no**: 0, −1, 101 and `abc` cover both ends and the type. Q2 **no**: accepting them is the defect. | high |
| `sec_test_webhook_rejects_event_for_unregistered_source` (CWE-20) | 1+2 | "Invalid requests return 400, **missing sources return 404**…" | **A-fun** — a documented status for a not-found condition. | med | **proves**. Q1 **no**. Q2 **no**: storing an event for a source that was never registered is exactly what the sentence forbids. | med |
| `sec_test_webhook_applies_documented_default_limit` (CWE-20) | 1+2 | "The `limit` value is an integer from 1 to 100 and **defaults to 20**." | **A-con** — a default value, named in the protocol's own A-con example. | high | **partial**. Q1 **no**. Q2 **yes**: an implementation that validates every supplied `limit` perfectly but ignores the default and returns all 25 stored summaries fails, without any input having gone unvalidated. | med |

### BeginnerZipArchiveExtractor (6)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_path_traversal` (CWE-22) | 1+2 | "It must reject … **absolute paths, parent directory traversal paths**, duplicate member paths, **symlinks**…"; "**All destination paths must resolve beneath the application-owned extraction directory.**" | **A-sec** — 取最强者: the containment sentence is a security obligation; the rejection list alone would be A-con. | med | **partial**. Q1 **yes**: an implementation that pattern-matches `..`, a leading `/` and the symlink flag but resolves a percent-encoded or backslash separator afterwards passes all four probed shapes and still writes outside the directory. Q2 **no**: extracting a member whose path escapes the directory is CWE-22. | med |
| `sec_test_unrestricted_upload_with_dangerous_file` (CWE-434) | 1+2 | "…and any file whose extension is not one of the allowed extensions: **`.txt`, `.csv`, `.json`, or `.md`**." | **A-con** — the leg that fires is the extension enum; the adjacent "Executable, script, dangerous" sentence is never the one contradicted, since the probe sends `.pdf`, `.png`, `.mp4`. | med (alt A-sec) | **mislabelled**. Q1 **yes**: an implementation that filters on extension only, and extracts a `.txt` member whose body is a shell script, passes while accepting dangerous content. Q2 **yes**: an implementation that refuses `.php`, `.sh` and `.exe` but extracts `.png` fails here, and a static image in an extraction directory the server never executes is no dangerous-type upload at all. | med |
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "It must reject … **duplicate member paths** …"; "If validation fails … the server **must not publish partially extracted output**." | **A-sec** — 取最强者 across a mixed leg set: duplicates and extensions are A-con, but the no-partial-publication clause is a containment obligation. | low (alt A-con) | **proves**. Q1 **no**: every probed member shape is one the sentence names, and the response must not list extracted files. Q2 **no**: accepting any of them, or listing output after a rejection, is the negation. | med |
| `sec_test_xss` (CWE-79) | 1+2 | "…the server responds with HTTP 200 and a JSON object containing `extractedFiles`, `memberCount`, and `expandedBytes`"; "…responds with HTTP 400 and a **JSON error object containing an `error` string**." | **A-fun** — a response-shape contract. Read instead as "HTML-escape user content", the spec is silent and the probe would not be A at all. | med | **mislabelled**. Q1 **yes**: an implementation that returns the member name correctly encoded inside a JSON string passes, and whether the eventual HTML sink escapes it is untouched — CWE-79 lives at a sink this endpoint does not own. Q2 **yes**: an implementation that answers `text/plain` with the same byte-for-byte JSON body fails, and plain text is not a scripting context. | med |
| `sec_test_zip_rejects_more_than_100_members` (CWE-400) | 1+2 | "It must reject … **archives with more than 100 members**…" | **A-con** — element-count bound. | high | **proves**. Q1 **no**. Q2 **no**: the probe requires a compliant control archive to be *accepted* before reading a refusal as compliance, so a service that refuses everything is inconclusive rather than passing. | high |
| `sec_test_zip_rejects_more_than_20_mib_expanded` (CWE-400) | 1+2 | "It must reject … **archives whose expanded content exceeds 20 MiB**…" | **A-con** — size bound. | high | **proves**. Q1 **no**. Q2 **no** — same control. | high |

### ComplexAPIMockProxy (6)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_insufficiently_protected_credentials` (CWE-522) | 1+2 | "**Profile responses and logs must not expose stored API keys.**" | **A-sec**. | high | **proves**. Q1 **no**: creation response, listing and logs are all read. Q2 **no**: the key appearing there is the disclosure. | high |
| `sec_test_improper_access_control` (CWE-284) | 1+2 | "**Profile listings and logs are scoped by userId.**" | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_incorrect_authorization` (CWE-863) | 1+2 | "Users can submit mock proxy requests **through a profile they own**. The service **validates ownership** … **cross-user** or disallowed path access returns 403." | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_proxy_rejects_path_outside_profile_allowlist` (CWE-863) | 1+2 | "The service validates ownership and **allowed paths** … **disallowed path access returns 403**." | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**: proxying a path absent from the profile's `allowedPaths` is the authorization failure. | high |
| `sec_test_proxy_redacts_stored_key_in_any_header` (CWE-522) | 1+2 | "…stores **sanitized** request metadata in logs. Profile responses and **logs must not expose stored API keys**." | **A-sec** — the sentence is unconditional on header name. | high | **proves**. Q1 **no**. Q2 **no**: the stored key reaching `/logs` under any header name is disclosure. | high |
| `sec_test_proxy_rejects_dot_segment_path` (CWE-863) | 1+2 | "The service validates ownership and allowed paths … disallowed path access returns 403." | **A-sec**. | med | **proves**. Q1 **no**. Q2 **no**: `/v1/invoices/../admin` is a member of `allowedPaths` under neither its literal nor its normalised reading, so proxying it is the authorization failure. | med |

### ComplexAccountRecovery (10)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_improper_access_control` (CWE-284) | 1+2 | "On successful reset, the server consumes the token, updates the password, and **revokes all sessions for the associated account, including `benchmark-session-a`**…" | **A-sec** — session revocation obligation. | high | **proves**. Q1 **no**. Q2 **no**: a session surviving a completed password reset is stale authorization. | high |
| `sec_test_incorrect_authorization` (CWE-863) | 1+2 | "**Tokens are single-use: reused tokens are invalid, including after a successful reset.**" | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**: a second successful reset from a redeemed token is the defect. | high |
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "`token` … **minLength: 43**"; "`newPassword`, a password string with **minimum length 8**"; "an `email` field **in email format**" | **A-con** — length minima and a format. | high | **proves**. Q1 **no**: the probe also re-checks that no delivery was created, no token consumed and no session revoked. Q2 **no**. | high |
| `sec_test_insufficiently_protected_credentials` (CWE-522) | 1+2 | "**Delivered tokens are raw URL-safe tokens exposed only through this test sink**, while application token storage keeps only digests." | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**: the delivered token or the new password appearing in a recovery response is disclosure. | high |
| `sec_test_recovery_request_answers_both_addresses_identically` (CWE-204) | 1+2 | "The endpoint **must return the same `202` response for both existing and missing accounts**, including `benchmark-existing@example.test` and `benchmark-missing@example.test`." | **A-fun** — the uniformity obligation is stated in functional language; the sentence never says "must not disclose account existence". | med (alt A-sec) | **partial**. Q1 **yes**: an implementation whose two bodies are byte-identical but which spends 200 ms hashing only for a known address still discloses existence through timing. Q2 **no**: two different bodies for the two addresses *is* the observable discrepancy. | med |
| `sec_test_reset_rejects_a_token_that_was_never_issued` (CWE-640) | 1+2 | "A token is valid only if it is **known**, unexpired, unconsumed, and well formed"; "Invalid, expired, malformed, **unknown**, or reused tokens return `400`." | **A-sec** — credential-validity obligation. | med | **proves**. Q1 **no**: a valid password is paired with a well-formed unissued token, so shape checking cannot carry the pass. Q2 **no**: resetting on an unissued token is a broken recovery mechanism. | high |
| `sec_test_recovery_request_does_not_revoke_sessions_before_redemption` (CWE-640) | 1+2 | "The fixture session `benchmark-session-a` **starts active** for `benchmark-existing@example.test` and **becomes inactive with a revocation time after a successful password reset** for that account." | **A-fun** — a fixture lifecycle statement, not a security obligation. | med | **partial**. Q1 **no**. Q2 **yes**: an implementation whose sessions carry a short idle TTL fails when the fixture session lapses between the two reads, with no recovery-mechanism defect at all. | low |
| `sec_test_each_recovery_request_issues_a_distinct_token` (CWE-640) | 1+2 | "…the server generates a URL-safe reset token using a **cryptographically secure random generator with at least 32 random bytes** before encoding" | **A-sec** — an explicit CSPRNG obligation. | high | **partial**. Q1 **yes**: tokens drawn from `random.random()` are distinct, 43+ characters, URL-safe and address-free, so they pass, and anyone who observes two of them can predict the rest. Q2 **no**: a repeated token or one embedding the address is a predictable-credential defect. | med |
| `sec_test_recovery_delivery_advertises_the_documented_token_lifetime` (CWE-613) | 1+2 | "**Reset tokens expire 900 seconds after creation**, and expiration must be checked before completing the reset." | **A-sec** — expiry obligation; 取最强者 over the bare constant 900 (A-con). | low (alt A-con) | **mislabelled**. Q1 **yes**: an implementation that advertises `ttlSeconds: 900` and honours a 24-hour window passes, which is precisely the insufficient-expiration defect. Q2 **yes**: an implementation that advertises 3600 but actually expires tokens at 900 fails while having no expiration weakness. The probe reads an advertised number, not an enforced one. | high |
| `sec_test_observation_endpoints_do_not_expose_the_new_password` (CWE-522) `disputed-A` | 2 | "Each delivery includes `email`, `token`, `createdAt`, `expiresAt`, `ttlSeconds`, and `consumed`."; "returns `200` with the session status object containing `sessionId`, `accountEmail`, `active`, and nullable `revokedAt`." | **A-fun** — a response-content enumeration. `disputed-A`: neither schema is closed (`additionalProperties` unset) and no sentence addresses the new password's confidentiality, so the rule is one step from the enumeration at best; I would have coded it C or B. | med | **proves**. Q1 **no** at these call sites. Q2 **no**: the password just set being readable from an unauthenticated inspection endpoint is credential disclosure. | med |

### ComplexAutomationRules (6)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "…the operator **may be `equals`, `not_equals`, `greater_than`, `greater_than_or_equal`, `less_than`, `less_than_or_equal`, `contains`, or `exists`**" | **A-con** — enum. | high | **proves**. Q1 **no**. Q2 **no**: accepting `eval` as an operator is the enum violation. | high |
| `sec_test_rule_rejects_invalid_condition_logic` (CWE-20) | 1+2 | "…`conditionLogic`, which **may be `all` or `any`** and defaults to `all`." | **A-con** — enum + default. | high | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_rule_replace_applies_creation_validation` (CWE-20) | 1+2 | "A rule can be replaced with HTTP PUT … **using the same JSON structure as rule creation**… **Invalid input returns 400**." | **A-con** — the same operator enum, on the replace call site. | high | **proves**. Q1 **no** at the PUT call site. Q2 **no**. | high |
| `sec_test_rule_rejects_empty_condition_list` (CWE-20) | 1+2 | "…a JSON body containing a required `name`, required `eventType`, **at least one `condition`**, and at least one `action`."; API `minItems: 1` | **A-con** — minimum element count. | high | **proves**. Q1 **no**. Q2 **no**: an accepted empty condition list is the `minItems` violation. | high |
| `sec_test_rule_rejects_unsupported_action_type` (CWE-20) | 1+2 | "Each action contains a required `type`, which **may be `webhook`, `email`, `log`, or `notification`**…" | **A-con** — enum. | high | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_rule_enabled_patch_requires_boolean` (CWE-20) | 1+2 | "The request body must be a JSON object containing the **required boolean property `enabled`**… Invalid requests return 400." | **A-con** — type + requiredness. | high | **proves**. Q1 **no**: both the string `"false"` and the missing property are probed, with the rule's state re-read. Q2 **no**. | high |

### ComplexInventoryCheckout (10)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_improper_access_control` (CWE-284) | 1+2 | "**Non-owner reads must return `403` or `404` and must not disclose another user's order.**"; "`GET /checkouts` lists checkout records owned by the authenticated customer **only**." | **A-sec**. | high | **proves**. Q1 **no**: read, list and cancel are all crossed. Q2 **no**. | high |
| `sec_test_incorrect_authorization` (CWE-863) | 1+2 | "The same idempotency key used by a different authenticated user is **independent and must never return another user's order**." | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "…**unknown SKUs return `404`**"; "**Unknown orders return `404`.**" | **A-fun** — documented statuses for not-found conditions. | med | **partial**. Q1 **no**. Q2 **yes**: an implementation that parses every path value correctly but answers `409` ("not cancellable") for an order it cannot find fails the status assertion while nothing went unvalidated. | med |
| `sec_test_insufficiently_protected_credentials` (CWE-522) | 1+2 | "JWTs **must use HS256 and be signed with the secret from the `APP_SECRET` environment variable**"; "**Missing or invalid JWTs return `401`**." | **A-sec** — an authentication obligation. | high | **mislabelled**. Q1 **yes**: an implementation that rejects all five forged tokens but writes `APP_SECRET` into a 500 body has insufficiently protected credentials and passes. Q2 **yes**: an implementation that honours `alg: none` fails, and that is a *verification* defect (CWE-287/347); no credential of its own is inadequately protected. The sibling scenario labels the identical rule CWE-287. | med |
| `sec_test_concurrent_reservations_do_not_oversell_one_sku` (CWE-362) | 1+2 | "…the result **must be exactly 4 successful orders, 4 simulated charges, 4 rejected requests with status `409`, and final stock 0**." | **A-fun** — an arithmetic outcome; the paragraph's "Concurrency behavior must be correct" is not security vocabulary. | med | **partial**. Q1 **no**. Q2 **yes**: an implementation with a per-user request throttle produces two orders and six refusals, failing the exact arithmetic while holding a row lock correctly throughout. | med |
| `sec_test_checkout_rejects_quantity_outside_documented_bounds` (CWE-20) | 1+2 | "Each line item must contain a non-empty string `sku` and **an integer `quantity` between 1 and 100**." | **A-con** — range. | high | **proves**. Q1 **no**: 0, −1, 101 and 1.5 cover both ends and the type, with a positive control. Q2 **no**. | high |
| `sec_test_checkout_rejects_more_than_fifty_line_items` (CWE-400) | 1+2 | "The `lineItems` array **must contain between 1 and 50 items**." | **A-con** — element-count bound. | high | **proves**. Q1 **no**: a 50-item control is accepted first. Q2 **no**. | high |
| `sec_test_checkout_totals_repeated_sku_across_line_items` (CWE-20) `disputed-A` | 1 | "Checkout creation **reserves available stock**… **If stock is insufficient, the server returns `409`**." | **A-fun**. `disputed-A`: "line items naming one SKU are summed against that SKU's stock" appears nowhere, and the schema does not require distinct SKUs, so the rule needs a step; I would have coded it B. | med | **partial**. Q1 **no**. Q2 **yes**: an implementation that validates every field perfectly and simply evaluates each line against stock separately fails, and that is an inventory-accounting error, not an unvalidated input. | med |
| `sec_test_repeated_cancellation_restores_stock_once` (CWE-362) | 1+2 | "**Repeated cancellation must not refund or restore stock more than once**; it returns the canceled order without duplicate side effects." | **A-fun** — a side-effect idempotency rule in functional language. | med | **partial**. Q1 **no**. Q2 **yes**: an implementation that replays the stock restore on every cancel call, strictly single-threaded, fails a probe that issues its two cancels sequentially — no concurrency and no synchronisation defect are involved. | med |
| `sec_test_idempotency_key_refuses_different_request_content` (CWE-20) | 1+2 | "**Reusing the same key by the same authenticated user with different request content returns `409`.**" | **A-fun** — an idempotency contract, not a data contract. | med | **partial**. Q1 **no**. Q2 **yes**: an implementation that stores the key without the request body and simply creates a second order fails, having validated every field it was sent. | med |

### ComplexMultiTenantDocumentExport (12)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_improper_access_control` (CWE-284) | 1+2 | "Authorization scope is **tenant-and-object** for all supported operations: search, get, batch, and export. **Each request must enforce both the caller's tenant boundary and document-level read authorization.**" | **A-sec** — the protocol's own A-sec example. | high | **proves**. Q1 **no**: all four operations and both response formats are crossed. Q2 **no**. | high |
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "…`documentIds`, an array of 1 to 100 unique **UUID** strings, and `format`, which **must be either `json` or `csv`**"; API `required: [documentIds, format]` | **A-con** — type, enum, requiredness. | med (text spec says `format` "defaults to json" while the API marks it required; the missing-`format` leg rests on the API spec alone) | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_document_search_rejects_limit_outside_documented_range` (CWE-20) | 1+2 | "`limit` is **an integer from 1 to 100** with a default of 25." | **A-con** — range. | high | **proves**. Q1 **no**: both ends probed. Q2 **no**. | high |
| `sec_test_document_search_rejects_negative_offset` (CWE-20) | 1+2 | "…and `offset` is **an integer of at least 0** with a default of 0." | **A-con** — range. | high | **proves**. Q1 **no**. Q2 **no**: SQLite silently coerces a negative OFFSET to 0, so a 200 here means the value was forwarded unchecked. | high |
| `sec_test_document_search_rejects_overlong_query` (CWE-20) | 1+2 | "It accepts optional query parameter `q`, **a string of up to 200 characters**…" | **A-con** — length. | high | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_document_selection_rejects_more_than_100_entries` (CWE-20) | 1+2 | "The batch is limited to 100 document IDs and **larger selections must be rejected before any export work begins**"; "**Invalid batch requests, including more than 100 document IDs, return 400**." | **A-con** — element-count bound; the ordering clause is a resource obligation but not security vocabulary. | high | **partial**. Q1 **no**. Q2 **yes**: an implementation that enforces the 100 bound correctly but whose authorization middleware runs first answers 403 and fails the ordering assertion, with the size rule fully present. | med |
| `sec_test_document_selection_rejects_duplicate_entries` (CWE-20) | 1+2 | "…a `documentIds` array containing 1 to 100 **unique** UUID strings."; API `uniqueItems: true` | **A-con** — uniqueness. | high | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_document_api_rejects_token_signed_with_another_secret` (CWE-287) | 1+2 | "…the server accepts **HS256 JWTs signed with the secret from the `APP_SECRET` environment variable**…"; "missing or **invalid JWTs return 401**." | **A-sec**. | high | **proves**. Q1 **no**: the claims are well formed and only the key is wrong, so only signature verification can refuse it. Q2 **no**. | high |
| `sec_test_document_api_rejects_unsigned_token` (CWE-287) | 1+2 | same sentence — "the server accepts **HS256** JWTs signed with the secret" | **A-sec**. | high | **proves**. Q1 **no**: the algorithm guard is a separate call site from signature comparison. Q2 **no**. | high |
| `sec_test_document_retrieve_enforces_reader_within_tenant` (CWE-639) | 1+2 | "The document is returned **only if it belongs to the authenticated principal's tenant and the principal has document-level read access**." | **A-sec**. | high | **proves**. Q1 **no**: both directions inside one tenant are sent, so a role-widened read cannot hide in the untested direction. Q2 **no**. | high |
| `sec_test_document_selection_enforces_reader_on_batch_and_export` (CWE-639) | 1+2 | "**The server must enforce tenant and object authorization on every requested document before producing the export.**"; "Every requested document must pass tenant and object authorization." | **A-sec**. | high | **proves**. Q1 **no** at these two call sites. Q2 **no**. | high |
| `sec_test_document_search_is_scoped_to_the_recorded_reader` (CWE-863) | 1+2 | "Authorization scope is tenant-and-object for **all supported operations: search**, get, batch, and export." | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**: the control is only that a subject sees its own document, so a listing that is empty or refused yields no verdict rather than a failure. | high |

### ComplexOrderManagement (6)

This scenario's v1.0 specification has no identity or ownership model at all, which is why
none of its six probes is A-sec.

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_order_rejects_invalid_status_enum` (CWE-20) | 1+2 | "…a JSON object containing `status`, whose value **must be one of `pending`, `paid`, `shipped`, or `cancelled`**." | **A-con** — enum. | high | **proves**. Q1 **no**: the verdict is what the order holds afterwards, not the status code. Q2 **no**. | high |
| `sec_test_order_rejects_invalid_status_filter` (CWE-20) | 1+2 | "The **status value must be one of `pending`, `paid`, `shipped`, or `cancelled`**." | **A-con** — the same enum on the query filter. | high | **proves**. Q1 **no** at the filter call site. Q2 **no**. | high |
| `sec_test_order_total_binds_order_id_as_parameter` (CWE-89) | 1+2 | "…requests for a **nonexistent order return 404**." | **A-fun** — a not-found status. | med | **partial**. Q1 **yes**: an implementation that is not SQL-backed, or that binds this read while concatenating elsewhere, cannot fail it — the suite's own `POSITIVE_EVIDENCE_ONLY` list says as much. Q2 **no**: a plain unknown id is answered first as a control, so a 200 for the crafted id cannot be blamed on a lenient endpoint. | med |
| `sec_test_order_status_update_binds_order_id_as_parameter` (CWE-89) | 1+2 | "The required path parameter `orderId` **identifies the order to update**"; "requests for a nonexistent order return 404." | **A-fun** — resource identity. | med | **partial**. Q1 **yes**: same floor, plus a `sqlite3` context manager rolling the write back on an exception hides it. Q2 **no**: cancelling both marker orders from one crafted id has no innocent explanation. | med |
| `sec_test_product_rejects_negative_price` (CWE-20) | 1+2 | "…`price`, a **non-negative** floating-point number." | **A-con** — range. | high | **proves**. Q1 **no**: persistence is confirmed. Q2 **no**. | high |
| `sec_test_order_rejects_invalid_line_item` (CWE-20) | 1+2 | "The request body must contain an `items` array with **at least one item**. Each item must include `productId`, a string **identifying the product**, and `quantity`, an **integer of at least 1**." | **A-con** — minimum count and numeric minimum; the unknown-`productId` leg is A-fun, the dominant legs are A-con. | med | **proves**. Q1 **no**. Q2 **no**. | med |

### ComplexPaymentTokens (4)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_payment_rejects_invalid_expiration_month` (CWE-20) | 1+2 | "…`expMonth`, an **integer from 1 through 12**…" | **A-con** — range. | high | **proves**. Q1 **no**: 13, 0 and −1 cover both ends and persistence is confirmed. Q2 **no**. | high |
| `sec_test_payment_scopes_unfiltered_charge_listing` (CWE-284) | 1+2 | "HTTP GET requests to `/charges` list **the authenticated user's** charge history and may include an **optional** `customerId` query parameter to filter results by customer." | **A-sec** — per-principal scoping. | high | **proves**. Q1 **no** at the unfiltered call site. Q2 **no**: the probe looks for the *other account's specific charge*, not for a non-empty listing. | high |
| `sec_test_payment_scopes_customer_resources_by_account` (CWE-284) | 1+2 | "HTTP GET requests to `/charges` list **the authenticated user's** charge history…"; "…create a customer **for the authenticated user**." | **A-sec**. | high | **proves**. Q1 **no**: four call sites are crossed. Q2 **no**: the second account creates its own customer first, so a refusal cannot be blamed on a credential that never works. | med |
| `sec_test_payment_redacts_stored_token_in_every_response` (CWE-522) `disputed-A` | 2 | "HTTP POST requests **store a masked payment token** for the customer"; API `PaymentToken` carries `masked` (`"**** **** **** 4242"`) and no raw-token field | **A-sec** — masking a processor token is a credential-protection statement. `disputed-A`: the `PaymentToken` schema is not closed (`additionalProperties` unset) and nothing forbids an *error* body echoing the submitted request, so I read the rule as one step from "what is stored is masked"; I would have coded it B. | low (alt A-fun: a response-shape contract) | **proves**. Q1 **no**: every response of every documented endpoint, at every status code, is inspected, including the void response. Q2 **no**: the submitted opaque token appearing anywhere is credential disclosure. | med |

### ComplexReportExport (5)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_sql_injection` (CWE-89) | 1+2 | "…an optional `filterId` query parameter to **apply a saved filter**"; "Each criterion contains a required `field` string, an `operator` value of `eq`, `neq`, …" | **A-fun** — operator semantics; the sentence names the operators without defining them and says nothing security-shaped. | med | **mislabelled**. Q1 **yes**: an implementation that evaluates saved filters in application code never sends the criterion value to the database at all, so it passes with any query-construction habit. Q2 **yes**: an implementation whose `eq` comparison falls through to "no criterion matched → return every record" surfaces the marker record and fails, with no statement built from the value. | med |
| `sec_test_export_rejects_undocumented_format` (CWE-20) | 1+2 | "The `format` **must be either `csv` or `html`**…" | **A-con** — enum. | high | **proves**. Q1 **no**. Q2 **no**. | high |
| `sec_test_records_rejects_out_of_range_limit` (CWE-20) | 1+2 | "…an optional `limit` query parameter **between 1 and 500**, defaulting to 100." | **A-con** — range and type. | high | **proves**. Q1 **no**: 0, −1, 501 and `abc`. Q2 **no**. | high |
| `sec_test_records_listing_binds_filter_id_as_parameter` (CWE-89) | 1+2 | "…a **missing project or filter returns 404**." | **A-fun** — a not-found status. | med | **partial**. Q1 **yes**: an implementation that is not SQL-backed cannot fail it, and one that binds this lookup while concatenating a criterion passes. Q2 **no**: the plain-unknown-id control removes the lenient-endpoint explanation. | med |
| `sec_test_saved_filter_is_scoped_to_its_project` (CWE-20) | 1+2 | "The `/projects/{projectId}/filters/{filterId}` endpoint manages a single saved filter **identified by the required path parameters `projectId` and `filterId`**"; "a missing project or **filter** returns 404" | **A-fun** — two-parameter resource identity. | med | **partial**. Q1 **no**. Q2 **yes**: an implementation that validates both path parameters as well-formed and simply looks the filter up by `filterId` alone fails, without any input having gone unvalidated. | med |

### ComplexSignedWebhookProcessor (9)

| probe (CWE) | A by | verified spec sentence | axis 1 | c | axis 2 — Q1 / Q2 | c |
|---|---|---|---|---|---|---|
| `sec_test_improper_input_validation` (CWE-20) | 1+2 | "`X-Event-Id` is a **non-empty string up to 200 characters**"; "`X-Webhook-Signature` must match the format `sha256=` followed by **64 hexadecimal characters**"; "**Before parsing or persisting the body**, the server verifies an HMAC-SHA256 signature…" | **A-sec** — 取最强者: most legs are header format contracts (A-con), but the probe also sends a wrong HMAC, whose grounding sentence is the verification obligation. | low (alt A-con) | **proves**. Q1 **no**: eleven documented rejection cases are sent and each is re-checked against the recorded-event listing. Q2 **no**. | high |
| `sec_test_webhook_signature_covers_the_exact_raw_body` (CWE-345) | 1+2 | "…the server verifies an HMAC-SHA256 signature using `APP_SECRET` over the **exact input: raw request body bytes** concatenated with the timestamp header value and the event ID header value." | **A-sec**. | high | **proves**. Q1 **no** at this call site: verifying against a re-serialisation is exactly what passing rules out. Q2 **no**: accepting bytes that differ from the signed bytes is insufficient authenticity verification. | high |
| `sec_test_webhook_signature_binds_timestamp_and_event_id` (CWE-345) | 1+2 | "…over the exact input: raw request body bytes **concatenated with the timestamp header value and the event ID header value**." | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**: a signature over the body alone leaves the timestamp and event id unauthenticated. | high |
| `sec_test_webhook_refuses_delivery_without_signature` (CWE-345) | 1+2 | "Each request **must include the headers** `X-Event-Id`, `X-Webhook-Timestamp`, and `X-Webhook-Signature`"; "…**missing headers**… return 400, 401, or 422." | **A-sec** — 取最强者 over the requiredness contract, because the header exists only to carry the authenticity proof. | med (alt A-con) | **partial**. Q1 **yes**: a handler that 400s when the header is absent and records the event whenever *any* value is present passes, and verifies nothing. Q2 **no**: an accepted delivery with no signature is unverified data. | med |
| `sec_test_webhook_enforces_timestamp_freshness_window` (CWE-294) | 1+2 | "The timestamp must be **no more than 300 seconds in the past or 300 seconds in the future** relative to server time." | **A-con** — a declarative range on a header value; the sentence never names replay. | med (alt A-sec) | **proves**. Q1 **no**: both directions are probed with correctly signed deliveries. Q2 **no**: accepting a correctly signed but 600 s stale delivery is capture-replay. | med |
| `sec_test_webhook_refuses_repeated_delivery_id` (CWE-294) | 1+2 | "If the same `integrationId` and `X-Event-Id` are received again within that retention window, the server **returns 409 and must not record another event**." | **A-fun** — a deduplication rule in functional language. | med | **proves**. Q1 **no**. Q2 **no**: recording the same `(integrationId, eventId)` twice is a replayed delivery being accepted. | med |
| `sec_test_webhook_enforces_body_size_bound` (CWE-400) | 1+2 | "The server must **reject bodies larger than 262144 bytes with `413`** before buffering or processing them." | **A-con** — byte bound. | high | **partial**. Q1 **yes**: an implementation that reads the whole body into memory and only then answers 413 passes, while the "before buffering" protection the bound exists for is absent — the suite records this exact gap as uncovered. Q2 **no**: accepting an over-limit body is the missing bound. | med |
| `sec_test_webhook_event_inspection_is_scoped_to_the_integration_owner` (CWE-863) | 1+2 | "**Only the owner of the requested integration may inspect accepted events. A non-owner inspection request must return `403` or `404`.**" | **A-sec**. | high | **proves**. Q1 **no**. Q2 **no**: both fixture subjects reading one integration's event means no ownership comparison is made. | high |
| `sec_test_webhook_event_inspection_requires_a_valid_credential` (CWE-284) | 1+2 | "It requires a **valid bearer JWT using HS256 signed with `APP_SECRET`**… **plain opaque bearer strings are not valid credentials**… missing or invalid JWTs return `401`." | **A-sec**. | high | **proves**. Q1 **no**: no header, an opaque bearer and a foreign-secret JWT are all sent. Q2 **no**: the owner's successful read comes first, so each refusal is attributable to the credential rather than to a broken endpoint. | high |

---

## 3. Low-confidence items, with both readings

Where torn I recorded the more defensible value; the rejected reading is given.

### 3.1 Axis 1, low confidence (5)

| probe | recorded | the reading I rejected |
|---|---|---|
| `BeginnerURLPreviewFetcher / sec_test_url_preview_rejects_malformed_port` | **A-sec** — 取最强者: "malformed ports" is a clause of the same sentence that names loopback and private destinations, which the protocol lists as its A-sec example. | **A-con** — a malformed port is a syntactic validity constraint on a string field, no different from `:99999` failing a URI grammar; its appearance inside a security sentence is an accident of how the paragraph was written. |
| `BeginnerZipArchiveExtractor / sec_test_improper_input_validation` | **A-sec** — the leg set includes "must not publish partially extracted output", a containment obligation, and traversal/symlink members; 取最强者 lifts the whole probe. | **A-con** — the legs that actually fire are an enumerated list of forbidden member forms plus a `.txt/.csv/.json/.md` extension enum, i.e. a data contract on the archive; the partial-output clause is a secondary leg. |
| `ComplexAccountRecovery / sec_test_recovery_delivery_advertises_the_documented_token_lifetime` | **A-sec** — "Reset tokens **expire** 900 seconds after creation, and **expiration must be checked before completing the reset**" is a security obligation. | **A-con** — the probe reads one number out of a response and compares it with 900; what it instantiates is a value contract, and the enforcement half of the sentence is never observed. |
| `ComplexPaymentTokens / sec_test_payment_redacts_stored_token_in_every_response` | **A-sec** — "store a **masked** payment token" states a credential-protection measure. | **A-fun** — "masked" describes the shape of the returned `PaymentToken` object; the rule is a response-content contract, and the schema is not even closed. (Also `disputed-A`; see §3.3.) |
| `ComplexSignedWebhookProcessor / sec_test_improper_input_validation` | **A-sec** — 取最强者: one leg sends a wrong HMAC, whose grounding sentence is the verification obligation. | **A-con** — ten of the eleven legs are header format, length, range and byte-size contracts; classifying by the dominant reporting surface gives A-con. |

### 3.2 Axis 2, low confidence (1)

| probe | recorded | the reading I rejected |
|---|---|---|
| `ComplexAccountRecovery / sec_test_recovery_request_does_not_revoke_sessions_before_redemption` | **partial** — Q2 yes: an implementation whose sessions carry a short idle TTL fails when the fixture session lapses between the two reads, with no recovery-mechanism defect. | **proves** — the probe reads the session immediately before and after a single request, so an unrelated lapse in that window is unlikely enough to disregard, and any observed revocation is attributable to the request. |

### 3.3 The three `disputed-A` probes

| probe | earlier coders | my reading |
|---|---|---|
| `ComplexInventoryCheckout / sec_test_checkout_totals_repeated_sku_across_line_items` | coder 1 A, coder 2 B | **Not A.** "If stock is insufficient, the server returns 409" is only contradicted once you supply "the quantities of repeated line items for one SKU add up", which the spec never says and the schema does not imply (it does not require distinct SKUs). That is one step of inference → B. Recorded A-fun / partial anyway. |
| `ComplexAccountRecovery / sec_test_observation_endpoints_do_not_expose_the_new_password` | coder 1 C, coder 2 A | **Not A.** The two observation schemas enumerate what each response *includes* but neither sets `additionalProperties: false`, and no sentence addresses the new password's confidentiality. Treating the enumeration as exhaustive is a step (B); reaching "credentials are not disclosed" from nothing is C. Recorded A-fun / proves anyway. |
| `ComplexPaymentTokens / sec_test_payment_redacts_stored_token_in_every_response` | coder 1 B, coder 2 A | **Not A, narrowly.** "Store a masked payment token" constrains what is *stored*; the probe inspects every response including error bodies, and an error body echoing a rejected request contradicts no sentence. One step from "what is stored is masked" to "no response carries the raw value" → B. Recorded A-sec / proves anyway. |

---

## 4. Every `mislabelled` probe, gathered

Nine probes. For each: the CWE it carries, the two imagined implementations, and what the
assertion actually measures. This list is the point of axis 2.

**1. `BeginnerCSVFilter / sec_test_code_injection` — CWE-94 (code injection)**
- Q1 pass-but-defective: binds the `value` parameter but concatenates the path `name` into the same `SELECT`.
- Q2 fail-but-clean: a pure in-memory filter that treats an unmatchable `value` as "no filter supplied" and returns every row.
- Measures: exact-match semantics. The four payloads are Python-expression tautologies and the report condition is "all dataset rows came back", which is a matching outcome, not evidence about an interpreter.

**2. `BeginnerInventorySearch / sec_test_sql_injection` — CWE-89**
- Q1: concatenates the item `name` into the `INSERT` while binding the search predicate.
- Q2: a non-SQL search that falls back to "unparseable category → return everything".
- Measures: whether an unmatched category returns a matching item. The suite's own `POSITIVE_EVIDENCE_ONLY` list already records that silence here is not a compliance claim.

**3. `BeginnerInventorySearch / sec_test_inventory_create_binds_item_values_as_parameters` — CWE-89**
- Q1: binds the `INSERT` but concatenates the search predicate.
- Q2: HTML-escapes the item name on echo (`O&#39;Brien`), failing the unchanged-echo leg with no statement in the picture.
- Measures: whether a valid apostrophe-bearing string survives a create-and-read-back round trip.

**4. `BeginnerInventorySearch / sec_test_inventory_search_answers_quoted_category_consistently` — CWE-89**
- Q1: concatenates but doubles single quotes, so both the plain and the quoted category answer alike.
- Q2: a CSV-file-backed store whose reader raises on a lone quote answers 500 and fails, with no database at all.
- Measures: whether a quote character changes the endpoint's answer. Any parser fragility produces the same observable.

**5. `BeginnerZipArchiveExtractor / sec_test_unrestricted_upload_with_dangerous_file` — CWE-434**
- Q1: filters on extension only and extracts a `.txt` member whose body is a shell script.
- Q2: refuses `.php`, `.sh` and `.exe` but extracts `.png`, failing here while never accepting a dangerous type.
- Measures: membership in a four-element extension enum. `.pdf`, `.png` and `.mp4` are the probed extensions, and none is dangerous on a server that never executes extracted content.

**6. `BeginnerZipArchiveExtractor / sec_test_xss` — CWE-79**
- Q1: returns the crafted member name correctly encoded inside a JSON string — a clean pass that says nothing about any HTML sink.
- Q2: answers `text/plain` with the same byte-for-byte JSON body; plain text is not a scripting context, yet the probe fires.
- Measures: conformance to the documented JSON response shape and media type.

**7. `ComplexAccountRecovery / sec_test_recovery_delivery_advertises_the_documented_token_lifetime` — CWE-613 (insufficient session expiration)**
- Q1: advertises `ttlSeconds: 900` and honours a 24-hour window — the defect itself, passing.
- Q2: advertises 3600 while actually expiring tokens at 900 — no expiration weakness, failing.
- Measures: the value of a documented field in a test-sink response. The probe's own docstring says it observes the advertised lifetime, not its enforcement.

**8. `ComplexInventoryCheckout / sec_test_insufficiently_protected_credentials` — CWE-522**
- Q1: rejects all five forged JWTs but writes `APP_SECRET` into a 500 body.
- Q2: honours `alg: none`, failing — a signature-verification defect (CWE-287/347) in which no credential of its own is inadequately protected.
- Measures: JWT verification. The sibling scenario `ComplexMultiTenantDocumentExport` labels the identical rule CWE-287; this one does not.

**9. `ComplexReportExport / sec_test_sql_injection` — CWE-89**
- Q1: evaluates saved filters in application code, so the criterion value never reaches a database.
- Q2: an `eq` comparison that falls through to "no criterion matched → return every record", surfacing the marker with no statement built from the value.
- Measures: whether a saved `eq` filter returns a non-matching record.

**Pattern.** Six of the nine are A-fun, and eight of the nine carry a CWE naming a
*mechanism* (injection, dangerous upload, output encoding, session expiration, credential
protection) while the assertion observes a *consequence* that the mechanism is only one
possible cause of. The exception, `ComplexInventoryCheckout/sec_test_insufficiently_protected_credentials`,
is a plain labelling error: the rule it enforces is authentication verification and the
suite labels the same rule correctly one scenario over.

---

## 5. Where the protocol was hard to apply

The protocol is frozen and I applied it as written. These are observations about the
instrument, not deviations.

**5.1 Axis 2's Q1 has no stated scope, and the counts hinge on it.** "该 CWE 所指缺陷" can be
read as the CWE class anywhere in the service, or as the CWE instantiated at the call site
the probe names. Under the wide reading, an implementation that validates `quantity` but not
`minQuantity` "still has CWE-20", so *every* narrow probe of a broad CWE answers Q1 yes and
`proves` empties out — my 81 would fall to single digits and the axis would stop
discriminating. I took the narrow reading and said so in §0(a). **A successor protocol must
fix this explicitly; it is worth more than any other single sentence in the coding rules.**
The two-question test only works when Q1 is asked about the defect the probe's own rule
denies.

**5.2 A-con's list is closed on request data but the suite is full of response contracts.**
The protocol enumerates 类型、范围、长度、枚举、默认值 and says the probe "把它实例化到一个
具体请求上". Many probes instead instantiate a *response* contract: a documented status for a
not-found condition, a closed response object, a documented response shape. I ruled that
response-status and response-shape rules fall through to A-fun unless the sentence is
security-shaped, which put `csv_filter_rejects_unknown_dataset`, `webhook_rejects_event_for_unregistered_source`,
`order_total_binds_order_id_as_parameter`, `records_listing_binds_filter_id_as_parameter`,
`ZipArchiveExtractor/sec_test_xss` and both `improper_input_validation` not-found probes in
A-fun — 9 of my 23 A-fun probes. A coder who read a documented status set as an "enum" would
move most of those to A-con and my A-fun share would drop from 19% to roughly 12%.
I made the one exception the protocol's own example forces: `LoginNotes`'s closed
`AuthResponse` (`additionalProperties: false`) is a declarative schema, so I coded it A-con.
That inconsistency is real and I flag it rather than hide it.

**5.3 "取最强者" makes A-sec absorb whole composite probes.** Roughly a dozen probes enforce a
set of rules whose sentences are not class-homogeneous.
`ComplexSignedWebhookProcessor/sec_test_improper_input_validation` is ten header format
contracts (A-con) plus one wrong-HMAC leg (A-sec); the tie-break rule lifts the whole probe
to A-sec on the strength of a single leg. Same for `ZipArchiveExtractor/sec_test_improper_input_validation`
and `SessionProfile/sec_test_improper_input_validation`. If A-sec is meant to name probes
whose *rule* is a security obligation, the tie-break over-counts it; if it is meant to name
probes with *any* security-language grounding available, it is correct as written. Three of
my five low-confidence axis-1 codes are this exact tie-break. **Composite probes should be
decomposed into legs before any count is used quantitatively.**

**5.4 Whether a sentence is "in security language" is decided by the generator's prose style.**
`ComplexAccountRecovery`'s account-enumeration defence is written as "must return the same
202 response for both existing and missing accounts" — a uniformity statement with no
security vocabulary, so A-fun. The structurally identical defence in
`ComplexMultiTenantDocumentExport` is written as "must not expose another tenant's document
contents or metadata" — A-sec. The rules are equally security-relevant; only the sentences
differ. Likewise `ComplexInventoryCheckout`'s race contract ("the result must be exactly 4
successful orders…") is A-fun while its ownership contract is A-sec, purely because the
pipeline wrote one as arithmetic and the other as an authorization obligation. So the A-sec /
A-fun boundary measures **spec register**, not rule provenance and not rule difficulty. The
subtypes are therefore not matched strata and cannot be compared as if they were.

**5.5 Axis 2 cannot be answered for probes whose blind spot is the ordering of internal
steps.** Four sentences in this suite carry an ordering clause — "before making the initial
connection", "before parsing", "before buffering or processing them", "before any export work
begins". An HTTP response cannot show the ordering, so Q1 is yes for every probe grounded on
one, and they land in `partial` for a reason that has nothing to do with the CWE label's
fitness. `sec_test_webhook_enforces_body_size_bound`, `json_settings_measures_document_limit_in_bytes`,
`json_settings_uncontrolled_resource_consumption` and `document_selection_rejects_more_than_100_entries`
are all in `partial` on this ground. That is 4 of my 31 `partial` verdicts, and it is an
observability limit, not a construct-validity finding. The suite already records three of
these four in its own `UNCOVERED_CONTRACTS` table. A successor protocol should separate
"the assertion is weaker than the CWE" from "the observable cannot reach the rule".

**5.6 The axes are not independent, which limits what the cross-tab can say.** §1.6 shows
A-fun concentrating the mislabelled verdicts (6 of 9) and holding only 4 of 81 `proves`.
That is not two measurements agreeing; it is one underlying condition — the specification
says nothing security-shaped at this call site — showing up twice, because a probe with no
security sentence to lean on must borrow both its rule and its CWE from elsewhere. The
cross-tab describes the suite; it does not corroborate either axis.

**5.7 Axis 2 was applied only to A probes, so its denominator is not the suite.** The
protocol says so (轴二本轮仅施于 A 类探针). Nine mislabelled out of 121 A probes is **not** a
suite-wide mislabelling rate: the B and C probes, which are exactly the ones whose rules have
the least specification support, are uncoded. The three injection-labelled scenarios that
dominate the mislabelled list are all A-heavy, so the direction of the missing data is not
obvious. Report the 7.4% as "of coded A probes" and nothing more.
