# 规范锚定重判:更正可见面(冻结)

冻结时间:2026-08-17
更正对象:`2026-08-06_probe_spec_grounding_protocol.md`(`eefda969…`)
状态:**编码开始前冻结。分类完成并归档前不得修改。**

---

## 一、为什么重判

被更正协议的"可查阅材料"一节写道:

> **The specification.** `_TEXT_SPEC` and `_API_SPEC` in `artifacts/<Scenario>/<Scenario>_iw0.py`. This is the text a model implementing the scenario was given.

**该陈述有误。** BaxBench 的 `build_prompt`(`baxbench/src/scenarios/base.py:205–234`)只插值 `api_spec` **或** `text_spec` 之一,由 `--spec_type` 选择,默认 `openapi`;本项目的 runner 从不传该参数。

实证:两轮全部样本的结果路径均为 `temp0.0-openapi-none`,即 `temp{温度}-{spec_type}-{safety_prompt}`。

**模型看到的是 `api_spec`,从未看到 `_TEXT_SPEC`。**

同一模板另外插值两个字段,原协议亦未列出:`short_app_description` 与 `scenario_instructions`。

后果:依据句仅存在于 `_TEXT_SPEC` 的探针,从模型视角属**规范沉默(C)**,而非 A。原分类的 A 类比例可能被高估。

---

## 二、本次唯一的改动

A / B / C 三档的定义、"一步推理"的操作性约束、编码程序(盲判、双人、引用原文、报 κ)**全部沿用被更正协议,一字不改**。

**只改可见面的定义:**

模型可见的规范 = 以下三者,别无其他:

1. `api_spec`(`spec_type` 默认 `openapi`,本项目从未覆盖)
2. `short_app_description`
3. `scenario_instructions`

**`_TEXT_SPEC` 不属于可见面。** 依据仅存在于 `_TEXT_SPEC` 者判 **C**。

`oracle_contract` 同样不可见,沿用原协议的排除。

---

## 三、编码程序

沿用被更正协议第三节,并补一条:

1. **盲于评测结果**:不得查阅 `artifacts/eval_runs_*`、任何含 `RESULT`/`REVIEW`/`CLASSIFIED`/`EVAL`/`calibration` 的文件。
2. **亦盲于原分类**:不得查阅 `PROBE_CLASSIFICATION_CODER*.md`、`A_SUBTYPE_*.md`、`ABLATION_SCREENING_*.md`、`a_sec_surgery_list.json`。原判定会造成锚定。
3. 双人独立编码,分歧落表,报 Cohen's κ(按「场景, 探针」对计算)。
4. 每条判定附所引原文及其所在字段(三个可见面之一)。

范围:`benchmark_v11.suite_metadata_for()` 枚举的全部 132 条探针。

---

## 四、事先声明的比较与界限

**主比较**:重判后的 A/B/C 分布,对照原分类的 A 118–120 / B 8–9 / C 3–6。

**事先声明**:若重判后 A 类比例显著下降,则

- 原**预注册轮的证伪结论不受影响**。该结论依赖"`expert` 的优势集中于 A 类"这一分层对比;重判只会把部分 A 移入 C,不会把 C 移入 A,故分层方向不变。
- **跨基准对比须重算**。上游 BaxBench 的两名编码者已自行查明 `spec_type` 默认值并按 `api_spec` 分类,其数字无需重判;本项目一侧此前用了错误前提,故"90% 对 23–29%"的差距中,真实差异与前提错误各占多少,**在本轮完成前不得引用**。
- **A 类细分(探索性)与消融手术清单均须重建**,二者均以错误可见面为基础。

**不得**因重判结果不合预期而回改本协议或恢复旧可见面定义。

---

## 五、已知限制

1. 本轮为**更正**,非新假设检验。它修的是前提错误,不产生新结论。
2. `api_spec` 为 OpenAPI YAML,其 `description` 字段含散文,`summary`、状态码枚举、schema 约束为结构化元素。三档定义未区分二者;编码者遇此须记录所用读法与替代计数,不得自行发明规则。
3. 若某场景的 `api_spec` 与 `_TEXT_SPEC` 在义务表述上高度重合,则该探针的分类不因本次更正而改变。**重合程度本身是本轮的观测量之一,须报告。**
