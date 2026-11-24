# =============================================================================
# FILE PURPOSE:
# Demonstrates GuardPVM's deterministic Step Quota sandbox protection.
# It sets an instruction limit and executes an infinite loop to prove the VM
# halts cleanly without hanging or crashing the host process.
# Run with: guard-python examples/01_basic_sandbox.py
# =============================================================================

"""
=============================================================================
DUAL RUN COMPARISON GUIDE:
=============================================================================

🔴 [1] RUNNING ON REGULAR / STOCK PYTHON (Standard CPython 3.12 / 3.13 / 3.14):
    $ python3 examples/01_basic_sandbox.py
    
    EXPECTED OUTCOME / ERROR:
    -------------------------------------------------------------------------
    AttributeError: module 'sys' has no attribute 'set_step_quota'
    (OR if run without GuardPVM guardrails, the infinite loop below hangs
     at 100% CPU indefinitely until killed by SIGKILL / Ctrl+C).
    -------------------------------------------------------------------------

🟢 [2] RUNNING ON GUARDPVM UPGRADED RUNTIME (guard-python):
    $ guard-python examples/01_basic_sandbox.py
    
    EXPECTED OUTCOME (SUCCESS):
    -------------------------------------------------------------------------
    [OK] Engine Identity: Python 3.16.0a5+ [GuardPVM v1.0, GCC 15.2.0]
    [OK] Applying step quota: 10,000 steps
    [OK] Executing untrusted infinite loop: 'while True: counter += 1'
    [CAUGHT EXPECTED ERROR] RuntimeError: GuardPVM step quota exceeded
    [TELEMETRY] Total steps executed: 10001
    [SUCCESS] Host server remained responsive. Infinite loop terminated safely!
    -------------------------------------------------------------------------
=============================================================================
"""

import sys
import time

def main():
    print("=================================================================")
    print(" GUARDPVM STEP QUOTA SANDBOX DEMO")
    print("=================================================================")

    # Check runtime capability
    if not hasattr(sys, "set_step_quota"):
        print("\n🔴 RUNTIME CHECK FAILED:")
        print("This Python interpreter does NOT have GuardPVM capabilities.")
        print(f"Current version: {sys.version}")
        print("\nPlease run this script using the GuardPVM runtime:")
        print("  $ guard-python examples/01_basic_sandbox.py")
        sys.exit(1)

    print(f"🟢 [OK] Engine Identity:\n  {sys.version}\n")

    # Reset stats
    sys.reset_guard_stats()
    before_stats = sys.get_guard_stats()
    print(f"Initial Odometer Reading: {before_stats['steps_executed']} steps")

    # Set quota
    QUOTA = 10000
    print(f"\n--> Setting Fuel Limit (Step Quota) to: {QUOTA:,} instructions")
    sys.set_step_quota(QUOTA)

    print("--> Entering untrusted user code (Infinite Loop)...")
    start_time = time.perf_counter()

    loop_counter = 0
    try:
        while True:
            loop_counter += 1
    except RuntimeError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        print(f"\n🟢 [SUCCESSFULLY INTERCEPTED BY GUARDPVM]")
        print(f"  Exception Raised : {type(e).__name__}: {e}")
        print(f"  Loop Iterations  : {loop_counter:,} iterations completed")
        print(f"  Wall Time Taken  : {elapsed:.2f} ms")

    after_stats = sys.get_guard_stats()
    print(f"\n📊 [POST-EXECUTION TELEMETRY]:")
    print(f"  Total Steps Run   : {after_stats['steps_executed']}")
    print(f"  Zero Div Intercept: {after_stats['zero_div_count']}")
    print(f"  Top 3 Opcodes     : {list(after_stats['top_opcodes'].items())[:3]}")
    print("\n✅ Sandboxing verified: Host process survived without hanging!")

if __name__ == "__main__":
    main()
