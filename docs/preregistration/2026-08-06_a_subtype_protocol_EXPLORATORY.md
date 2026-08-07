# A 类细分与构造效度编码规则(探索性)

冻结时间:2026-08-06
状态:**编码开始前冻结。分类完成并归档前不得修改。**

## 本轮不是预注册研究

前一轮(协议 SHA256 `eefda969…`,冻结 commit `f47ecc1`)是预注册的:类别定义与证伪条件在看到任何数据之前写死。

**本轮不是。** 三档细分的定义是在读过 CWEval 编码结果之后提出的——先看到分布,再定义类别。因此:

- 本轮结果**不得**与 `eefda969` 那轮并列陈述为同等证据
- 归档、汇报与论文写作中一律标注为 **exploratory**
- 它的作用是刻画已观测到的差异,不是检验任何假设

补偿措施(不能把探索性变成确证性,但能排除已知偏差):标准先冻结再编码;双人独立编码并报一致性;编码者盲于全部评测结果;使用全新上下文的编码者。

---

## 轴一:A 类细分

仅对前一轮判为 A(规范逐字)的探针适用。判定「探针所依据的那句规范文本,本身是什么性质」。

### A-sec — 安全义务

该句用安全语言直接陈述了一项安全义务。违反它就是违反一条被明写的安全要求。

*本项目实例*
- `BeginnerSessionProfile`:"On logout, the server-side session must be invalidated so the old cookie cannot be reused"
- `BeginnerURLPreviewFetcher`:"must reject … loopback destinations, private network destinations … before making the initial connection"(SSRF 防御被逐字写入规范)
- `ComplexMultiTenantDocumentExport`:"Each request must enforce both the caller's tenant boundary and document-level read authorization"

### A-con — 声明式数据约束

该句陈述的是一项数据契约(类型、范围、长度、枚举、默认值),探针把它实例化到一个具体请求上。防御性质是隐含的:约束成立即防御成立。

*本项目实例*
- `BeginnerInventorySearch`:"quantity, an integer greater than or equal to 0" → 探针提交 −1
- `BeginnerWebhookLogger`:"limit is an integer from 1 to 100, defaults to 20"
- `BeginnerLoginNotes`:"between 1 and 500 characters"

### A-fun — 普通功能契约

该句陈述的是与安全无关的功能行为,安全输入恰好使实现违反它。规范中不存在任何可读作安全要求的成分。

*本项目实例*
- `BeginnerCSVFilter/sec_test_code_injection`:依据 "exact value to match"
- `BeginnerInventorySearch/sec_test_sql_injection`:依据 "returns a JSON array of matching items"

*CWEval 同构实例*:SQL 注入检查依据 docstring 的 "otherwise, return None"

### 判定顺序

依次判断:该句是否用安全语言陈述义务(A-sec)→ 是否为数据契约(A-con)→ 否则 A-fun。
一句同时具备多重性质时,取最强者(A-sec > A-con > A-fun),并在理由中说明。

---

## 轴二:构造效度 —— 断言是否证明了所挂的 CWE

对同一批探针,独立于轴一,回答:**该探针的断言,是否构成其所标注 CWE 的证据?**

两个诊断问题,分别作答:

1. **能否设想一个通过该断言、却仍具有该 CWE 所指缺陷的实现?**(假阴性方向)
2. **能否设想一个未通过该断言、却完全不具备该 CWE 所指缺陷面的实现?**(假阳性方向)

判定:
- **proves** — 两问皆否
- **partial** — 其中一问为是
- **mislabelled** — 两问皆是

*实例*(`BeginnerCSVFilter/sec_test_code_injection`,标注注入类 CWE):一个不做任何参数化、仅做精确字符串匹配的实现可以通过;一个存在子串匹配缺陷、但完全没有注入面的实现会失败。两问皆是 → **mislabelled**。该探针测量的是精确匹配这一功能契约,不是注入。

每条判定须给出所设想的实现,一句话即可。

---

## 编码程序

1. **盲判**。不得查阅任何评测结果:不得知道哪些探针曾报出失败,不得知道各提示条件得分。可查阅:探针实现源码、规范文本、种子契约。
2. **双人独立编码**,分歧落表,报一致性(轴一 Cohen's κ;轴二同)。
3. 每条判定附:所引规范原文;轴一的性质判断理由;轴二两个诊断问题的答案与所设想的实现。
4. 分类表与本文件一同打时间戳归档。

## 范围

本轮编码对象:本项目套件与上游 BaxBench 中前一轮判为 A 的全部探针。

CWEval 已有一份细分(编码者二),但计数单位为"规则"与"文件",与本轮不一致,**不并入主表**,仅作旁证并注明单位差异。

轴二本轮仅施于 A 类探针。B、C 类的构造效度未编码,系已知缺口。

## 头条对比的界定

最干净的对照是:**同一套 harness、同一任务粒度,人工编写的上游 BaxBench 对照本项目的流水线生成套件**,变量近似只有"人写 vs 生成"。

CWEval 为函数级,其"规范"仅为一段 docstring,C 类占比有一部分源于粒度差异。**它作为佐证,不作为第二个等价对照。**
