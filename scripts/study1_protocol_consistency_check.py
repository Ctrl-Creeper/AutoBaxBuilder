"""Mechanical consistency check for the Study 1 prevalence protocol, run once before freezing.

Eight prespecified checks, mapping one-to-one to the freeze instruction. Every check is
mechanical: a required sentence is located verbatim (whitespace-normalised), a banned
phrase is located and then classified by its negation context, never by reading meaning.
Occurrence lists are printed so the classification is auditable.

Lesson applied from the v2 checker's bugs: a banned phrase inside an explicit negation or
prohibition ("never described as the cause") is compliant, so every banned-phrase check
inspects its surrounding sentence for a negator before failing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOC = Path(sys.argv[1] if len(sys.argv) > 1 else
           "docs/preregistration/2026-08-27_study1_prevalence_protocol.md")

text = DOC.read_text()
norm = re.sub(r"\s+", " ", text)
fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {msg}")
    if not ok:
        fails.append(msg)


def has(fragment: str) -> bool:
    return re.sub(r"\s+", " ", fragment) in norm


def sentences_with(pattern: str) -> list[str]:
    """Sentences (crudely split) containing the pattern, for negation-aware banned checks."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", norm)
            if re.search(pattern, s, re.IGNORECASE)]


NEGATORS = re.compile(
    r"\bnever\b|\bnot\b|\bno\b|\bcannot\b|\bnor\b|excluded|prohibit|is not described",
    re.IGNORECASE)

print(f"checking {DOC}\n")

# --- 1. S_t definition matches get_prompt; no residual SeCodePLT signature component
check(has("the verbatim output of `SecodepltPythonInstruct.get_prompt(doc)`"),
      "1a: S_t defined as verbatim get_prompt output")
check(has("no rendered function signature exists in S_t"),
      "1b: explicit statement that no signature is rendered in SeCodePLT S_t")
check("plus the function signature" not in norm,
      "1c: the earlier 'plus the function signature' residue is gone")
# 1d is scoped to §1–§5, the SeCodePLT-only sections: §6's signature mentions describe
# CWEval's S, which genuinely contains a rendered signature, and are correct as written.
sec1to5 = norm.split("## 6.")[0]
sig_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", sec1to5)
             if re.search(r"\bsignature\b", s, re.IGNORECASE)]
bad_sig = [s for s in sig_sents if not NEGATORS.search(s) and "prose fields" not in s]
check(not bad_sig,
      f"1d: within §1–§5, no sentence affirms signature as a model-visible component "
      f"({len(sig_sents)} signature sentences inspected)")
for s in sig_sents:
    print(f"        [signature] {s[:110]}")

# --- 2. setup/preamble inside S_t wherever carriers are described
check(has("the setup/preamble IS part of the default model-visible S"),
      "2a: setup declared inside default S_t")
check(has("the seven labelled fields plus the setup block"),
      "2b: carrier components for quote attribution include the setup block")
check(has("rendered unconditionally"),
      "2c: setup rendering recorded as unconditional")

# --- 3. security_policy analysis: quote-location/bounds only; banned attribution language
check(has("supports claims about *citation*, never about *unique source*"),
      "3a: citation-vs-source discipline stated")
banned = sentences_with(r"unique source|caused by|\bthe cause\b|sole source|source of determination")
bad_attr = [s for s in banned if not NEGATORS.search(s)]
check(not bad_attr,
      f"3b: every attribution phrase occurs only inside a negation/prohibition "
      f"({len(banned)} occurrences inspected)")
for s in banned:
    print(f"        [attribution] {s[:110]}")
check(has("**upper bound = 1**"),
      "3c: upper bound of the survival fraction is 1, not the policy-only rate")
check(has("is **partially identified**"),
      "3d: survival fraction stated as partially identified")

# --- 4. CWEval: unconditional planned replication, not result-contingent
check(has("planned unconditionally, by this protocol, before any SeCodePLT prevalence number exists"),
      "4a: unconditional planning clause present")
check(has("No SeCodePLT result — high, low, or awkward — is a permissible input"),
      "4b: result-independence clause present")
check(has("may start only after SeCodePLT's formal prevalence is complete"),
      "4c: fixed execution order present")
check(has("preregistered cross-benchmark replication using an independently developed benchmark"),
      "4d: fixed paper wording present")
check(has("the *coding* is not described as fully independent"),
      "4e: coding-independence overclaim prohibited")

# --- 5. SecurePrompt excluded from default S_t
check(has("`SecurePrompt` variant") and has("is **excluded** from *S_t*"),
      "5: SecurePrompt recorded as non-default and excluded from S_t")

# --- 6. cwe_943_0 prior exposure and pre-exclusion recorded
c943 = sentences_with(r"cwe_943_0")
check(any("excluded" in s for s in c943) and any("examined" in s.lower() for s in c943),
      f"6: cwe_943_0 exposure declared and family pre-excluded ({len(c943)} mentions)")

# --- 7. Study 1 vs Study 2/3 data-flow isolation mechanisms all present
for frag, label in [
        ("never imports, opens, or transits any writer artifact", "7a: build-path isolation"),
        ("no ID collides", "7b: ID namespace separation"),
        ("never reads Round-2 submissions, the writer output, or Round-2 results",
         "7c: analysis data-flow rule"),
        ("contain zero quantities computed from any S′ judgement", "7d: reporting separation"),
        ("not told these tasks relate to any prior study", "7e: coder blinding"),
        ("preflight", "7f: isolation preflight")]:
    check(has(frag) if frag != "preflight" else ("preflight" in norm.lower()), label)

# --- 8. no TBD / open decisions / result-contingent analysis branches
open_hits = sentences_with(r"\bTBD\b|open design decision|open item|to be decided|to be verified"
                           r"|verification item|remains? deferred|\bdeferred\b")
bad_open = [s for s in open_hits if not NEGATORS.search(s)]
check(not bad_open,
      f"8: no TBD/open-decision/deferred language outside negations "
      f"({len(open_hits)} occurrences inspected)")
for s in open_hits:
    print(f"        [open?] {s[:110]}")

print(f"\n{'CONSISTENCY CHECK PASSED' if not fails else str(len(fails)) + ' FAILURE(S)'}")
sys.exit(1 if fails else 0)
