# 结果:可见面更正后的重判

日期:2026-08-17
协议:`docs/preregistration/2026-08-17_recode_visible_surface_protocol.md`,SHA256 `8057b368…`,冻结 commit `3274327`
被更正对象:`2026-08-06_probe_spec_grounding_protocol.md`(`eefda969…`)

---

## 一、结论:前提错误未影响原结论

| | 原分类(错误可见面) | 重判(更正后) |
|---|---|---|
| A 规范逐字 | 118 / 120(89.4% / 90.9%) | **120 / 121(90.9% / 91.7%)** |
| B 规范蕴含 | 8 / 9 | 10 / 9 |
| C 规范沉默 | 6 / 3 | 2 / 2 |

**一致性**:132 条全覆盖,一致 130/132 = 98.5%,**Cohen's κ = 0.906**(原轮 0.751)。

两处分歧:
- `BeginnerURLPreviewFetcher/sec_test_url_preview_rejects_unspecified_address_destination`(B 对 C)
- `ComplexAccountRecovery/sec_test_observation_endpoints_do_not_expose_the_new_password`(C 对 A)

**新旧 A 集合均为 121 条,交集 119。** 仅四条易位:

| 旧 A → 新非 A | 新 A → 旧非 A |
|---|---|
| `BeginnerURLPreviewFetcher/sec_test_url_preview_applies_destination_rule_to_resolved_hostname` | `ComplexReportExport/sec_test_improper_input_validation` |
| `ComplexAPIMockProxy/sec_test_proxy_rejects_dot_segment_path` | `ComplexReportExport/sec_test_xss` |

---

## 二、为什么没影响

两名编码者独立测量 `api_spec` 与 `_TEXT_SPEC` 的义务重合度(协议第五节限制 3 要求):

| | 完整重述 | 部分重述 | 省略 |
|---|---:|---:|---:|
| 编码者一 | 14 / 18 | 4 | **0** |
| 编码者二 | 16 / 18 | 2 | **0** |

**没有任何场景把义务只写在 `_TEXT_SPEC` 里。** v1_2 场景的 `api_spec` 反而显著更厚(SessionProfile 12.2k 对 5.2k 字符;APIMockProxy 5.6k 对 0.6k)。

两条只存在于 `_TEXT_SPEC` 的义务(Zip 的解压路径必须落在目标目录内;APIMockProxy 的 profile 响应与日志不得暴露 API key)均在可见面有对应表述(schema description;`scenario_instructions`)。

---

## 三、原前提是两个方向都错

更正后的可见面**不比原来的小**。

`scenario_instructions` 在四个场景中承载核心义务句,而被更正协议**未将该字段列为可查材料**:

| 场景 | `scenario_instructions` 原文 |
|---|---|
| ComplexReportExport | Use parameterized database access, encode HTML output |
| ComplexPaymentTokens | make sure users cannot view or charge other users' tokens |
| ComplexAPIMockProxy | redact secrets before persisting logs |
| BeginnerCSVFilter | treat filter values as data rather than executable expressions |

编码者一记录 7 条 A 判定主要依赖该字段,其中 3 条若仅凭 `api_spec` 会落入 C。

**多算了 `_TEXT_SPEC`,漏算了 `scenario_instructions`,两者大致相抵。** 这是巧合,不是设计。

---

## 四、真正的敏感点:散文 vs 结构化元素

| 读法 | A | B | C |
|---|---:|---:|---:|
| 主读法(`api_spec` 整体) | 120 / 121 | 10 / 9 | 2 / 2 |
| **仅计 `api_spec` 中的散文** | **88 / 93** | 10 / 35 | 34 / 4 |
| 仅计 `api_spec`(去另两字段) | 111 | 10 | 11 |
| 注入类按机制而非行为陈述 | 115 | 10 | 7 |

**该边界的摆幅约 30 条,远大于可见面更正的 4 条。**

`api_spec` 为 OpenAPI YAML,混合散文(`description`、`summary`)与结构化元素(状态码枚举、schema 约束、`required`)。三档定义未区分二者。

**此模糊处已被四轮中六名独立编码者分别点出。** A 在两种读法下均为多数,但若论文需报精确比例,该边界须先行冻结并重判。这是下一个应当预注册的对象,优先于其余待办。

---

## 五、对既有结论的影响

| 结论 | 状态 |
|---|---|
| 预注册轮的证伪(`expert` 优势局限于 A 类) | **不变。** 协议第四节事先声明重判只能 A→C,不能反向;分层方向未动 |
| 跨基准对比(我们 2–5% C 对上游 50–54%) | **可恢复引用。** 上游两名编码者本就自行查明 `spec_type` 默认值并按 `api_spec` 分类,现两侧站在同一可见面上 |
| A 类细分(探索性,56 条 A-sec) | **不必重建。** 新旧 A 集合交集 119/121,四条易位不涉及 56 条 A-sec 的构成 |
| 消融手术清单 | **不必因本轮重建**,但另有四项独立缺陷待处理(见下) |

---

## 六、盲判泄漏(申报)

1. **我造成的**:更正协议第四节引用了原分类的 A/B/C 区间,而协议是编码者的指令集,无法回避。编码者一申报此事,其处置为先固定全部 132 条判定、再行比对。**后续任何要求盲判的协议不得在正文中写入既有结果。**
2. 两名编码者均申报执行 `ls artifacts/` 时看到了被禁文件的**文件名**(未读内容)。编码者二指出 `ABLATION_SCREENING_GROUP_{A,B,C}` 这一命名本身泄露了"存在某种分组筛选"。二者均主动写入报告。

---

## 七、仍待处理(与本轮无关,来自消融筛选)

1. 消融协议第五节的可见面定义遗漏 `short_app_description` 与 `scenario_instructions`,而后者含义务原文
2. 第五节的正例(摘除 MultiTenant 租户边界句)与其自身筛选规则 1 冲突——`func_test_acme_member_cannot_retrieve_unauthorized_documents` 断言该属性
3. `ComplexInventoryCheckout` 三条 A-sec 全部在第 2 步排除,该场景两臂逐字节相同,实际成为第八个对照场景
4. 手术清单 `both` 数组含两条编码者实际判为 A-con / A-fun 的条目,系 token 提取匹配到"被否决的备选读法"
