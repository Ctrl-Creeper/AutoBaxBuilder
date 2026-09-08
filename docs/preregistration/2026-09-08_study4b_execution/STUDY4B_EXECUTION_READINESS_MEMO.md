# Study 4B execution-readiness memo

1. **Frozen-pair recovery:** All 47 Study-3 DS pairs are mechanically recoverable. The
   frozen DS IDs map one-to-one through the frozen Q/P/W keys to 47 unique source indices;
   S and S-prime are copied byte-for-byte from the frozen Study-3 packet markers, and the
   hidden tests/oracles are copied from their hash-pinned benchmark/materialization sources.

2. **Context readiness:** All 94 condition prompts fit. S spans 192-541 tokens and S-prime
   spans 205-601 tokens. The maximum requirement is 8,921 tokens under the frozen rule
   `prompt_tokens + 8192 + 128 <= 262144`; over-limit count is zero.

3. **Calls/runtime:** `47 * 2 * 4 = 376` independent generation requests. At concurrency
   two, plan for approximately 1-3 hours on the recorded M4 Max; an all-max-token tail would
   be substantially longer (approximately 9 hours), so this is an engineering estimate.

4. **Generation parameters:** Ornith-1.5-35B-A3B-Abliterated-MLX-4bit, model fingerprint
   `3fe867b89aa52259573e963d121e8974128d5665367b30781d4419b71ef538de`, omlx 0.6.4
   (build 2529), no system prompt, temperature 0.2, top-p 1.0, max tokens 8,192,
   `enable_thinking=false`, fresh stateless requests, and maximum client concurrency two.

5. **Estimator:** For each task,
   `d_t = mean_r(Y_sec[t,S,r]) - mean_r(Y_sec[t,Sprime,r])`; headline
   `Delta_hat_S_DS = sum_t(d_t)/47`. Report the paired t 95% CI and an exact two-sided
   task-level sign-flip randomization test. Apply the same task-equal-weighted estimator to
   CapabilityPass as the guardrail and to the joint endpoint as secondary.

6. **Maximum reviewer limitation:** DS47 is selected on Study-3 transformation success.
   This estimates behavior conditional on demonstrated separability, not a fresh-sample or
   SeCodePLT-wide effect, and cannot identify average effects outside DS47.

7. **Decision:** **GO for Study-4B execution readiness.** No generation schedule or model
   request has been created; execution remains gated on explicit user confirmation.
