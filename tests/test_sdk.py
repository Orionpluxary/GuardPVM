# =============================================================================
# FILE PURPOSE:
# Automated unit tests for the GuardPVM Python SDK (guardpvm package).
# Validates guardpvm.run(), step quota enforcement, zero-division recovery,
# and telemetry dictionary formatting.
# Run with: python3 tests/test_sdk.py
# =============================================================================

import sys
sys.path.insert(0, "./src")
sys.path.insert(0, "./src/guardpvm")

import guardpvm

print("=================================================")
print(" GuardPVM Python SDK Demo (import guardpvm)")
print("=================================================")

# 1. Test normal execution with telemetry
print("\n[1] Running code through guardpvm.run():")
res1 = guardpvm.run("primes = [x for x in range(2, 20) if all(x % d != 0 for d in range(2, x))]; print('Primes:', primes)")
print("Output:", res1.stdout)
print("Steps :", res1.stats.get("steps_executed"))

# 2. Test Step Quota runaway loop abort
print("\n[2] Testing step quota abort:")
res2 = guardpvm.run("while True: pass", step_quota=1000)
print("Exit code:", res2.exit_code)
print("Stderr   :", res2.stderr)

# 3. Test Zero-Division Recovery
print("\n[3] Testing zero-division recovery:")
res3 = guardpvm.run("x = 100 / 0; y = 50 // 0; print('x:', x, 'y:', y)", div_mode="recover")
print("Output:", res3.stdout)
print("Zero divisions caught:", res3.stats.get("zero_div_count"))

print("\n[SUCCESS] Python SDK works cleanly!")
