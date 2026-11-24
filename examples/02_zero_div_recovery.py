# =============================================================================
# 😁 changes done here (100% New File: Zero-Division Recovery Mode Demo)
# =============================================================================
# FILE PURPOSE:
# Demonstrates GuardPVM's configurable Zero-Division handling modes.
# It proves that in 'strict' mode it behaves 100% like standard Python, but
# in 'recover' mode it acts as an airbag by returning 0 without crashing.
# Run with: guard-python examples/02_zero_div_recovery.py
# =============================================================================

"""
=============================================================================
DUAL RUN COMPARISON GUIDE:
=============================================================================

🔴 [1] RUNNING ON REGULAR / STOCK PYTHON (Standard CPython):
    $ python3 examples/02_zero_div_recovery.py
    
    EXPECTED OUTCOME / ERROR:
    -------------------------------------------------------------------------
    AttributeError: module 'sys' has no attribute 'set_div_mode'
    (OR if executing '10 / 0' directly, the process crashes fatally with:
     ZeroDivisionError: division by zero).
    -------------------------------------------------------------------------

🟢 [2] RUNNING ON GUARDPVM UPGRADED RUNTIME (guard-python):
    $ guard-python examples/02_zero_div_recovery.py
    
    EXPECTED OUTCOME (SUCCESS):
    -------------------------------------------------------------------------
    [1] Testing STRICT mode (Default Python Behavior):
        Dividing 10 / 0 -> Caught expected ZeroDivisionError: division by zero
    
    [2] Testing RECOVER mode (GuardPVM Airbag Activated):
        Switched mode to 'recover'
        Running pipeline batch with zero denominators:
          100 / 0   => Result: 0 (No Crash!)
          50 // 0   => Result: 0 (No Crash!)
          25 % 0    => Result: 0 (No Crash!)
    
    [3] Telemetry Audit:
        Zero-Division faults intercepted and safely neutralized: 3
    -------------------------------------------------------------------------
=============================================================================
"""

import sys

def main():
    print("=================================================================")
    print(" GUARDPVM ZERO-DIVISION AIRBAG DEMONSTRATION")
    print("=================================================================")

    if not hasattr(sys, "set_div_mode"):
        print("\n🔴 RUNTIME CHECK FAILED:")
        print("This Python interpreter does not support GuardPVM set_div_mode.")
        print("Please run with:")
        print("  $ guard-python examples/02_zero_div_recovery.py")
        sys.exit(1)

    print(f"🟢 [OK] Engine Version:\n  {sys.version}\n")

    # 1. STRICT MODE TEST
    print("-----------------------------------------------------------------")
    print("PART 1: STRICT MODE (Normal CPython behavior)")
    print("-----------------------------------------------------------------")
    sys.set_div_mode("strict")
    print(f"Active Division Safety Mode: '{sys.get_div_mode()}'")

    try:
        val = 10 / 0
        print(f"Unexpected success: {val}")
    except ZeroDivisionError as e:
        print(f"✅ In STRICT mode, 10 / 0 raised expected error: {type(e).__name__}: {e}")

    # 2. RECOVER MODE TEST
    print("\n-----------------------------------------------------------------")
    print("PART 2: RECOVER MODE (Zero-Division Recovery)")
    print("-----------------------------------------------------------------")
    sys.reset_guard_stats()
    sys.set_div_mode("recover")
    print(f"Active Division Safety Mode: '{sys.get_div_mode()}'")

    print("\nExecuting batch math operations with zero denominators...")
    res_float_div = 100 / 0
    res_int_div   = 50 // 0
    res_modulo    = 25 % 0

    print(f"  100 /  0  => {res_float_div} (Type: {type(res_float_div).__name__})")
    print(f"  50  // 0  => {res_int_div} (Type: {type(res_int_div).__name__})")
    print(f"  25  %  0  => {res_modulo} (Type: {type(res_modulo).__name__})")

    stats = sys.get_guard_stats()
    print(f"\n📊 Telemetry Crash Log:")
    print(f"  Total Zero-Division traps intercepted: {stats['zero_div_count']}")
    print("\n✅ Verification Complete: Pipeline continued without a single unhandled crash!")

if __name__ == "__main__":
    main()
