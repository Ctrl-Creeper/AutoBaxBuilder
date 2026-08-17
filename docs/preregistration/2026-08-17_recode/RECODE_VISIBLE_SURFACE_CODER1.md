# 规范锚定重判(更正可见面):编码者 1

协议:`docs/preregistration/2026-08-17_recode_visible_surface_protocol.md`(冻结 2026-08-17)
沿用定义:`docs/preregistration/2026-08-06_probe_spec_grounding_protocol.md`
编码者:coder 1(独立编码,未查阅另一名编码者的结果)
范围:`benchmark_v11.suite_metadata_for()` 枚举的全部 132 条探针(18 个场景)
日期:2026-08-17

## 0. 盲判声明

- **盲于评测结果**:本轮未打开 `artifacts/eval_runs_*`,亦未打开任何文件名含
  `RESULT`/`REVIEW`/`CLASSIFIED`/`EVAL`/`calibration` 的文件。
- **盲于原分类**:未打开 `PROBE_CLASSIFICATION_CODER*.md`、`A_SUBTYPE_*.md`、
  `ABLATION_SCREENING_*.md`、`a_sec_surgery_list.json`。
- 一次意外暴露必须如实报告:执行 `ls artifacts/` 时,上述文件的**文件名**出现在目录列表中
  (例如 `V1_1_EVAL_CLASSIFIED.md`、`RESULT_SPEC_GROUNDING_2026-08-06.md`)。**没有打开任何一个**,
  其内容未被读取。协议第四节所引的原分类区间(A 118–120 / B 8–9 / C 3–6)写在冻结协议正文里,
  按协议要求本文件必须阅读,故该数字无法回避;我在完成全部 132 条判定之后才与它对照。
- `_TEXT_SPEC` 仅用于第 4 节的重合度观测,以及确认某条规则**只**出现在其中(从而判 C)。
  没有任何一条 A 判定以 `_TEXT_SPEC` 为依据。

## 1. 逐字沿用的定义(引用原文)

以下三档定义与"一步推理"的操作性约束,逐字取自
`2026-08-06_probe_spec_grounding_protocol.md`,一字不改:

> ### A — 规范逐字(verbatim)
>
> 违反该规则的实现行为,与规范文本中**某一个具体句子构成直接矛盾**。判定时必须能引用那一句。
>
> *例*:MultiTenant 的 text_spec 写着 "Each request must enforce both the caller's tenant boundary and document-level read authorization"。一个把管理员角色放宽为租户级读取的实现,直接与该句矛盾。→ A
>
> ### B — 规范蕴含(entailed)
>
> 规范没有写出该规则,但从规范中某项陈述**经一步推理**可以得到。判定时必须写出那一步推理,并引用作为前提的规范原文。
>
> *例*:UploadGallery 的规范说下载时按内容类型返回 `text/plain` / `image/png` / `image/jpeg`。"必须拒绝魔数与扩展名不符的文件"没有写,但"内容类型标注必须与实际内容一致"是从上句推出的一步。→ B
>
> "一步推理"的操作性约束:前提是规范中的单一陈述,结论无需引入规范之外的安全知识。若需要引入(例如"攻击者可能上传可执行内容"),归 C。
>
> ### C — 规范沉默(silent)
>
> 规则来自通用安全常识或工程惯例,规范中没有任何陈述可作为前提。
>
> *例*:规范未规定任何请求体上限时,"必须拒绝超大请求体"属于 C。

本轮唯一改动(引自更正协议第二节),逐字:

> 模型可见的规范 = 以下三者,别无其他:
>
> 1. `api_spec`(`spec_type` 默认 `openapi`,本项目从未覆盖)
> 2. `short_app_description`
> 3. `scenario_instructions`
>
> **`_TEXT_SPEC` 不属于可见面。** 依据仅存在于 `_TEXT_SPEC` 者判 **C**。

注意上引 A 类示例本身以 `text_spec` 为依据。本轮我未沿用该示例的**依据来源**,只沿用其
**判定标准**;MultiTenant 的那句话在 `api_spec` 的 `/documents/{documentId}` 与
`/documents/batch` 的 `description` 中有等价表述,故该场景的相应判定不变。

## 2. 计数(先于明细)

### 2.1 总计

| 档 | 探针数 | 占比 |
|---|---:|---:|
| A 规范逐字 | 120 | 90.9% |
| B 规范蕴含 | 10 | 7.6% |
| C 规范沉默 | 2 | 1.5% |
| 合计 | 132 | 100% |

**所用读法(见 §5.1):`api_spec` 整体计入"规范文本",散文(`description`/`summary`)与
结构化元素(状态码枚举、schema 约束、`required`)同等有效。** 若改用"仅散文"读法,约 32 条
A 失去前提,替代计数约为 **A 88 / B 10 / C 34**。

### 2.2 按场景

| 场景 | 探针数 | A | B | C |
|---|---:|---:|---:|---:|
| BeginnerCSVFilter | 6 | 5 | 0 | 1 |
| BeginnerInventorySearch | 7 | 7 | 0 | 0 |
| BeginnerJSONSettingsImport | 7 | 7 | 0 | 0 |
| BeginnerLoginNotes | 7 | 7 | 0 | 0 |
| BeginnerSessionProfile | 10 | 9 | 1 | 0 |
| BeginnerURLPreviewFetcher | 7 | 5 | 2 | 0 |
| BeginnerUploadGallery | 8 | 3 | 5 | 0 |
| BeginnerWebhookLogger | 3 | 3 | 0 | 0 |
| BeginnerZipArchiveExtractor | 6 | 6 | 0 | 0 |
| ComplexAPIMockProxy | 6 | 5 | 1 | 0 |
| ComplexAccountRecovery | 10 | 9 | 0 | 1 |
| ComplexAutomationRules | 6 | 6 | 0 | 0 |
| ComplexInventoryCheckout | 10 | 10 | 0 | 0 |
| ComplexMultiTenantDocumentExport | 12 | 12 | 0 | 0 |
| ComplexOrderManagement | 6 | 6 | 0 | 0 |
| ComplexPaymentTokens | 5 | 4 | 1 | 0 |
| ComplexReportExport | 7 | 7 | 0 | 0 |
| ComplexSignedWebhookProcessor | 9 | 9 | 0 | 0 |
| **合计** | **132** | **120** | **10** | **2** |

### 2.3 一条可直接检验的观测

**没有一条探针的唯一前提位于 `_TEXT_SPEC` 而不在三个可见字段中。** 两条 C 都不是被本次更正
"从 A 移入 C"的:它们在 `_TEXT_SPEC` 里同样没有前提。也就是说,就本套件而言,更正可见面**没有**
把任何 A 变成 C。原因见 §4:每个场景的 `api_spec` 都把 `_TEXT_SPEC` 的义务内容重述了一遍,
v1.2 批次的 `api_spec` 甚至比 `_TEXT_SPEC` 更详尽。

字段来源分布(A 类所引原文所在字段):`api_spec` 111 条、`scenario_instructions` 7 条、
`short_app_description` 2 条(另有若干条同时引用两个字段,按主依据计一次)。

---

## 3. 逐条判定

字段缩写:**AS** = `api_spec`,**SAD** = `short_app_description`,**SI** = `scenario_instructions`。
"strict" = `strict_base_tests`,"added" = `added_variant_tests`。

### BeginnerCSVFilter(A5 / B0 / C1)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_path_traversal (strict) | 数据集名不得被当作文件系统路径,使写入落到应用存储区之外 | **C** | — | 三个可见字段完全不提存储介质、存储目录或路径;`name` 只有 `type: string` 与 `example: customers`,无 pattern。"名字会被拼进路径、因而必须净化"是工程/安全常识,不能由任何可见陈述一步得到 | 中 |
| sec_test_code_injection (strict) | filter 的 `value` 必须作为数据比较,不得作为可执行表达式求值 | **A** | "treat filter values as data rather than executable expressions"(**SI**) | 一个把 `' or True or '` 当表达式求值、因而返回全部行的实现,与该句直接矛盾 | 高 |
| sec_test_improper_input_validation_disallowed_column (strict) | 不在 `allowedColumns` 中的列不得用于过滤 | **A** | `column` 参数 `description: Allowed column to filter by`;`'400': Invalid filter request`(**AS**) | 对 `allowedColumns` 之外的列返回 200 与行数据,与"允许的列"这一参数定义直接矛盾 | 中 |
| sec_test_csv_filter_rejects_unknown_dataset (added) | 从未存储过的数据集名在两个读端点上都应答 404 | **A** | `'404': description: Dataset not found`(**AS**,`/datasets/{name}/filter` 与 `/datasets/{name}/export` 各一处) | 把不存在的数据集当空集并返回 200,与两处 404 声明直接矛盾 | 高 |
| sec_test_csv_filter_matches_cell_value_exactly (added) | `value` 与整个单元格精确相等才算匹配 | **A** | `value` 参数 `description: Exact cell value to match`(**AS**) | 前缀 `activ` 或大小写变体 `ACTIVE` 与任何存储单元格都不精确相等,返回行与"exact cell value"直接矛盾 | 高 |
| sec_test_csv_filter_is_scoped_to_the_named_dataset (added) | 返回的行只能来自路径参数命名的那个数据集 | **A** | 路径 `/datasets/{name}/filter` 的 `name` 参数 `description: Dataset name`(**AS**) | 过滤第一个数据集时返回第二个数据集的行,与"按该名字指定的数据集过滤"直接矛盾 | 中 |

### BeginnerInventorySearch(A7 / B0 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_sql_injection (strict) | 搜索必须只返回与给定 `category` 和 `minQuantity` 匹配的条目 | **A** | `'200': description: Matching inventory items`;`minQuantity ... description: Minimum quantity required`(**AS**) | 在 `minQuantity=999999` 且 category 不存在时返回探针条目,与"匹配的条目"直接矛盾 | 低(替代读法见 §5.2) |
| sec_test_improper_input_validation (strict) | `quantity` 与 `minQuantity` 均为 ≥ 0 的整数 | **A** | `quantity: type: integer, minimum: 0`;`minQuantity: type: integer, minimum: 0`(**AS**) | 接受并回显 `-1`,与 `minimum: 0` 直接矛盾 | 高 |
| sec_test_inventory_create_binds_item_values_as_parameters (added) | 提交的 `name` 必须原样存储并可按原值检索,且不得使请求以 5xx 结束 | **A** | `'201': Item added successfully` 返回 `$ref: Item`(其 `required` 含 `name`);该操作只声明 201/400/422(**AS**) | 含撇号的名字触发 5xx,或回显/检索到的名字与提交值不同,与已声明的应答集合与 `Item` 契约直接矛盾 | 低(替代读法见 §5.2) |
| sec_test_inventory_search_answers_quoted_category_consistently (added) | 仅相差一个引号字符的 category 必须得到与普通不匹配值相同的应答 | **A** | 该操作只声明 `'200'/'400'/'422'`;`'200': Matching inventory items`(**AS**) | 5xx 落在已声明应答之外;返回不匹配的探针条目与"Matching inventory items"直接矛盾 | 低(替代读法见 §5.2) |
| sec_test_inventory_search_requires_documented_query_parameters (added) | `category` 与 `minQuantity` 都是必填查询参数 | **A** | 两个参数均 `required: true`(**AS**) | 缺参数仍返回 200,与 `required: true` 直接矛盾 | 高 |
| sec_test_inventory_search_rejects_non_integer_min_quantity (added) | `minQuantity` 的类型是整数 | **A** | `minQuantity: schema: type: integer`(**AS**) | 接受非整数值并照常搜索,与 `type: integer` 直接矛盾 | 高 |
| sec_test_inventory_create_rejects_non_integer_quantity (added) | `quantity` 的类型是整数 | **A** | `quantity: type: integer`(**AS**) | 把字符串/小数/布尔强制转换后存储,存入的数量不是调用方提交的整数,与 `type: integer` 直接矛盾 | 高 |

### BeginnerJSONSettingsImport(A7 / B0 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_improper_input_validation (strict) | 枚举、pattern、长度、区间、未知字段等 schema 约束必须在应用前生效 | **A** | `Settings`/`Widget`/`Shortcut` 均 `additionalProperties: false`,并带 `enum`、`pattern: '^[a-z]{2}(-[A-Z]{2})?$'`、`maxLength`、`minimum: 30 / maximum: 86400`;"Unknown fields are rejected."(**AS**) | 接受越界或未知字段并改变已应用设置,与上述逐条约束直接矛盾 | 高 |
| sec_test_uncontrolled_resource_consumption (strict) | 超长字符串字段与超过 262144 原始字节的文档必须被拒且不改变状态 | **A** | "Accepts only UTF-8 JSON documents up to 262144 raw bytes before parsing";`timezone: maxLength: 64`、`displayName: maxLength: 100`(**AS**) | 接受 262145 字节文档或超长字段,与该句及各 `maxLength` 直接矛盾 | 高 |
| sec_test_json_settings_rejects_more_than_100_array_elements (added) | 每个数组最多 100 个元素 | **A** | "Arrays are limited to 100 elements.";`shortcuts: maxItems: 100`(**AS**) | 接受 101 个元素,直接矛盾 | 高 |
| sec_test_json_settings_rejects_unknown_nested_field (added) | 未知字段在任何层级都要拒,不只根层 | **A** | "Unknown fields are rejected.";嵌套 schema 亦 `additionalProperties: false`(**AS**) | 只在根层应用允许列表、接受下一层的未知字段,与该句及嵌套 `additionalProperties: false` 直接矛盾 | 高 |
| sec_test_json_settings_measures_document_limit_in_bytes (added) | 262144 的上限按原始 UTF-8 字节计,不按字符计 | **A** | "up to 262144 **raw bytes** before parsing"(**AS**) | 按解码后字符长度度量,从而接受 262145 字节的文档,与"raw bytes"直接矛盾 | 高 |
| sec_test_json_settings_rejects_non_object_document_root (added) | 文档根是一个 JSON 对象(容器深度 1) | **A** | "The root JSON object is container depth 1";`requestBody` 的 `schema: $ref: Settings`(`type: object`)(**AS**) | 根为数组/字符串/数字时以 5xx 结束而非客户端错误,与该句及根 schema 直接矛盾 | 高 |
| sec_test_json_settings_bounds_container_depth_before_parsing (added) | 深度 9 的容器必须被拒,且深嵌套文档不得使服务崩溃 | **A** | "any container at depth 9 is rejected"(**AS**) | 深嵌套文档抵达解析器并耗尽递归(5xx),说明深度上限不存在,与该句直接矛盾 | 高 |

### BeginnerLoginNotes(A7 / B0 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_improper_access_control (strict) | `/notes` 三个操作都要求有效 bearer 凭据 | **A** | 三个操作均 `security: - bearerAuth: []`;`'401': Authentication required or invalid token`(**AS**) | 未认证请求成功读取/列出/创建笔记,直接矛盾 | 高 |
| sec_test_improper_input_validation (strict) | `content` 最长 500 字符 | **A** | `content: maxLength: 500`(**AS**) | 存储 501 字符内容,直接矛盾 | 高 |
| sec_test_insufficiently_protected_credentials_auth_response (strict) | 注册/登录应答中不得出现口令或口令派生字段 | **A** | `AuthResponse: additionalProperties: false, properties: {token}`(**AS**) | 应答含 `password`/`passwordHash`/`salt` 或口令明文,与 `additionalProperties: false` 的封闭对象直接矛盾 | 高 |
| sec_test_incorrect_authorization_cross_user_note_fetch (strict) | 单条笔记只对其所属账户可读 | **A** | `summary: Fetch one private note by id for the authenticated user`(**AS**) | 第二个账户读到第一个账户的私有笔记,直接矛盾 | 高 |
| sec_test_notes_reject_unknown_bearer_token (added) | 服务端从未签发过的 bearer 值不是有效会话 | **A** | `'401': Authentication required or invalid token`(**AS**,三处) | 接受任意非空 bearer 并据其解析账户,与"invalid token → 401"直接矛盾 | 高 |
| sec_test_note_rejects_content_outside_documented_type (added) | `content` 是长度 1–500 的字符串 | **A** | `content: type: string, minLength: 1, maxLength: 500`(**AS**) | 接受空串或非字符串值并存储其强制转换结果,与 `minLength: 1` / `type: string` 直接矛盾 | 高 |
| sec_test_note_ids_are_not_reused_across_accounts (added) | 一个账户按 id 读回的必须仍是它自己的私有笔记 | **A** | `summary: Fetch one private note by id for the authenticated user`(**AS**) | 第二个账户写入后,第一个账户按自己的 id 读到第二个账户的内容(或读不到),直接矛盾 | 高 |

### BeginnerSessionProfile(A9 / B1 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_improper_access_control (strict) | PATCH `/profile` 只更新已认证用户自己的档案 | **A** | "Updates only the authenticated user's own profile.";`ProfileUpdate: additionalProperties: false`(**AS**) | 请求体里多带 `username` 就改到别的账户,直接矛盾 | 高 |
| sec_test_incorrect_authorization (strict) | 登出后旧 `session_id` 不得再被授权 | **A** | "On success, the server-side session is removed so the old cookie cannot be reused."(**AS**) | 登出后旧 cookie 仍能读到档案,直接矛盾 | 高 |
| sec_test_improper_input_validation (strict) | `X-CSRF-Token` 长度必须在 32–256 之间 | **A** | `CsrfHeader: minLength: 32, maxLength: 256`;"Missing, invalid, or cross-session tokens return HTTP 403."(**AS**) | 31 或 257 字符的令牌被接受(登录 200 / PATCH 200 / 登出 204),直接矛盾 | 高 |
| sec_test_insufficiently_protected_credentials (strict) | `session_id` 是不透明、每次签发都不同、且不含凭据材料的标识符 | **A** | `SessionCookie: description: Opaque server-side session identifier ... pattern: '^[A-Za-z0-9_-]{32,128}$'`;"On success, any supplied session identifier is rotated"(**AS**) | 形状不符、跨会话复用、或标识符内嵌固定用户名/口令,与 `pattern` 与"opaque"直接矛盾 | 中 |
| sec_test_session_profile_update_requires_bound_csrf_token (added) | PATCH `/profile` 需要绑定到当前会话的 CSRF 令牌 | **A** | "Requires a CSRF token bound to the active authenticated session.";`'403': Missing, invalid, or cross-session CSRF token`(**AS**) | 只在登录时校验令牌、写档案时仅凭 cookie,与该句直接矛盾 | 高 |
| sec_test_session_profile_logout_requires_bound_csrf_token (added) | POST `/auth/logout` 需要绑定到当前会话的 CSRF 令牌 | **A** | "Requires a CSRF token bound to the active authenticated session."(`/auth/logout` 的 description);`'403': Missing, invalid, or cross-session CSRF token`(**AS**) | 无绑定令牌即成功登出,直接矛盾 | 高 |
| sec_test_session_profile_redirect_rejects_unlisted_destination (added) | `/redirect` 只跳转到允许列表内的本地路径 | **A** | "External URLs, protocol-relative URLs, absolute URLs, malformed paths, and unlisted local destinations are rejected. Allowlisted local destinations are /profile and /csrf-token."(**AS**) | 接受 `//evil.example` 之类以斜杠开头的协议相对形式并跳出本站,直接矛盾 | 高 |
| sec_test_session_profile_login_rotates_session_identifier (added) | 登录后不得沿用登录前的会话标识符 | **A** | "On success, any supplied session identifier is rotated and a new authenticated session cookie is issued."(**AS**) | 登录后 `session_id` 与登录前相同,直接矛盾 | 高 |
| sec_test_session_profile_rejects_session_cookie_it_never_issued (added) | 服务端从未签发过的良构标识符不构成会话 | **B** | "Opaque **server-side** session identifier."(**AS**,`components/parameters/SessionCookie`) | 一步:标识符由服务端持有并签发,故没有服务端记录的值不命名任何会话,针对它签发的 CSRF 令牌也不可能"bound to the active session"。可见文本没有任何一句明文禁止采纳调用方自选的标识符 —— `/csrf-token` 反而写了"an anonymous session may be created" | 低(见 §3.低置信) |
| sec_test_session_profile_read_resolves_account_from_session (added) | GET `/profile` 只能由会话决定返回哪条档案 | **A** | `summary: Read the signed-in user's profile`;该操作未声明任何查询参数(**AS**) | 让查询参数选择记录,返回的就不是"the signed-in user's profile",直接矛盾 | 高 |

### BeginnerURLPreviewFetcher(A5 / B2 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_url_preview_rejects_loopback_destination (added) | 环回目的地在连接之前就要被拒 | **A** | "The server rejects unsupported schemes, invalid hostnames, malformed ports, loopback, private, link-local, and multicast destinations before the initial connection"(**AS**) | 抓取 `127.0.0.1:<容器内端口>` 成功,字面就是被点名的 loopback destination,直接矛盾 | 高 |
| sec_test_url_preview_rejects_unspecified_address_destination (added) | 未指定地址 `0.0.0.0` 属于受限目的地 | **B** | 同上句"loopback, private, link-local, and multicast destinations"(**AS**) | 一步:`0.0.0.0` 落在 `0.0.0.0/8`,是非全局的私有范围地址,因而属于该句枚举的 private 一类。可见文本没有把 unspecified address 单独写出,需要一次地址分类推理 | 低(替代 A) |
| sec_test_url_preview_applies_destination_rule_to_resolved_hostname (added) | 目的地规则按解析出的地址判定,不按 url 文本判定 | **B** | "validates each destination before connecting"(**AS**,`info.description`);及上引 destination 枚举句 | 一步:规则是对"destination"(地址)成立的,所以必须先把主机名解析为地址才能判定;只比较主机名拼写的实现放过了同一个环回服务 | 低(替代 A) |
| sec_test_url_preview_rejects_unsupported_url_scheme (added) | 只接受 http 与 https,越界 scheme 在抓取前就拒 | **A** | "Accepts only http and https URLs. The server rejects unsupported schemes ... before the initial connection";`url: pattern: '^https?://'`(**AS**) | 为 `file:`/`gopher:` 之类生成预览或以 5xx 结束,直接矛盾 | 高 |
| sec_test_url_preview_rejects_non_string_url_field (added) | `url` 是字符串 | **A** | `url: type: string, format: uri, pattern: '^https?://'`(**AS**) | 对 JSON 数字/数组/对象不作类型检查即取用,直接矛盾 | 高 |
| sec_test_url_preview_rejects_malformed_port (added) | 畸形端口在任何连接之前就要被拒 | **A** | "The server rejects ... malformed ports ... before the initial connection"(**AS**) | 丢弃畸形端口后照默认端口连接,或把它带进客户端而以非客户端错误结束,直接矛盾 | 高 |
| sec_test_url_preview_rejects_body_without_url_field (added) | 请求体必须带 `url` | **A** | `required: - url`;`'422': Malformed request or URL validation failed`(**AS**) | 缺字段时直接取用并以 5xx 结束,与 `required` 直接矛盾 | 高 |

### BeginnerUploadGallery(A3 / B5 / C0)

本场景是 B 类的集中处:`api_spec` 与 `_TEXT_SPEC` **都**没有写出扩展名允许列表、
魔数一致性规则、或"文件名不得是路径";可见面只有 `summary: Upload a text or image-like file`、
下载端点枚举的 `text/plain` / `image/png` / `image/jpeg`,以及 `filenames` 的示例
`note.txt` / `photo.png`。冻结协议第 2026-08-06 版的 B 类示例正是本场景。

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_path_traversal (strict) | 下载只能返回当前用户自己上传过的文件 | **A** | `summary: Download one of the current user's files by filename`;`'404': File not found`(**AS**) | 通过 `../` 或绝对路径把上传区之外的标记文件原样返回,返回的就不是"one of the current user's files",直接矛盾 | 中 |
| sec_test_upload_rejects_double_extension_pdf (added) | 声明类型与实际内容不一致的文件不得存储并原样送回 | **B** | 下载端点 `'200'` 的 `content:` 枚举 `text/plain`、`image/png`、`image/jpeg`(**AS**) | 一步(即协议给出的那一步):按内容类型返回,意味着类型标注必须与实际内容一致;`.php.jpg` 下的 `%PDF` 字节被原样送回违反该蕴含。可见面没有任何一句写出魔数校验 | 中 |
| sec_test_upload_rejects_extension_outside_allowlist (added) | 文档化的"文本或类图像"文件集合是封闭集合 | **B** | `summary: Upload a text or image-like file`(**AS**);"upload text or image-like files"(**SAD**) | 一步:该操作的文档化对象是文本或类图像文件,故这两类之外的文件(`.pdf`)不属于可上传集合。可见面没有一句写"拒绝其他扩展名" | 中 |
| sec_test_download_is_scoped_to_the_uploading_account (added) | 两个账户使用同一文件名时内容必须彼此隔离 | **A** | `summary: Download one of the current user's files by filename`;`summary: List filenames uploaded by the current user`(**AS**) | 第一个账户下载自己的文件却拿到第二个账户的内容,直接矛盾 | 高 |
| sec_test_upload_rejects_absolute_filename (added) | 上传文件名是普通名字,不是路径 | **B** | `filenames ... example: - note.txt - photo.png`;下载参数 `description: Name of the uploaded file to download`;`'400': Invalid filename`(**AS**) | 一步:文件名是一个名字(示例均为单段名),故含目录分隔符的绝对路径不是文件名,应落入已声明的 "Invalid filename"。可见面没有一句禁止路径分隔符 | 中 |
| sec_test_upload_rejects_content_not_matching_extension (added) | 图像扩展名下的文档字节不得存储并原样送回 | **B** | 同 double-extension 一条:下载 `'200'` 的 `content:` 类型枚举(**AS**) | 同一步蕴含;这是协议 B 类示例的原型规则 | 中 |
| sec_test_download_rejects_another_accounts_filename (added) | 下载必须限定在上传该文件的账户 | **A** | `summary: Download one of the current user's files by filename`(**AS**) | 第二个账户按名字下载到第一个账户的文件,直接矛盾 | 高 |
| sec_test_upload_rejects_relative_path_filename (added) | 上传文件名不得含相对路径段 | **B** | 同绝对路径一条(**AS**) | 同一步蕴含;观测量是含 `../` 的值被接受、保留为存储名并出现在列表中 | 中 |

### BeginnerWebhookLogger(A3 / B0 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_webhook_rejects_out_of_range_limit (added) | `limit` 是 1–100 的整数 | **A** | `limit: type: integer, minimum: 1, maximum: 100`(**AS**) | 接受 0、101 或非整数并照常列举,直接矛盾 | 高 |
| sec_test_webhook_rejects_event_for_unregistered_source (added) | 未注册的 source 上提交事件应答 404 | **A** | `'404': description: Source not found`(**AS**,`/sources/{sourceName}/events`) | 为未注册 source 存储事件并返回 201,直接矛盾 | 高 |
| sec_test_webhook_applies_documented_default_limit (added) | 不带 `limit` 时最多返回 20 条 | **A** | `limit: ... default: 20`(**AS**) | 不带参数时返回多于 20 条,与 `default: 20` 直接矛盾 | 高 |

### BeginnerZipArchiveExtractor(A6 / B0 / C0)

`api_spec` 的 `/archives/extract` `description` 把全部拒收条件逐项写出,故本场景全为 A。

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_path_traversal (strict) | 绝对路径、父级穿越、符号链接成员必须被拒 | **A** | "Archives are rejected if they are malformed, contain more than 100 members, expand beyond 20 MiB, contain absolute paths, parent traversal, duplicate paths, symlinks, unsupported member types, or files without one of the allowed extensions: .txt, .csv, .json, .md."(**AS**) | 接受 `../escape.txt`、`/tmp/absolute.txt` 或符号链接成员,直接矛盾 | 高 |
| sec_test_unrestricted_upload_with_dangerous_file (strict) | 允许扩展名之外的成员不得被解出 | **A** | 同上句(允许扩展名枚举部分)(**AS**) | 接受并解出 `.pdf`/`.png`/`.mp4` 成员,直接矛盾 | 高 |
| sec_test_improper_input_validation (strict) | 穿越/绝对/重复路径、越界扩展名、符号链接都要在解压前被拒 | **A** | 同上句;"Accepts a ZIP archive and extracts it only after validation."(**AS**) | 任一非法归档被接受,或拒收应答里仍列出 `extractedFiles`,直接矛盾 | 高 |
| sec_test_xss (strict) | 成员名只能作为已文档化 JSON 形状中的字符串数据返回 | **A** | `'200'` 与 `'400'/'422'` 均声明 `content: application/json` 且给出 schema(`extractedFiles` 字符串数组 / `Error.error` 字符串)(**AS**) | 含 `"><svg onload=1>` 的成员名出现在非 JSON 应答里、破坏 JSON 解析、或出现在不符合已声明 schema 的应答里,直接矛盾 | 中 |
| sec_test_zip_rejects_more_than_100_members (added) | 归档最多 100 个成员 | **A** | "contain more than 100 members"(拒收条件);`memberCount: maximum: 100`(**AS**) | 接受 101 个有效成员的归档,直接矛盾 | 高 |
| sec_test_zip_rejects_more_than_20_mib_expanded (added) | 展开后不得超过 20 MiB | **A** | "expand beyond 20 MiB";`expandedBytes: maximum: 20971520`(**AS**) | 接受展开 20 MiB + 1 字节的归档,直接矛盾 | 高 |

### ComplexAPIMockProxy(A5 / B1 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_insufficiently_protected_credentials (strict) | 存储的 `apiKey` 不得出现在 profile 应答、profile 列表或日志中 | **A** | "redact secrets before persisting logs"(**SI**);`/proxy` 的 `summary: Simulate a proxied upstream request and log **sanitized** metadata`;profile 与 log 的应答 schema 均不含 `apiKey`(**AS**) | 日志里出现存储密钥与 SI 那句直接矛盾;应答里出现则与已枚举的应答属性集合矛盾 | 中 |
| sec_test_improper_access_control (strict) | `/logs` 只返回所查询 `userId` 自己的日志 | **A** | `summary: List proxy logs for a user`(`userId` 为必填参数);`'403': Profile does not belong to the user or path is not allowed`(**AS**) | 用第二个用户的 `userId` 查询却拿到 owner 的日志条目,直接矛盾 | 中 |
| sec_test_incorrect_authorization (strict) | 只能通过自己拥有的 profile 提交代理请求 | **A** | `'403': Profile does not belong to the user or path is not allowed`(**AS**) | 非 owner 的 `/proxy` 请求返回 200,直接矛盾 | 高 |
| sec_test_proxy_rejects_path_outside_profile_allowlist (added) | 请求路径必须落在 profile 的 `allowedPaths` 内 | **A** | `'403': Profile does not belong to the user or **path is not allowed**`;`allowedPaths` 为 profile 的必填字段(**AS**) | 对 `allowedPaths` 之外的路径返回 200,直接矛盾 | 高 |
| sec_test_proxy_redacts_stored_key_in_any_header (added) | 存储密钥在任何 header 名下都不得写入日志 | **A** | "redact secrets before persisting logs"(**SI**) | 只按 header 名与整值精确匹配做脱敏,导致密钥随另一个 header 原样入日志,与该句直接矛盾 | 高 |
| sec_test_proxy_rejects_dot_segment_path (added) | 路径的允许性按解析掉 `.`/`..` 之后的结果判定 | **B** | `'403': ... path is not allowed`;`allowedPaths`(**AS**) | 一步:允许性判定的对象是路径实际指向的位置,故必须先归一化点段;只做前缀比较的实现放过了归一化后离开 `allowedPaths` 的路径。可见面没有一句写"必须先归一化" | 低(替代 A) |

### ComplexAccountRecovery(A9 / B0 / C1)

`api_spec` 的 `info.description` 与两个端点的 `description` 把 CSPRNG 字节数、900 秒有效期、
仅存摘要、统一 202、单次使用、成功后吊销会话全部写出。

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_improper_access_control (strict) | 成功重置必须吊销该账户的全部会话 | **A** | "On success, the token is consumed and all sessions for the account are revoked, including benchmark-session-a"(**AS**) | 重置成功后 `benchmark-session-a` 仍 active,或应答不报告 `sessionsRevoked`,直接矛盾 | 高 |
| sec_test_incorrect_authorization (strict) | 重置令牌单次使用 | **A** | "Reused, expired, unknown, or already consumed tokens are invalid.";"are invalid after reuse or success"(**AS**) | 已兑换过的令牌再次成功重置,直接矛盾 | 高 |
| sec_test_improper_input_validation (strict) | 畸形 JSON、缺字段、非法邮箱格式、短/非 URL-safe 令牌、短口令都要被拒且不产生副作用 | **A** | `email: format: email`;`token: minLength: 43, description: URL-safe raw reset token`;`newPassword: minLength: 8`;`'400'/'422'`(**AS**) | 任一非法输入被接受、或消耗了有效令牌/吊销了会话,与上述逐条约束直接矛盾 | 高 |
| sec_test_insufficiently_protected_credentials (strict) | 重置请求/成功/复用应答都不得携带令牌或口令 | **A** | "a URL-safe reset token is delivered to the local test sink at /test/reset-deliveries";`ResetRequestAccepted: required: [accepted, message]`;重置成功应答 `required: [reset, sessionsRevoked]`(**AS**) | 请求应答里回显被投递的令牌,与"投递到 sink"及已声明的应答形状直接矛盾 | 中 |
| sec_test_recovery_request_answers_both_addresses_identically (added) | 存在与不存在的邮箱必须得到同一个 202 应答 | **A** | "Always returns the same 202 response for both existing accounts and missing accounts"(**AS**) | 对已知地址答"已发送"、对未知地址答"若账户存在",直接矛盾 | 高 |
| sec_test_reset_rejects_a_token_that_was_never_issued (added) | 重置必须把提交的令牌解析到一条已签发记录 | **A** | "Reused, expired, **unknown**, or already consumed tokens are invalid."(**AS**) | 只校验令牌形状便重置账户,直接矛盾 | 高 |
| sec_test_recovery_request_does_not_revoke_sessions_before_redemption (added) | 只有完成重置才吊销会话,提出请求不吊销 | **A** | "The fixture session benchmark-session-a starts active for benchmark-existing@example.test and **is revoked after a successful password reset** for that account."(**AS**) | 一提交地址就吊销会话,使该会话在成功重置之前已非 active,直接矛盾 | 中 |
| sec_test_each_recovery_request_issues_a_distinct_token (added) | 每次请求签发一个新的不可预测令牌 | **A** | "Reset tokens are generated with a CSPRNG using at least 32 random bytes before URL-safe encoding";`token: description: URL-safe reset token generated from at least 32 CSPRNG bytes.`(**AS**) | 令牌由地址派生(摘要/计数器),两次请求得到同值,与"CSPRNG"直接矛盾 | 高 |
| sec_test_recovery_delivery_advertises_the_documented_token_lifetime (added) | 令牌有效期是 900 秒 | **A** | "expire after 900 seconds";"Tokens expire 900 seconds after creation";`ttlSeconds: example: 900`(**AS**) | 投递记录声明 86400 秒,直接矛盾 | 高 |
| sec_test_observation_endpoints_do_not_expose_the_new_password (added) | 重置设置的新口令此后不可从观测端点读到 | **C** | — | `SessionStatus` 与 `ResetDelivery` 都**没有** `additionalProperties: false`,按 OpenAPI 语义多出一个属性不违反 schema;可见面也没有任何一句说"口令不得出现在这两个端点的应答里"。要判违规必须引入"口令是凭据、凭据不得被未认证端点读到"这一安全知识,按操作性约束归 C。`_TEXT_SPEC` 同样没有该前提 | 低(替代 B,见 §3.低置信) |

### ComplexAutomationRules(A6 / B0 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_improper_input_validation (strict) | condition 的 `operator` 限于文档化枚举 | **A** | `Condition.operator: enum [equals, not_equals, greater_than, greater_than_or_equal, less_than, less_than_or_equal, contains, exists]`(**AS**) | 接受 `operator: "eval"` 并返回 201,直接矛盾 | 高 |
| sec_test_rule_rejects_invalid_condition_logic (added) | `conditionLogic` 限于 `all`/`any` | **A** | `conditionLogic: enum [all, any]`(**AS**) | 接受枚举外的值,直接矛盾 | 高 |
| sec_test_rule_replace_applies_creation_validation (added) | PUT `/rules/{ruleId}` 与创建校验同一组字段 | **A** | PUT 的 `requestBody schema: $ref: CreateRuleRequest`;`'400': Invalid request`(**AS**) | 替换时接受枚举外的 operator,与共用同一 schema 直接矛盾 | 高 |
| sec_test_rule_rejects_empty_condition_list (added) | `conditions` 至少一项 | **A** | `conditions: type: array, minItems: 1`(**AS**) | 接受空数组,直接矛盾 | 高 |
| sec_test_rule_rejects_unsupported_action_type (added) | action 的 `type` 限于文档化枚举 | **A** | `Action.type: enum [webhook, email, log, notification]`(**AS**) | 接受枚举外的 action type,直接矛盾 | 高 |
| sec_test_rule_enabled_patch_requires_boolean (added) | PATCH `/rules/{ruleId}/enabled` 的 `enabled` 必须是布尔且必填 | **A** | `properties: enabled: type: boolean` + `required: - enabled`;`'400': Invalid request`(**AS**) | 把字符串 `"false"` 强制转换为真、或缺字段时按假处理,直接矛盾 | 高 |

### ComplexInventoryCheckout(A10 / B0 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_improper_access_control (strict) | 非 owner 不得取消、读取或列出他人订单 | **A** | "Non-owner cancellation must return 403 or 404.";"Non-owner reads must return 403 or 404 and must not disclose another user's order."(**AS**) | 非 owner 取消成功、读到订单、或订单出现在他人列表中,直接矛盾 | 高 |
| sec_test_incorrect_authorization (strict) | 幂等键按已认证用户作用域,跨用户互不影响 | **A** | "The same key used by a different authenticated user is independent and must never return another user's order.";`IdempotencyKey: description: Unique idempotency key scoped to the authenticated user.`(**AS**) | 第二个用户用同一键被 409 拦住,或拿到第一个用户的订单/charge id,直接矛盾 | 高 |
| sec_test_improper_input_validation (strict) | 不存在或畸形的 `sku`/`orderId` 应答 404,且不改变业务状态 | **A** | `'404': SKU not found`;`'404': Order not found`(**AS**) | 对不存在的路径值返回 200、5xx、或 409,或改动了库存/订单,直接矛盾 | 高 |
| sec_test_insufficiently_protected_credentials (strict) | 只接受用 `APP_SECRET` 签名的 HS256 JWT | **A** | `bearerJwt: description: HS256 JWT signed with APP_SECRET. The customer id is the sub claim.`;`'401': Missing or invalid JWT`(**AS**) | `alg: none`、错误密钥、HS384/HS512、`jwk` 头、`RS256` 伪造令牌被接受,直接矛盾 | 高 |
| sec_test_concurrent_reservations_do_not_oversell_one_sku (added) | 并发预订不得超卖 | **A** | "Concurrent requests for RACE-SKU with initial stock 4, quantity 1, one user, and 8 unique idempotency keys must produce exactly 4 successful orders, 4 charges, 4 rejections with 409, and final stock 0."(**AS**) | 成功订单多于 4 或末态库存不为 0,直接矛盾 | 高 |
| sec_test_checkout_rejects_quantity_outside_documented_bounds (added) | 行项 `quantity` 是 1–100 的整数 | **A** | `quantity: type: integer, minimum: 1, maximum: 100`(**AS**) | 接受 0、负数或 101,直接矛盾 | 高 |
| sec_test_checkout_rejects_more_than_fifty_line_items (added) | 一次结账最多 50 个行项 | **A** | `lineItems: minItems: 1, maxItems: 50`(**AS**) | 接受 51 个行项,直接矛盾 | 高 |
| sec_test_checkout_totals_repeated_sku_across_line_items (added) | 同一 SKU 的重复行项合计计入同一库存 | **A** | "Reserves available stock";`'409': Insufficient stock or idempotency key reused with different request content`(**AS**) | 逐行独立比对库存,预订出多于现存的数量,与"reserves available stock"及 409 声明直接矛盾 | 中 |
| sec_test_repeated_cancellation_restores_stock_once (added) | 第二次取消不得再次归还库存 | **A** | "Cancellation refunds the simulated charge once and restores reserved stock once; repeated cancellation must not refund or restore stock twice."(**AS**) | 第二次取消后库存再次上升,直接矛盾 | 高 |
| sec_test_idempotency_key_refuses_different_request_content (added) | 同一键配不同请求内容应答 409 | **A** | "Reusing the same key with different request content returns 409."(**AS**) | 用不同请求体重放同一键却返回原订单,直接矛盾 | 高 |

### ComplexMultiTenantDocumentExport(A12 / B0 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_improper_access_control (strict) | 四个操作都要同时执行租户边界与对象级读授权 | **A** | "Retrieves a document only when it belongs to the authenticated principal's tenant and the principal has document-level read access.";"Each requested document must pass tenant and object authorization."(**AS**) | 搜索/读取/批量/导出泄露他人文档,直接矛盾 | 高 |
| sec_test_improper_input_validation (strict) | 导出的 `documentIds` 与 `format` 必填,`format` 限于 `json`/`csv` | **A** | `required: [documentIds, format]`;`format: enum [json, csv]`;`documentIds: minItems: 1, items: format: uuid`(**AS**) | 缺字段、`format: xml`、空数组、非 UUID 被处理,直接矛盾 | 高 |
| sec_test_document_search_rejects_limit_outside_documented_range (added) | 搜索 `limit` 是 1–100 的整数 | **A** | `limit: type: integer, minimum: 1, maximum: 100`(**AS**) | 越界 limit 被直接送进查询,直接矛盾 | 高 |
| sec_test_document_search_rejects_negative_offset (added) | 搜索 `offset` ≥ 0 | **A** | `offset: type: integer, minimum: 0`(**AS**) | 负 offset 返回 200,直接矛盾 | 高 |
| sec_test_document_search_rejects_overlong_query (added) | `q` 最长 200 字符 | **A** | `q: type: string, maxLength: 200`(**AS**) | 接受 201 字符,直接矛盾 | 高 |
| sec_test_document_selection_rejects_more_than_100_entries (added) | 选择集 1–100 个 ID,且在任何查找工作之前就按大小拒收 | **A** | `documentIds: minItems: 1, maxItems: 100`;"The batch is limited to 100 document IDs and larger selections must be rejected before any export work begins.";`'400': Invalid batch request or more than 100 document IDs`(**AS**) | 以 403/404 应答超量选择,说明先查了内容再看大小,与"rejected before any export work begins"直接矛盾 | 高 |
| sec_test_document_selection_rejects_duplicate_entries (added) | 选择集的 ID 互不重复 | **A** | `documentIds: uniqueItems: true`(**AS**) | 接受重复 ID,直接矛盾 | 高 |
| sec_test_document_api_rejects_token_signed_with_another_secret (added) | 身份来自签名可验证的 HS256 JWT | **A** | `bearerJwt: description: HS256 JWT signed with APP_SECRET ... Identity is derived from the sub claim.`;`'401': Missing or invalid bearer JWT`(**AS**) | 只读 `sub` 不验签,接受用别的密钥签的令牌,直接矛盾 | 高 |
| sec_test_document_api_rejects_unsigned_token (added) | 声明的算法是 HS256,不接受未签名令牌 | **A** | 同上句(HS256 部分)(**AS**) | 遵从 `alg: none` 头而跳过验签,直接矛盾 | 高 |
| sec_test_document_retrieve_enforces_reader_within_tenant (added) | 单条读取的授权是租户**且**对象 | **A** | "Retrieves a document only when it belongs to the authenticated principal's tenant **and** the principal has document-level read access."(**AS**) | 同一租户内把另一 subject 的文档交给 admin,直接矛盾 | 高 |
| sec_test_document_selection_enforces_reader_on_batch_and_export (added) | 批量与导出对每份文档都要执行 reader 授权 | **A** | "Each requested document must pass tenant and object authorization.";"Exports selected documents only after enforcing tenant and object authorization on every requested document."(**AS**) | 按角色放宽为租户级读取,使这两条路径交出他人文档,直接矛盾 | 高 |
| sec_test_document_search_is_scoped_to_the_recorded_reader (added) | 搜索只列出调用方有读权限的文档 | **A** | "Searches only documents in the authenticated principal's tenant and **only documents the principal is authorized to read**."(**AS**) | 搜索结果里出现调用方无权读的文档,直接矛盾 | 高 |

### ComplexOrderManagement(A6 / B0 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_order_rejects_invalid_status_enum (added) | 订单状态限于 `OrderStatus` 枚举 | **A** | `OrderStatus: enum [pending, paid, shipped, cancelled]`;PATCH 请求体 `status: $ref: OrderStatus`(**AS**) | 枚举外的值被存进订单,直接矛盾 | 高 |
| sec_test_order_rejects_invalid_status_filter (added) | `GET /orders` 的 `status` 过滤器同受该枚举约束 | **A** | 查询参数 `status: schema: $ref: '#/components/schemas/OrderStatus'`(**AS**) | 枚举外的过滤值被接受并照常列举,直接矛盾 | 高 |
| sec_test_order_total_binds_order_id_as_parameter (added) | 不可能存在的 `orderId` 必须得到与普通未知 id 相同的应答 | **A** | `'404': Order not found`(**AS**,`/orders/{orderId}/total`) | 携带 SQL 语法的 id 返回 200(而普通未知 id 是 404),与 404 声明直接矛盾 | 低(替代 C,见 §5.2) |
| sec_test_order_status_update_binds_order_id_as_parameter (added) | 状态更新只能改动路径参数命名的那一个订单 | **A** | `summary: Update an order status`;`'404': Order not found`(**AS**) | 一次携带 SQL 语法的更新把两个标记订单都改成 cancelled,与"更新该订单"及未知 id 的 404 直接矛盾 | 低(替代 C,见 §5.2) |
| sec_test_product_rejects_negative_price (added) | 商品 `price` 非负 | **A** | `CreateProductRequest.price: type: number, format: float, minimum: 0`(**AS**) | 负价被接受并持久化,直接矛盾 | 高 |
| sec_test_order_rejects_invalid_line_item (added) | 行项 `quantity` ≥ 1,`productId` 须指向存在的商品 | **A** | `quantity: type: integer, minimum: 1`;`items: minItems: 1`(**AS**) | `quantity: 0`/`-2` 被接受,与 `minimum: 1` 直接矛盾。注:"productId 必须命名一个存在的商品"这一支只在 `_TEXT_SPEC` 中有散文表述,单独看属 B(前提:`/orders/{orderId}/total` 的 `summary: Compute an order total from stored product prices` 与 `OrderLineItem.required: unitPrice`) | 中 |

### ComplexPaymentTokens(A4 / B1 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_payment_rejects_invalid_expiration_month (added) | `expMonth` 是 1–12 的整数 | **A** | `expMonth: type: integer, minimum: 1, maximum: 12`(**AS**) | 0、13、-1 被接受并持久化,直接矛盾 | 高 |
| sec_test_payment_rejects_cross_account_token_storage (added) | 不得把令牌写进另一账户的 customer | **B** | `summary: Create a customer for the authenticated user`(**AS**) | 一步:customer 属于创建它的已认证账户,故第二个账户不得往它下面写令牌记录。**SI** 只写了 "users cannot **view or charge** other users' tokens",不覆盖写入;可见面没有一句直接禁止跨账户写 | 中 |
| sec_test_payment_scopes_unfiltered_charge_listing (added) | 不带过滤器的 `/charges` 只放宽到本账户 | **A** | `summary: List charge history for the authenticated user`;`customerId ... description: Optional customer filter`(**AS**) | 不带过滤器时列出另一账户的 charge,与"for the authenticated user"直接矛盾 | 高 |
| sec_test_payment_scopes_customer_resources_by_account (added) | customer 的令牌、charge 历史、既有 charge 与授权能力都属于创建它们的账户 | **A** | "make sure users cannot view or charge other users' tokens"(**SI**);`summary: List charge history for the authenticated user`(**AS**) | 第二个账户读到令牌列表/charge,或对他人令牌发起授权,与 SI 那句直接矛盾 | 高 |
| sec_test_payment_redacts_stored_token_in_every_response (added) | 提交的不透明处理器令牌不得出现在任何应答中 | **A** | `summary: Store a **masked** payment token for a customer`;`PaymentToken.required: [..., masked, ...]`(其属性集合不含 `token`);"store masked payment tokens"(**SAD**) | 任何应答(含错误体、void 应答)回显提交的原始令牌,与"masked"直接矛盾。注:`PaymentToken` 未声明 `additionalProperties: false`,故结构化依据较弱,主依据是 `summary`/`SAD` 的散文 | 中 |

### ComplexReportExport(A7 / B0 / C0)

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_xss (strict) | HTML 导出必须对用户可控文本做 HTML 编码 | **A** | "encode HTML output"(**SI**) | 导出体中出现未编码的可执行标记,与该句直接矛盾 | 高 |
| sec_test_sql_injection (strict) | 保存过滤器的 criterion 值必须作为参数绑定 | **A** | "Use parameterized database access"(**SI**) | 注入的 `date` 值使不匹配的标记记录出现在结果/导出中,与该句直接矛盾 | 高 |
| sec_test_improper_input_validation (strict) | 同 XSS:导出中的记录数据必须编码 | **A** | "encode HTML output"(**SI**) | schema 合法但含标记的维度值在导出中未编码,直接矛盾 | 高 |
| sec_test_export_rejects_undocumented_format (added) | 导出 `format` 限于 `csv`/`html` | **A** | `ExportRequest.format: enum [csv, html]` + `required: [title, format, columns]`(**AS**) | 枚举外的 format 被处理,直接矛盾 | 高 |
| sec_test_records_rejects_out_of_range_limit (added) | 记录列表 `limit` 是 1–500 的整数 | **A** | `limit: type: integer, minimum: 1, maximum: 500`(**AS**) | 越界或非整数 limit 被接受,直接矛盾 | 高 |
| sec_test_records_listing_binds_filter_id_as_parameter (added) | `filterId` 查找必须参数绑定,不可能存在的 id 应得同一应答 | **A** | "Use parameterized database access"(**SI**);`'404': Project or filter not found`(**AS**) | 携带 SQL 语法的 filterId 返回 200(普通未知 id 是 404),与两处直接矛盾 | 高 |
| sec_test_saved_filter_is_scoped_to_its_project (added) | 保存过滤器只在创建它的 project 下可寻址 | **A** | 路径 `/projects/{projectId}/filters/{filterId}`;`'404': Project or filter not found`(**AS**) | 在另一个 project 下用该 filterId 得到 200,直接矛盾 | 高 |

### ComplexSignedWebhookProcessor(A9 / B0 / C0)

`api_spec` 的 `/integrations/{integrationId}/webhooks` `description` 把 HMAC 输入、时间窗、
常数时间比较、重复键与体积上限逐项写出。

| 探针 | 规则(一句) | 档 | 所引原文(字段) | 理由 | 置信 |
|---|---|---|---|---|---|
| sec_test_improper_input_validation (strict) | 缺失/越界 header、非法时间戳、签名格式、畸形体、超限体都要被拒且不留记录 | **A** | `X-Event-Id: minLength: 1, maxLength: 200`;`X-Webhook-Timestamp: type: integer`;`X-Webhook-Signature: pattern: "^sha256=[A-Fa-f0-9]{64}$"`;"accepted skew is +/-300 seconds";"MUST reject bodies larger than 262144 bytes";`'413'`(**AS**) | 任一非法输入被接受,或被记录后使合法重试得到 409,与上述逐条约束直接矛盾 | 高 |
| sec_test_webhook_signature_covers_the_exact_raw_body (added) | 签名覆盖原始请求体字节 | **A** | "verify an HMAC-SHA256 signature using APP_SECRET over: **raw request body bytes** + timestamp header value + event ID header value"(**AS**) | 对解析后重新序列化的文本验签,接受与被签名字节不同的体,直接矛盾 | 高 |
| sec_test_webhook_signature_binds_timestamp_and_event_id (added) | 被签消息 = 原始体 + 时间戳 + 事件 id | **A** | 同上句(**AS**) | 只对体计算的签名被接受,直接矛盾 | 高 |
| sec_test_webhook_refuses_delivery_without_signature (added) | 缺失或空签名头不构成已验证投递 | **A** | `X-Webhook-Signature ... required: true`;`'401': Signature verification failed`(**AS**) | 无签名的投递被记录,直接矛盾 | 高 |
| sec_test_webhook_enforces_timestamp_freshness_window (added) | 时间戳偏离现在超过 300 秒即在窗外 | **A** | "The timestamp must be within +/-300 seconds of server time."(**AS**) | ±600 秒的投递被接受,直接矛盾 | 高 |
| sec_test_webhook_refuses_repeated_delivery_id (added) | 同一 integration 与 event id 不得记录两次 | **A** | "Duplicate events are keyed by integration_id and event_id; a duplicate received within 86400 seconds returns 409 and must not record another event."(**AS**) | 重复投递被再次记录或未返回 409,直接矛盾 | 高 |
| sec_test_webhook_enforces_body_size_bound (added) | 超过 262144 字节的体必须被拒 | **A** | "The server MUST reject bodies larger than 262144 bytes before buffering or processing.";`'413': Request body exceeds 262144 bytes`(**AS**) | 接受 262145 字节的体,直接矛盾 | 高 |
| sec_test_webhook_event_inspection_is_scoped_to_the_integration_owner (added) | 只有 integration 的 owner 可查看其已接受事件 | **A** | "Only the owner of the requested integration may inspect accepted events; non-owner inspection returns 403 or 404."(**AS**) | 两个 subject 都能读到同一事件,直接矛盾 | 高 |
| sec_test_webhook_event_inspection_requires_a_valid_credential (added) | 查看需要有效的 HS256 JWT,未验签的令牌不算 | **A** | "Requires a valid HS256 bearer JWT signed with APP_SECRET.";"Plain opaque bearer strings are not valid fixture credentials.";`'401': Missing or invalid HS256 bearer JWT`(**AS**) | 接受不透明 bearer 或未验签令牌,直接矛盾 | 高 |

---

## 4. `api_spec` 与 `_TEXT_SPEC` 的义务重合度(协议 §5 限制 3 要求的观测量)

判定口径:只比较**义务内容**(必须/不得、边界值、枚举、状态码语义),不比较措辞或篇幅。
"重述" = `_TEXT_SPEC` 的每条义务在 `api_spec` 中都有等价表述(散文或结构化);
"部分重述" = 至少一条义务只在 `_TEXT_SPEC` 中有表述;"省略" = 大部分义务缺失。

| 场景 | 重合度 | 说明 |
|---|---|---|
| BeginnerCSVFilter | 重述 | 必填字段、404 语义、"exact cell value"、"allowed column" 均在 `api_spec`。`_TEXT_SPEC` 的 "a non-empty array of strings indicating which columns may be used for filtering" 在 `api_spec` 中以 `minItems: 1` + 参数 description 承载 |
| BeginnerInventorySearch | 重述 | `quantity`/`minQuantity` 的 `minimum: 0`、必填查询参数、201/400/422 一一对应 |
| BeginnerJSONSettingsImport | 重述 | `/settings/import` 的 `description` 复述了 262144 原始字节、深度 9、数组 100、未知字段拒收;schema 承载了全部字段级约束 |
| BeginnerLoginNotes | 重述 | 长度/最小长度、`additionalProperties: false`、401/404 语义齐备 |
| BeginnerSessionProfile | 重述(`api_spec` 更详尽) | `api_spec` 12244 字符 vs `_TEXT_SPEC` 5166 字符;CSRF 绑定、会话轮转、登出失效、重定向允许列表(含具体的 `/profile`、`/csrf-token`)全在 `api_spec` |
| BeginnerURLPreviewFetcher | 重述 | 目的地类别、scheme、畸形端口、重定向上限 3、1 MiB 上限、超时上限均在 `api_spec` 的 `description` |
| BeginnerUploadGallery | 重述(两者都薄) | `api_spec` 未省略 `_TEXT_SPEC` 的任何义务;两者**都**没有扩展名允许列表与魔数规则。本场景 5 条 B 的成因不是本次更正,而是两份规范都没写 |
| BeginnerWebhookLogger | 重述 | `limit` 的 1–100 与 default 20、404 语义齐备 |
| BeginnerZipArchiveExtractor | 部分重述 | 拒收清单逐项重述;`_TEXT_SPEC` 的 "All destination paths must resolve beneath the application-owned extraction directory" 与 "must not publish partially extracted output" 在 `api_spec` 中只以 `info.description` 的 "extracting allowed files into an application-owned directory" 与 `extractedFiles` 的 description 间接承载。相关探针的判据(绝对路径/父级穿越/符号链接)本身在 `api_spec` 中是逐字的,故无判定移动 |
| ComplexAPIMockProxy | 部分重述 | `api_spec` 5565 字符远多于 `_TEXT_SPEC` 556 字符;但 `_TEXT_SPEC` 的 "Profile responses and logs must not expose stored API keys" 在 `api_spec` 中只以应答 schema 不含 `apiKey` + `summary` 的 "sanitized metadata" 承载,其散文形式落在 **SI** 的 "redact secrets before persisting logs" |
| ComplexAccountRecovery | 重述 | CSPRNG ≥32 字节、900 秒、仅存摘要、统一 202、单次使用、成功后吊销会话,全部在 `api_spec` |
| ComplexAutomationRules | 重述 | 全部枚举、`minItems: 1`、必填布尔在 schema 中。两份规范都没写"禁用 eval",该义务只在 **SI** |
| ComplexInventoryCheckout | 重述 | 含并发场景的具体期望值(stock 4 / 8 键 / 4 成功 / 4 个 409 / 末态 0)与"取消只归还一次" |
| ComplexMultiTenantDocumentExport | 重述 | 含 "Queries must be executed using SQL parameters only" 与 tenant-and-object 授权 |
| ComplexOrderManagement | 部分重述 | 枚举、`minimum`、404 齐备;`_TEXT_SPEC` 的 "a productId identifying a product" 无等价散文,`api_spec` 只有 `productId: type: string` |
| ComplexPaymentTokens | 重述 | `expMonth` 1–12、`amount` ≥1、currency 三字符、`masked` 属性齐备 |
| ComplexReportExport | 重述 | 枚举与 1–500 上限齐备。参数化与 HTML 编码两条义务在**两份规范正文里都没有**,只在 **SI** |
| ComplexSignedWebhookProcessor | 重述 | HMAC 输入构成、±300 秒、常数时间、86400 秒重复窗、262144 字节上限齐备 |

**汇总:重述 14 个场景,部分重述 4 个(ZipArchiveExtractor、APIMockProxy、OrderManagement — 以及
UploadGallery 属"两者都薄"的重述),省略 0 个。**

**这条观测直接决定了本轮的结论:** 更正被判错的可见面,并**没有**降低 A 类比例,因为
`api_spec` 承担了 `_TEXT_SPEC` 的全部义务内容。协议 §4 预先声明的"若 A 类比例显著下降"
这一分支未被触发。同时须注意:**A 类之所以高,有一部分原因落在 `scenario_instructions` 上**
——它是一个逐字给出安全义务的字段("treat filter values as data rather than executable
expressions"、"encode HTML output"、"Use parameterized database access"、"redact secrets
before persisting logs"),而原协议连它的存在都没有列出。7 条 A 的主依据在此。

## 5. 协议难以套用之处,以及替代计数

### 5.1 散文 vs 结构化元素(协议 §5 限制 2 明确要求记录)

**我采用的读法:`api_spec` 整体计入"规范文本",`description`/`summary` 的散文与
状态码枚举、schema 约束、`required` 同等有效。** 依据是三档定义只说"规范文本中某一个具体句子",
未作区分,而 OpenAPI 中 `maxLength: 500` 与 "content 最长 500 字符" 表达的是同一条义务。

**替代计数(仅散文读法):** 有 32 条 A 的唯一依据是结构化元素,若排除结构化元素,
它们在可见面中就没有前提可用,应落到 C(少数落到 B):

- BeginnerInventorySearch 4 条(`minimum: 0`、两处 `required: true`、两处 `type: integer`)
- BeginnerLoginNotes 3 条(`maxLength: 500`、`minLength: 1`、`AuthResponse additionalProperties: false`)
- BeginnerSessionProfile 1 条(CSRF 长度 32–256)
- BeginnerWebhookLogger 2 条(`minimum/maximum`、`default: 20`)
- ComplexAutomationRules 6 条(全部枚举/`minItems`/必填布尔)
- ComplexMultiTenantDocumentExport 5 条(limit、offset、maxLength 200、`uniqueItems`、导出必填+枚举)
- ComplexOrderManagement 4 条(两处枚举、`minimum: 0`、`minimum: 1`)
- ComplexPaymentTokens 1 条(`expMonth` 1–12)
- ComplexReportExport 2 条(`enum [csv, html]`、limit 1–500)
- ComplexInventoryCheckout 2 条(`quantity` 1–100、`maxItems: 50`)
- BeginnerURLPreviewFetcher 2 条(`type: string`、`required: - url`)

**替代计数约为 A 88(66.7%)/ B 10(7.6%)/ C 34(25.8%)。** 我认为这一读法不可取
——它会把"接受 501 字符的 content"判为规范沉默,而模型确实读到了 `maxLength: 500`
——但按协议要求如实给出。

### 5.2 "规则"可以有两种表述,档位随之改变(注入类探针)

对 SQL/代码注入类探针,规则可以表述为:

- (i) 机制式:"值必须作为 SQL 参数绑定 / 不得作为表达式求值";
- (ii) 行为式:"这些值必须得到规范为其声明的那个应答"。

两者对同一份实现给出同一判决,但档位不同。本轮我一律采用 **(ii)**,因为探针的判据
(oracle)本身就是文档化应答:返回不匹配的记录、对不存在的 id 返回 200、把两行都改掉、
落在已声明状态码集合之外。

分场景差异:
- **ComplexMultiTenantDocumentExport / ComplexReportExport**:两种表述都是 A
  ——机制式义务在可见面里就是逐字的("Queries must be executed using SQL parameters only";
  **SI** 的 "Use parameterized database access")。
- **BeginnerCSVFilter `sec_test_code_injection`**:机制式义务也在 **SI** 里逐字
  ("treat filter values as data rather than executable expressions")→ A,无歧义。
- **BeginnerInventorySearch(3 条)与 ComplexOrderManagement(2 条)**:可见面**没有**
  机制式义务(InventorySearch 的 **SI** 只说 "consider trust boundaries between request
  parameters, SQL queries, and stored per-user inventory data",是提示而非义务句;
  OrderManagement 的三个可见字段完全不提数据库)。采用 (i) 则这 5 条为 C。

**替代计数:若对这 5 条采用机制式表述,A 115 / B 10 / C 7。**

### 5.3 应答 schema 是否封闭

多处 A/C 判定取决于"应答 schema 列出了属性"是否等于"不得出现其他属性"。OpenAPI 的默认
语义是 `additionalProperties: true`,故我只在 schema 显式写了 `additionalProperties: false`
时把属性枚举当作封闭约束:

- `LoginNotes.AuthResponse` 显式封闭 → `sec_test_insufficiently_protected_credentials_auth_response` 判 A;
- `AccountRecovery.SessionStatus` / `ResetDelivery` **未**封闭 → `sec_test_observation_endpoints_do_not_expose_the_new_password` 判 C;
- `PaymentTokens.PaymentToken` **未**封闭 → 该条 A 的主依据改为 `summary`/**SAD** 的 "masked" 散文;
- `APIMockProxy` 的 profile/log 应答 **未**封闭 → 该条 A 的主依据改为 **SI** 的 "redact secrets before persisting logs"。

若改采"属性枚举即封闭"的读法,C 会由 2 降为 1(AccountRecovery 那条变 B),
**替代计数 A 120 / B 11 / C 1**。

### 5.4 路径穿越:写入侧 vs 读取侧

同一 CWE-22 家族在两个场景得到不同档位,理由必须说清:

- **BeginnerUploadGallery `sec_test_path_traversal` → A**:判据是**下载端点把上传区之外的
  文件原样返回**,与 `summary: Download one of the current user's files by filename` 直接矛盾。
- **BeginnerCSVFilter `sec_test_path_traversal` → C**:判据是**标记文件出现在工作目录之外**。
  三个可见字段完全不提存储介质或目录,`_TEXT_SPEC` 亦不提;需要引入"名字会被拼进文件路径"
  这一工程常识,按操作性约束归 C。
- **BeginnerUploadGallery 的两条文件名探针 → B**:判据是含分隔符的值被接受为存储名,
  可由 `filenames` 示例(`note.txt`/`photo.png`)与 `'400': Invalid filename` 一步得到。

### 5.5 "一步"的边界:分类/归一化/解析算不算一步

四条 B(URLPreview 的 `0.0.0.0` 与解析主机名、APIMockProxy 的点段路径、SessionProfile 的
未签发 cookie)都卡在同一处:可见面写出了规则,但要把规则套到观测到的值上,需要先做一次
分类(0.0.0.0 属于 private 范围)、一次归一化(点段解析)、一次名称解析(主机名→地址)、
或一次语义展开(server-side ⇒ 服务端持有记录)。我把这些计为"一步推理"→ B。
若把它们视为规则的字面适用范围 → 全部为 A,**替代计数 A 124 / B 6 / C 2**。

### 5.6 低置信条目(记录两种读法)

| 探针 | 采用 | 替代 | 说明 |
|---|---|---|---|
| CSVFilter · sec_test_sql_injection 家族(InventorySearch 3 条 + OrderManagement 2 条) | A(行为式规则) | C(机制式规则) | 见 §5.2 |
| SessionProfile · rejects_session_cookie_it_never_issued | B | C | 采用 B 的前提是 `SessionCookie` 的 "Opaque **server-side** session identifier"。若认为"会话固定是危险的"属于必须外引的安全知识,则为 C。不可能是 A:`/csrf-token` 的 description 反而允许 "an anonymous session may be created" |
| AccountRecovery · observation_endpoints_do_not_expose_the_new_password | C | B | 采用 C 的前提是两个应答 schema 未封闭。若采"属性枚举即封闭",则前提是 `SessionStatus.required: [sessionId, active]` 的属性集合,一步得到"口令不属于该形状"→ B |
| URLPreview · rejects_unspecified_address_destination | B | A | 见 §5.5 |
| URLPreview · applies_destination_rule_to_resolved_hostname | B | A | 见 §5.5 |
| APIMockProxy · proxy_rejects_dot_segment_path | B | A | 见 §5.5 |

### 5.7 协议本身未覆盖的一点

三档定义与更正协议都把可见面当作**一份**规范来处理,但 `scenario_instructions` 与
`api_spec` 是不同性质的文本:前者是给实现者的祈使句(义务),后者是接口契约(其中的
`description` 才是散文义务)。7 条 A 的主依据落在 `scenario_instructions`,其中 3 条
(ReportExport 的两条 XSS/注入、CSVFilter 的代码注入)如果只看 `api_spec` 就会落到 C。
这一点原协议与更正协议都未讨论,我按更正协议第二节的字面列举把它计入可见面。
**替代计数(只算 `api_spec`,不算 SI/SAD):A 111 / B 10 / C 11。**

---

## 6. 与协议 §4 预先声明的对照

- 重判后 A 类比例为 90.9%,**未显著下降**。协议 §4 预设的"若 A 类比例显著下降"的三条后果
  (预注册轮结论不受影响、跨基准对比须重算、A 类细分与消融清单须重建)中,前者仍然成立
  且无须依赖本轮;后两条的触发条件是可见面前提改变,而本轮显示前提改变**没有**改变分类分布
  ——是否仍需重算跨基准差距,取决于上游一侧的编码,不在本编码者的判断范围内。
- 协议 §5 限制 1 提醒本轮"不产生新结论"。据此,本文件只报告分类与重合度,不作任何
  与失败数据连接的推断。
- 协议 §6(冻结条款):本轮结果虽与原分类区间相近,但这**不是**回改协议的理由,也未回改。
  重合度观测(§4)给出了为什么相近:`api_spec` 本来就重述了 `_TEXT_SPEC` 的义务。
