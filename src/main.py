# =============================================================================
# 😁 changes done here (100% New File: GuardPVM Project Map & Verification Runner)
# =============================================================================
# FILE PURPOSE:
# Serves as the primary entry point and central codebase map for GuardPVM.
# Contains an architectural map of all project files and executes a complete
# quick-start validation of sandboxing, telemetry, and zero-division recovery.
# Run with: guard-python src/main.py
# =============================================================================

"""
===============================================================================
                         GUARDPVM PROJECT ARCHITECTURE MAP
===============================================================================

GuardPVM/
├── README.md                      # Comprehensive user & developer documentation
├── COMPARISON.md                  # Side-by-side upstream CPython vs GuardPVM diffs
├── .gitignore                     # Git ignore rules for caches, builds, and artifacts
│
├── src/                           # Core source files and SDK libraries
│   ├── main.py                    # [YOU ARE HERE] Codebase map & quick-start runner
│   │
│   ├── core/                      # Modified CPython 3.16 C Engine Source
│   │   ├── Include/internal/
│   │   │   └── pycore_guardpvm.h  # Shared telemetry state struct (_PyGuardPVMState)
│   │   └── Python/
│   │       ├── ceval_macros.h     # Instruction dispatch hook (GUARD_PVM_STEP)
│   │       ├── bytecodes.c        # Arithmetic zero-division airbag interceptor
│   │       ├── guardpvm.c         # Engine state logic & environment variable parser
│   │       ├── sysmodule.c        # Python 'sys' module API bindings
│   │       ├── pylifecycle.c      # Boot initialization hook (_Py_GuardPVM_Init)
│   │       └── getversion.c       # Custom flavor branding banner ([GuardPVM v1.0])
│   │
│   ├── guardpvm/                  # Python SDK Package (pip install)
│   │   ├── __init__.py            # High-level context managers & sandbox runners
│   │   └── setup.py               # Python setuptools packaging configuration
│   │
│   └── node/                      # Node.js SDK Package (npm install)
│       ├── index.js               # GuardPVM JavaScript class wrapper (child_process)
│       └── package.json           # npm package metadata and configuration
│
├── scripts/                       # Build, patch, and installation automation
│   ├── install.sh                 # Fast binary installer into /opt/guard-pvm
│   └── build.sh                   # From-source compiler and build script
│
├── tests/                         # Automated test suites
│   ├── test_guardpvm.py           # Engine verification & benchmark test suite
│   └── test_sdk.py                # Python SDK unit test suite
│
└── examples/                      # Runnable demonstrations with dual run guides
    ├── 01_basic_sandbox.py        # Step Quota protection against infinite loops
    ├── 02_zero_div_recovery.py    # Zero-division strict vs recover airbag demo
    ├── 03_telemetry_benchmark.py  # VM instruction telemetry & speed benchmark
    └── 04_node_integration.js     # Running sandboxed Python from Node.js
===============================================================================
"""

import sys
import time

def run_quickstart():
    print("=" * 70)
    print("         GUARDPVM v1.0 QUICK-START VERIFICATION")
    print("=" * 70)

    # 1. Check runtime capability
    is_guard = hasattr(sys, "set_step_quota") and hasattr(sys, "get_guard_stats")
    if not is_guard:
        print("\n[WARNING] Running on standard CPython runtime.")
        print(f"Current Interpreter: {sys.version}")
        print("\nTo experience GuardPVM's engine features, execute with:")
        print("  $ guard-python src/main.py")
        return

    print(f"[OK] Running inside GuardPVM custom runtime:")
    print(f"   {sys.version}\n")

    # 2. Reset telemetry
    sys.reset_guard_stats()
    sys.set_div_mode("recover")

    # 3. Quota demonstration
    QUOTA = 25000
    print(f"[DEMO 1] Testing Deterministic Step Quota ({QUOTA:,} steps budget):")
    sys.set_step_quota(QUOTA)
    
    counter = 0
    start = time.perf_counter()
    try:
        while True:
            counter += 1
    except RuntimeError as exc:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  ✓ Caught expected exception: {exc}")
        print(f"  ✓ Loop halted safely after : {counter:,} iterations ({elapsed:.2f} ms)")

    # 4. Zero division recovery demonstration
    print(f"\n[DEMO 2] Testing Zero-Division Airbag (Mode: '{sys.get_div_mode()}'):")
    val = 42 / 0
    print(f"  ✓ 42 / 0 evaluated safely to : {val} (No crash!)")

    # 5. Telemetry display
    stats = sys.get_guard_stats()
    print(f"\n[DEMO 3] Live Execution Telemetry:")
    print(f"  - Hardware Steps Executed : {stats['steps_executed']:,}")
    print(f"  - Zero-Divisions Caught   : {stats['zero_div_count']}")
    print(f"  - Top Executed Instructions:")
    for op, cnt in list(stats["top_opcodes"].items())[:4]:
        print(f"      * {op:<20}: {cnt:,} times")

    print("\n" + "=" * 70)
    print(" ✅ GuardPVM v1.0 is healthy, operational, and fully verified!")
    print("=" * 70)

if __name__ == "__main__":
    run_quickstart()
