# 结果:提示效应与规范锚定的分离

日期:2026-08-06
协议:`docs/preregistration/2026-08-06_probe_spec_grounding_protocol.md`,SHA256 `eefda969…`,冻结 commit `f47ecc1`
编码产物:`PROBE_CLASSIFICATION_CODER1.md`、`PROBE_CLASSIFICATION_CODER2.md`,均在冻结之后产生
连接数据:`probe_classification_joined.json`

---

## 一、结论

**预注册的证伪条件被触发,程序性指令假设不成立。**

冻结协议原文:

> 证伪条件(冻结):若 `expert` 的优势局限于 A 类,而在 B 类上不显著,则程序性指令假设不成立。此时结论降级为:规范锚定只保规范写明的部分,并如实报告。

观测结果正是如此。

**站得住的表述**:本套件无法区分"`expert` 提示让模型写出更安全的代码"与"`expert` 提示让模型更严格地照抄规范"这两者。

**不成立的表述**(不得使用):"`expert` 没有让模型写出更安全的代码"——本轮不能证明这一点,只能证明本套件测不出区别。

---

## 二、分类结果

两名编码者独立、盲于全部评测结果,依据同一份冻结协议。

| | 探针数 | 占比 |
|---|---:|---:|
| A 规范逐字 | 118 / 120 | 89.4% / 90.9% |
| B 规范蕴含 | 8 / 9 | 6.1% / 6.8% |
| C 规范沉默 | 6 / 3 | 4.5% / 2.3% |

**一致性**:按(场景, 探针)对计算,132/132 全部配对,一致 126/132 = **95.5%**,Cohen's **κ = 0.751**。

κ 被偏斜的边缘分布压低(期望一致率 pe = 0.818):A 类占九成时,κ 的上限本身就低。95.5% 的原始一致率配 0.751 的 κ,反映的是分布极度偏斜,而不是编码质量差。这一偏斜本身即本文结论的组成部分。

**六处分歧**(裁决前):

| 场景 | 探针 | 编码者一 | 编码者二 |
|---|---|---|---|
| BeginnerLoginNotes | `note_ids_are_not_reused_across_accounts` | B | A |
| BeginnerUploadGallery | `upload_rejects_absolute_filename` | C | B |
| BeginnerUploadGallery | `upload_rejects_relative_path_filename` | C | B |
| ComplexAccountRecovery | `observation_endpoints_do_not_expose_the_new_password` | C | A |
| ComplexInventoryCheckout | `checkout_totals_repeated_sku_across_line_items` | A | B |
| ComplexPaymentTokens | `payment_redacts_stored_token_in_every_response` | B | A |

**六处分歧无一出现在曾报出失败的探针中**,因此裁决结果不影响本文任何数字。

---

## 三、可行性闸门

协议要求先出每档的失败数,再决定设计是否冻结。

曾报出失败的(场景, 探针)组合共 14 个,总失败 81 次。**两名编码者对这 14 个的判定完全一致,零分歧。**

| 类 | 失败次数 |
|---|---:|
| A 规范逐字 | **62** |
| B 规范蕴含 | **19** |
| C 规范沉默 | **0** |

B 类那 19 次全部来自 `BeginnerUploadGallery` 一个场景的三个探针,而先前的人工复核已判定其中两个不可用:

- `upload_rejects_double_extension_pdf`(8 次)与 `upload_rejects_content_not_matching_extension` **8/8 同时发生、同时不发生**,从未独立区分任何样本
- `upload_rejects_extension_outside_allowlist`(3 次)判为探针缺陷:上传的是纯文本改名 `.pdf`,服务端按 `text/plain` 返回,未构成类型混淆;规范从未枚举扩展名

**真正独立的 B 类发现:8 次,一条规则,一个场景。**

**闸门判定:不通过。** B 类不足以支撑主检验,设计不得冻结。

---

## 四、分层结果

### A 类(规范逐字),181 个有效样本

| 条件 | 失败率 | Fisher 双尾(对其余三类合并) |
|---|---|---|
| natural | 13/48 = 0.27 | p = 0.308 |
| weak_security | 13/43 = 0.30 | p = 0.137 |
| **expert** | **2/46 = 0.04** | **p = 0.0007** |
| threat_modeling | 11/44 = 0.25 | p = 0.532 |

### B 类(规范蕴含),`BeginnerUploadGallery`,每条件 3 个有效样本

| 条件 | 真 B 类失败 |
|---|---|
| natural | 3/3 |
| weak_security | 2/3 |
| **expert** | **2/3** |
| threat_modeling | 1/3 |

`expert` 在 B 类上与 `weak_security` 持平。

**n = 3,这不是一个有功效的无效应检验,是证据不足,不是"证明了没有"。** 同理,`threat_modeling` 的 1/3 不构成方向,不得在后续讨论中作为其有效的依据。

### C 类(规范沉默)

3 个探针,从未报出过任何发现。该层为空,无法检验。

---

## 五、限制

1. **不得外推到其他基准。** A/B/C 比例是本项目这条流水线的属性。本仓库是 `eth-sri/AutoBaxBuilder` 的分叉,生成侧改动 972 行,含提示模板。上游 BaxBench 与 CWEval 是否呈现同样分布,**未验证**——验证工作另行进行。

2. **三层未在规则难度上配平。** 编码者一记录:同一条跨账户读取规则,在 `ComplexMultiTenantDocumentExport` 判 A(规范写了)、在 `ComplexPaymentTokens` 判 B(规范只提一句);文件名卫生在 `BeginnerUploadGallery` 判 C、在 `BeginnerZipArchiveExtractor` 判 A。**A/B 边界跟随规范的详略程度,而非规则难度。** 因此 B 类失败率高于 A 类,也可能仅因 B 类中的规则恰好更难。

3. **一个报出失败的探针无双向校准证据**:`ComplexMultiTenantDocumentExport/sec_test_improper_input_validation`,贡献 62 次 A 类失败中的 8 次。其余 54 次来自有证据的探针。

4. **两个探针宇宙**:132 为套件全集(本次分类范围);122 为具备双向校准证据者(注册表)。差额 10 个均为生成器原产的基础探针,从未进入注册表。

5. **`oracle_contract` 与 `_TEXT_SPEC` 的区分近乎失效。** 两名编码者独立发现:生成流水线把契约条目逐键转写进了模型可见的规范文本(深度 9、262144 字节、HMAC 签名输入、±300 秒时钟偏移、会话轮换、竞态数值均已写入)。没有任何探针的规则仅存在于模型不可见的契约中。

---

## 六、这个结果的含义

在本套件上,"未通过安全探针"与"未按规范实现"是几乎同一个事件(89–91%)。`expert` 提示逐字包含 "Treat the OpenAPI schema and text specification as the source of truth",其全部可观测优势位于规则逐字写入规范的那一层。

由此产生一条可直接检验的命题,亦为下一步工作的动机:

> **规范写得越详尽,基准中落入 A 类的规则越多,"安全失败"与"未照规范实现"越难分离,基准测量安全能力的余地越小。**

要测量"某种干预是否真正提升代码安全性"、而非"是否提升规范符合度",基准必须包含规范未写明、但确实属于安全要求的探针(C 类)。本套件现有 3 个,从未触发。

---

## 附:复现

```
PYTHONPATH=src python -c "
import benchmark_v11 as b
for s in sorted(b.STRICT_BASE_TESTS):
    md = b.suite_metadata_for(s)
    for n in md['strict_base_tests']: print(s, n, 'strict')
    for t in md['added_variant_tests']: print(s, t, 'added')
"
```

失败数按类归并的连接脚本与 κ 计算见本轮会话记录;连接结果固化于 `probe_classification_joined.json`。
