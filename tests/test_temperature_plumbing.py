"""Check --temperature reaches the BaxBench arg list, and the collapse guard."""
import subprocess, sys, ast, pathlib
src = pathlib.Path("scripts/run_smoke_eval.py").read_text()
tree = ast.parse(src)
# the common list must interpolate args.temperature, not the literal "0"
assert 'str(args.temperature)' in src, "temperature not forwarded to BaxBench"
assert '"--temperature",\n        "0",' not in src, "temperature still hardcoded"

# guard: n-samples>1 must still abort at temp 0, and be allowed above 0
def guard(ns, temp):
    r = subprocess.run(
        [sys.executable, "scripts/run_factorial_smoke_eval.py",
         "--n-samples", str(ns), "--temperature", str(temp),
         "--manifest", "/nonexistent.json"],
        capture_output=True, text=True, env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin", "OPENAI_TIMEOUT": "1200"},
    )
    return (r.stdout + r.stderr)

out0 = guard(3, 0)
assert "produces a single sample at" in out0, f"guard missing at temp 0:\n{out0[:400]}"
out7 = guard(3, 0.7)
assert "produces a single sample at" not in out7, f"guard wrongly fired at temp 0.7:\n{out7[:400]}"
print("PASS: temperature forwarded; collapse guard fires only at temp 0")
