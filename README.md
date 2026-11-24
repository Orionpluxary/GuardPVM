# GuardPVM (v1.0)
### Sandboxed CPython Runtime with Instruction Step Quotas & Telemetry

[![CPython](https://img.shields.io/badge/CPython-3.16-blue.svg)](https://python.org)
[![Build](https://img.shields.io/badge/Build-Passing-green.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20WSL2-lightgrey.svg)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)]()

GuardPVM is a custom build of CPython 3.16 that I developed to address safety and observability limitations in standard Python. It enforces deterministic instruction quotas, collects execution telemetry, and provides configurable zero-division recovery directly inside the interpreter's bytecode dispatch loop.

---

## The Problem in Standard Python

When running untrusted scripts or executing long-running data jobs, stock CPython has several architectural limitations:

1. **Denial of Service from Runaway Loops:**  
   Code such as `while True: pass` consumes 100% CPU. Traditional wall-clock timeouts (like `signal.SIGALRM` or background watchdog threads) are non-deterministic, vary across CPU speeds, and can be unreliable on Windows or multi-threaded environments.
2. **Fatal Division by Zero:**  
   In stock CPython, a division by zero immediately halts execution with an unhandled `ZeroDivisionError`, crashing long batch processing jobs over a single bad record.
3. **No Bytecode Telemetry:**  
   Standard Python does not track the number of physical instructions executed by the virtual machine, making precise compute accounting impossible.

---

## How I Implemented GuardPVM

I modified CPython across 5 core files:

1. **`Include/internal/pycore_guardpvm.h` & `Python/guardpvm.c`:**  
   Created the central `_PyGuardPVMState` struct to store global telemetry (instruction steps, opcode frequency histogram, zero-division counts, and division modes).
2. **`Python/ceval_macros.h`:**  
   Replaced the empty release-mode macro `PRE_DISPATCH_GOTO()` with `GUARD_PVM_STEP()`. Every single bytecode instruction increments `steps_executed` and checks if the configured `step_quota` has been exceeded. If reached, it raises `RuntimeError("GuardPVM step quota exceeded")` and performs a safe C stack unwind via `goto error;`.
3. **`Python/bytecodes.c`:**  
   Intercepted `_BINARY_OP` arithmetic operations. When a zero-division error occurs:
   - Increments the fault counter `zero_div_count`.
   - In `'recover'` mode, clears the exception via `PyErr_Clear()` and returns `0`.
   - In `'strict'` mode, preserves standard Python crash behavior.
4. **`Python/sysmodule.c`:**  
   Registered 6 new native functions in `sys` (`set_step_quota`, `get_step_quota`, `get_guard_stats`, `reset_guard_stats`, `set_div_mode`, `get_div_mode`) to allow userspace control.
5. **`Python/pylifecycle.c` & `Python/getversion.c`:**  
   Hooked `_Py_GuardPVM_Init()` into early VM boot, and tagged `sys.version` with `[GuardPVM v1.0]`.

---

## Execution Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as User Script
    participant Sys as sys Module (sysmodule.c)
    participant State as _PyGuardPVMState (pycore_guardpvm.h)
    participant Loop as Dispatch Loop (ceval_macros.h)
    participant Op as Opcode Handler (bytecodes.c)

    User->>Sys: sys.set_step_quota(50000)
    Sys->>State: Store step_quota = 50000

    loop Every Bytecode Instruction
        Loop->>State: Increment steps_executed
        Loop->>State: Check if steps_executed >= step_quota
        alt Quota Exceeded
            Loop-->>User: Raise RuntimeError via goto error;
        else Quota OK
            Loop->>Op: Execute instruction
            alt Zero Division in Recover Mode
                Op->>State: Increment zero_div_count
                Op-->>Loop: Clear exception, return 0
            end
        end
    end

    User->>Sys: sys.get_guard_stats()
    Sys-->>User: Return telemetry dictionary
```

---

## Dual Run Comparison

### Scenario A: Unmodified Stock Python (Runaway Loop Hang)
```bash
$ python3 examples/01_basic_sandbox.py
```
**Output:**
```
🔴 RUNTIME CHECK FAILED:
This Python interpreter does NOT have GuardPVM capabilities.
Current version: 3.14.0
AttributeError: module 'sys' has no attribute 'set_step_quota'
```

### Scenario B: Upgraded GuardPVM Engine (Deterministic Protection)
```bash
$ guard-python examples/01_basic_sandbox.py
```
**Output:**
```
=================================================================
 GUARDPVM STEP QUOTA SANDBOX DEMO
=================================================================
🟢 [OK] Engine Identity:
  3.16.0a5+ [GuardPVM v1.0, GCC 15.2.0]

Initial Odometer Reading: 42 steps
--> Setting step quota to: 10,000 instructions
--> Entering untrusted user code (Infinite Loop)...

🟢 [SUCCESSFULLY INTERCEPTED BY GUARDPVM]
  Exception Raised : RuntimeError: GuardPVM step quota exceeded
  Loop Iterations  : 1,666 iterations completed
  Wall Time Taken  : 0.12 ms

📊 [POST-EXECUTION TELEMETRY]:
  Total Steps Run   : 10001
  Zero Div Intercept: 0
  Top 3 Opcodes     : [('BINARY_OP', 3333), ('LOAD_FAST', 3333), ('STORE_FAST', 1667)]

Sandboxing verified: Host process survived without hanging!
```

---

## Project Structure

```
GuardPVM/
├── README.md                      # Project documentation and guide
├── COMPARISON.md                  # Side-by-side upstream CPython vs GuardPVM diffs
├── .gitignore                     # Git ignore rules
│
├── src/                           # Source files
│   ├── main.py                    # Central codebase map & quickstart runner
│   ├── core/                      # Modified CPython 3.16 source files
│   │   ├── Include/internal/
│   │   │   └── pycore_guardpvm.h  # State struct header
│   │   └── Python/
│   │       ├── ceval_macros.h     # Instruction dispatch hook (GUARD_PVM_STEP)
│   │       ├── bytecodes.c        # Arithmetic opcode interceptor
│   │       ├── guardpvm.c         # Engine backend and env var parser
│   │       ├── sysmodule.c        # sys module C bindings
│   │       ├── pylifecycle.c      # Boot hook (_Py_GuardPVM_Init)
│   │       └── getversion.c       # Version banner branding
│   ├── guardpvm/                  # Python SDK package
│   │   ├── __init__.py            # Context managers and runner
│   │   └── setup.py               # setuptools configuration
│   └── node/                      # Node.js SDK package
│       ├── index.js               # GuardPVM Node client class
│       └── package.json           # npm package metadata
│
├── scripts/                       # Automation scripts
│   ├── install.sh                 # Precompiled binary installer
│   └── build.sh                   # Build from source script
│
├── tests/                         # Automated test suites
│   ├── test_guardpvm.py           # Engine verification & benchmark suite
│   └── test_sdk.py                # Python SDK unit tests
│
└── examples/                      # Runnable demonstrations
    ├── 01_basic_sandbox.py        # Step quota demo
    ├── 02_zero_div_recovery.py    # Zero-division strict vs recover demo
    ├── 03_telemetry_benchmark.py  # Performance and telemetry benchmark
    └── 04_node_integration.js     # Running sandboxed code from Node.js
```

---

## Installation

### 1. Build and Install Runtime from Source
```bash
git clone https://github.com/Orionpluxary/GuardPVM.git
cd GuardPVM
bash scripts/build.sh
```

### 2. Python SDK (`pip`)
```bash
pip install -e src/guardpvm
# Or install directly from GitHub:
pip install "git+https://github.com/Orionpluxary/GuardPVM.git#subdirectory=src/guardpvm"
```

### 3. Node.js SDK (`npm`)
```bash
cd src/node
npm install
# Or install directly from GitHub:
npm install "https://github.com/Orionpluxary/GuardPVM.git#main:src/node"
```

---

## API Reference (`import sys`)

| Method | Description |
| :--- | :--- |
| `sys.set_step_quota(limit: int)` | Sets instruction limit. Pass `0` for unlimited. |
| `sys.get_step_quota() -> int` | Returns current instruction budget. |
| `sys.get_guard_stats() -> dict` | Returns telemetry dict (steps, opcodes, fault counts). |
| `sys.reset_guard_stats()` | Resets step and fault counters to zero. |
| `sys.set_div_mode(mode: str)` | Sets division handling mode: `'strict'` or `'recover'`. |
| `sys.get_div_mode() -> str` | Returns current division mode. |

---

## Performance Benchmarks

Benchmarked across 2,500,000 iterations of an arithmetic compute loop:

| Metric | Stock CPython 3.14 | GuardPVM v1.0 | Overhead |
| :--- | :--- | :--- | :--- |
| **Execution Time** | 0.082s | 0.098s | **+19.5%** |
| **Instruction Tracking** | None | 10,000,042 steps | Full Telemetry |
| **Opcode Breakdown** | None | Real-time Top Opcodes | Built-in |
| **Infinite Loop Protection** | Freezes thread | Terminated in 0.1ms | Safe |

---

## License

GuardPVM is released under the **MIT License**. Upstream CPython is subject to the Python Software Foundation (PSF) License.
