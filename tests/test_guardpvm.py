#!/usr/bin/env guard-python
# =============================================================================
# 😀 changes done here (100% New File: GuardPVM Test & Verification Benchmark)
# =============================================================================
# FILE PURPOSE:
# Core test suite and verification benchmark for GuardPVM custom runtime.
# Tests step quota aborts, telemetry odometer accuracy, zero-division airbag modes,
# and compares benchmark timings against unmodified CPython.
# Run with: guard-python tests/test_guardpvm.py
# =============================================================================

"""
GuardPVM v1.0 - Verification & Overhead Benchmark Suite
Tests step quota enforcement, execution telemetry, zero-division fault modes,
and measures performance overhead against stock CPython.
"""

import sys
import os
import time
import subprocess
import json

def separator(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def test_version_and_telemetry():
    separator("1. VERSION & VM EXECUTION TELEMETRY")
    print(f"Python sys.version:\n  {sys.version}")
    assert "GuardPVM" in sys.version, "Error: sys.version does not contain '[GuardPVM]'"
    print("\n[OK] GuardPVM flavor identity confirmed in sys.version.")

    sys.reset_guard_stats()
    initial_stats = sys.get_guard_stats()
    print(f"Stats after reset: {initial_stats}")
    assert initial_stats["steps_executed"] < 100, "Reset should clear steps_executed"
    assert initial_stats["zero_div_count"] == 0, "Reset should clear zero_div_count"

    # Run a normal workload: prime sieve & function calls
    def is_prime(n):
        if n < 2: return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0: return False
        return True

    primes = [n for n in range(2, 500) if is_prime(n)]
    print(f"Computed {len(primes)} primes in range [2, 500]")

    stats = sys.get_guard_stats()
    print(f"\nExecution Telemetry after normal workload:")
    print(f"  - steps_executed : {stats['steps_executed']}")
    print(f"  - call_count     : {stats['call_count']}")
    print(f"  - return_count   : {stats['return_count']}")
    print(f"  - zero_div_count : {stats['zero_div_count']}")
    print(f"  - div_mode       : {stats['div_mode']}")
    print(f"  - top_opcodes    : {dict(list(stats['top_opcodes'].items())[:8])}")

    assert stats["steps_executed"] > 1000, "steps_executed should be > 1000"
    assert stats["call_count"] > 100, "call_count should be tracked"
    assert stats["return_count"] > 100, "return_count should be tracked"
    print("\n[OK] Telemetry (steps, calls, returns, opcodes) successfully tracked.")

def test_step_quota():
    separator("2. STEP QUOTA ENFORCEMENT & CLEAN ABORT")
    # Test programmatic API: sys.set_step_quota
    sys.reset_guard_stats()
    sys.set_step_quota(3000)
    current_quota = sys.get_step_quota()
    print(f"Configured step quota: {current_quota}")
    assert current_quota == 3000

    caught_quota_error = False
    iterations_run = 0
    try:
        while True:
            iterations_run += 1
    except RuntimeError as exc:
        caught_quota_error = True
        print(f"Successfully caught expected RuntimeError: '{exc}'")
        assert "GuardPVM step quota exceeded" in str(exc)

    assert caught_quota_error, "Failed to abort runaway loop on step quota!"
    stats = sys.get_guard_stats()
    print(f"VM steps at abort: {stats['steps_executed']} (quota was {current_quota})")
    print(f"Quota after abort: {stats['step_quota']} (automatically disarmed for clean cleanup)")
    print(f"Iterations completed before quota limit: {iterations_run}")

    # Verify interpreter state remains completely sane and healthy
    test_val = sum([x * 2 for x in range(100)])
    assert test_val == 9900
    print("[OK] Interpreter state and memory remain fully coherent after quota abort.")

    # Test environment variable GUARD_PVM_STEP_QUOTA via subprocess
    print("\nTesting GUARD_PVM_STEP_QUOTA environment variable via subshell...")
    env = os.environ.copy()
    # Python startup requires ~55k steps; setting 80k allows startup then aborts runaway loop in user code
    env["GUARD_PVM_STEP_QUOTA"] = "80000"
    code = "try:\n while True: pass\nexcept RuntimeError as e:\n print('SUBPROC CAUGHT:', e)"
    proc = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True
    )
    combined = (proc.stdout + proc.stderr).strip()
    print(f"Subprocess output:\n  {combined}")
    assert "GuardPVM step quota exceeded" in combined, f"Env var GUARD_PVM_STEP_QUOTA failed: {combined}"
    print("[OK] Environment variable GUARD_PVM_STEP_QUOTA works cleanly.")

def test_zero_division_modes():
    separator("3. ZERO-DIVISION FAULT HANDLING ('strict' vs 'recover')")
    
    # Mode 1: Strict mode
    sys.set_div_mode("strict")
    assert sys.get_div_mode() == "strict"
    sys.reset_guard_stats()

    strict_caught = False
    try:
        _ = 42 / 0
    except ZeroDivisionError as e:
        strict_caught = True
        print(f"Strict mode: Caught expected ZeroDivisionError: '{e}'")
    assert strict_caught

    strict_caught_floor = False
    try:
        _ = 100 // 0
    except ZeroDivisionError as e:
        strict_caught_floor = True
        print(f"Strict mode: Caught expected floor ZeroDivisionError: '{e}'")
    assert strict_caught_floor

    stats = sys.get_guard_stats()
    print(f"Strict mode zero_div_count: {stats['zero_div_count']}")
    assert stats["zero_div_count"] == 2

    # Mode 2: Recover mode
    sys.set_div_mode("recover")
    assert sys.get_div_mode() == "recover"
    print("\nSwitched div_mode to 'recover'.")

    # In recover mode, division and floor division by zero return 0 without exception
    res_div = 42 / 0
    res_floordiv = 100 // 0
    res_mod = 50 % 0
    print(f"Recover mode 42 / 0   returned: {res_div} (type: {type(res_div).__name__})")
    print(f"Recover mode 100 // 0 returned: {res_floordiv} (type: {type(res_floordiv).__name__})")
    print(f"Recover mode 50 % 0   returned: {res_mod} (type: {type(res_mod).__name__})")

    assert res_div == 0
    assert res_floordiv == 0
    assert res_mod == 0

    stats = sys.get_guard_stats()
    print(f"Recover mode zero_div_count: {stats['zero_div_count']}")
    assert stats["zero_div_count"] == 5

    # Switch back to strict
    sys.set_div_mode("strict")
    assert sys.get_div_mode() == "strict"
    print("\n[OK] Zero-division fault modes ('strict' and 'recover') verified.")

def run_overhead_benchmark():
    separator("4. OVERHEAD BENCHMARK: GuardPVM vs. Stock CPython")
    stock_python = "/usr/bin/python3"
    guard_python = sys.executable

    print(f"GuardPVM Binary : {guard_python}")
    print(f"Stock CPython   : {stock_python}")

    if not os.path.exists(stock_python):
        print(f"Notice: {stock_python} not found, checking alternatives...")
        stock_python = subprocess.check_output(["which", "python3"]).decode().strip()

    stock_version = subprocess.check_output([stock_python, "--version"]).decode().strip()
    guard_version = subprocess.check_output([guard_python, "--version"]).decode().strip()
    print(f"Stock Version   : {stock_version}")
    print(f"Guard Version   : {guard_version}")

    benchmark_script = """
import time

def compute_heavy():
    total = 0
    for i in range(2_500_000):
        total = (total + i) ^ (i & 0xFF)
        if i % 500_000 == 0:
            total += (i >> 2)
    return total

times = []
for _ in range(5):
    t0 = time.perf_counter()
    compute_heavy()
    t1 = time.perf_counter()
    times.append((t1 - t0) * 1000.0)

times.sort()
best = times[0]
avg = sum(times) / len(times)
print(f"{best:.2f},{avg:.2f}")
"""

    print("\nRunning benchmark workload (5 rounds of 2,500,000 arithmetic & loop iterations)...")

    # Run Stock CPython
    p_stock = subprocess.run([stock_python, "-c", benchmark_script], capture_output=True, text=True, check=True)
    stock_best, stock_avg = map(float, p_stock.stdout.strip().split(","))

    # Run GuardPVM
    p_guard = subprocess.run([guard_python, "-c", benchmark_script], capture_output=True, text=True, check=True)
    guard_best, guard_avg = map(float, p_guard.stdout.strip().split(","))

    overhead_best = ((guard_best - stock_best) / stock_best) * 100.0
    overhead_avg = ((guard_avg - stock_avg) / stock_avg) * 100.0

    print("\n" + "-" * 70)
    print(f"{'Runtime':<20} | {'Best (ms)':<15} | {'Average (ms)':<15}")
    print("-" * 70)
    print(f"{'Stock CPython':<20} | {stock_best:<15.2f} | {stock_avg:<15.2f}")
    print(f"{'GuardPVM v1.0':<20} | {guard_best:<15.2f} | {guard_avg:<15.2f}")
    print("-" * 70)
    print(f"Measured Overhead (Best) : {overhead_best:+.2f}%")
    print(f"Measured Overhead (Avg)  : {overhead_avg:+.2f}%")
    print("-" * 70)
    print("[OK] Benchmark completed successfully.")

if __name__ == "__main__":
    print("=" * 70)
    print(" GUARDPVM (v1.0) COMPLETE END-TO-END VERIFICATION SUITE")
    print("=" * 70)
    
    test_version_and_telemetry()
    test_step_quota()
    test_zero_division_modes()
    run_overhead_benchmark()

    separator("ALL VERIFICATION CHECKS & BENCHMARKS PASSED SUCCESSFULLY")
    sys.exit(0)
