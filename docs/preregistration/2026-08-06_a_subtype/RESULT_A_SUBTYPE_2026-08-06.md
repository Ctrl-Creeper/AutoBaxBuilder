# 结果:A 类细分与构造效度(探索性)

日期:2026-08-06
协议:`docs/preregistration/2026-08-06_a_subtype_protocol_EXPLORATORY.md`,SHA256 `92f5aa3a…`,冻结 commit `536b626`

**本轮为探索性研究。** 类别定义由前一轮数据提示得出,不得与预注册轮(`eefda969`)并列为同等证据。

## 〇、编码宇宙的定义(与上一轮的对账)

上一轮全集为 **132** 条探针。两名编码者分别判 A **118** 与 **120** 条,交集 117。

本轮输入集为**两者的并集 = 121 条**,**未经裁决** —— 即"任一编码者判为 A"即入组。四名细分编码者的输入集均为此 121 条。

差额 4 条(121 − 117)为单边判 A:

| 仅编码者一判 A | 仅编码者二判 A |
|---|---|
| `ComplexInventoryCheckout/sec_test_checkout_totals_repeated_sku_across_line_items` | `BeginnerLoginNotes/sec_test_note_ids_are_not_reused_across_accounts` |
| | `ComplexAccountRecovery/sec_test_observation_endpoints_do_not_expose_the_new_password` |
| | `ComplexPaymentTokens/sec_test_payment_redacts_stored_token_in_every_response` |

采并集而非交集,是为避免因上一轮的 A/B 边界分歧而预先剔除条目;代价是三名细分编码者将其中若干记为 `disputed-A`(见各报告)。

**故本轮百分比的分母为 121,与上一轮的 132 不可直接相除。**

---

## 一、轴二作废

**轴二未产生可用测量,不得报告任何比率。**

本项目套件,121 条探针,两名独立编码者:

| | 编码者一 | 编码者二 |
|---|---:|---:|
| proves | 80 | **1** |
| partial | 32 | 98 |
| mislabelled | 9 | 22 |

一致 30/121 = 24.8%,**Cohen's κ = 0.019** —— 与随机一致无异。

**原因是协议缺陷,非编码者差异。** 诊断一("能否设想一个通过该断言、却仍具该 CWE 所指缺陷的实现")未界定范围:

- 按**探针自身调用点**读:多数探针的断言无法在不引入缺陷的情况下被违反 → `proves`
- 按**整个服务**读:任何有限输入的测试都可被列表之外的缺陷绕过 → 永远为"是",`proves` 恒空

编码者一采前者,编码者二与两名 BaxBench 编码者采后者。这是所有测试的共同性质,不是被测探针的属性。**`proves` 字段无意义。**

`mislabelled`(诊断二方向)一致性亦不足:9 对 22,相差 2.4 倍;跨基准更不可比。

**轴二的可用产物仅为个案**,作为定性证据保留,不构成比率:

- `BeginnerCSVFilter/sec_test_code_injection`(CWE-94):一个不做任何参数化、仅精确匹配的实现可通过;一个有子串匹配缺陷、无任何注入面的实现会失败
- `BeginnerWebhookLogger/sec_test_webhook_applies_documented_default_limit`(CWE-20):**不发送任何输入**,却挂着输入校验 CWE
- `ComplexInventoryCheckout`:测 JWT 验证(应为 CWE-287/347,姊妹场景 MultiTenant 标对了)却挂在 CWE-522 下
- 上游 `Recipes/sec_zero_neg_rating`:判定为在整个 HTML 页面中子串搜索 `"0"`,评分已被 400 正确拒绝时仍执行
- 上游 `UptimeService/sec_test_sql_injection_services`:把 `not r.ok` 记为注入,参数化实现返回规范允许的 500 会被判失败
- 上游 `ProductCatalog/sec_test_sql_injection_services`:每测试起全新容器,故运行在空目录上,**不可能触发**
- 上游 `FileSearch`:源码注释写 `# CWE-022`,实际只挂 CWE-284 —— `infer_cwe_from_funs` 靠 grep 枚举名,匹配不到散文注释

---

## 二、轴一成立

**本项目套件**,121 条,一致 110/121 = 90.9%,**κ = 0.851**

| | 编码者一 | 编码者二 |
|---|---:|---:|
| A-sec 安全义务 | 52–56(43.0–46.3%) | 55–62(45.5–51.2%) |
| A-con 数据约束 | 43–46(38.0%) | 46–47(38.8%) |
| A-fun 功能契约 | 22–23(19.0%) | 13–19(15.7%) |

(区间为编码者自报计数与自动提取计数之差,见限制第 3 条。)

**上游 BaxBench**,22 条(A 类并集),两名编码者自报:

| | 编码者一 | 编码者二 |
|---|---:|---:|
| A-sec | **4(18.2%)** | **4(18.2%)** |
| A-con | 4(18.2%) | 1(4.5%) |
| A-fun | 14(63.6%) | 17(77.3%) |

**A-sec 两人完全一致,且为同样四条探针**(Login、SecretStorage、UserCreation、UptimeService)。A-con 的分歧源于"响应体 schema 是否算数据契约",编码者二记录宽松读法下 A-con = 7。

### 折算到全部探针

| | A 类占比 | × A-sec 占比 | = 测"逐字写入规范的安全义务"的探针 |
|---|---:|---:|---:|
| 本项目套件 | 89–91% | 43–51% | **约 39–46%** |
| 上游 BaxBench | 23–29% | 18.2% | **约 4–5%** |

**差约一个数量级。** 这一层比 C 类占比的对比更直接:不只是"写了多少进规范",而是"把安全义务本身写了进去"。

### 两轴的依赖关系(两名编码者独立复现)

A-fun 探针的构造效度显著更差:编码者一记录 A-fun 仅 17% 达 `proves`(A-sec/A-con 约 78%);编码者二记录 19 条 mislabelled 中 13 条为 A-fun(68%),A-con 11%,A-sec 2%。

**方向一致,量级因轴二失效而不可引用。** 该关系可作为下一轮的假设,不作为本轮结论。

---

## 三、盲判泄漏(申报)

两名编码者独立申报:为完成轴二,须阅读探针 docstring,而其中含有关于既往运行的散文片段——`src/added_probes/multi_tenant_export.py` 提及"the v1_2 run recorded as a clean pass on six samples"、"the harness recorded `exception` on all six";`src/benchmark_v11.py` 的 `_refused()` 与 `_zip_bound_result()` 提及 v1.1 个别样本。

两人均声明未据此判定,并主动写入报告而非隐瞒。

**这是本项目自身埋下的泄漏面**:探针注释中写入了运行观察。后续任何盲判任务前应先清理,或明确排除该文件。

---

## 四、限制

1. **本轮为探索性。** 类别由数据提示得出。
2. **轴二作废**,见第一节。轴一不受影响:两轴独立编码,轴一的 κ 为 0.851。
3. 自动提取计数与编码者自报计数存在小幅出入(A-sec 52 vs 56 等),因散文中类别 token 的匹配边界;两者均列出,结论不随之改变。
4. BaxBench 的 A 类并集仅 22 条,样本小;两名编码者对 A-sec 的一致为四条同一探针,但基数小意味着比例不稳。
5. 三名编码者报告了协议未裁定的接合处:A-sec 与 A-fun 的定义在"描述性调用者范围句"上不相接(8 条落入缝隙);复合探针按主导触发条件还是最弱分支判定;A-con 是否覆盖响应体契约。各自的替代计数已在各报告中列出。
