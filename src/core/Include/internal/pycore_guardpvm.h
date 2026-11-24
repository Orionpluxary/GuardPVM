/* =============================================================================
 * FILE PURPOSE:
 * Central internal header defining GuardPVM's global runtime telemetry state.
 * Declares the _PyGuardPVMState struct, step quota bounds, and C API functions
 * shared across the interpreter evaluation loop and sys module.
 * Included internally via: #include "pycore_guardpvm.h"
 * ============================================================================= */

#ifndef Py_GUARDPVM_H
#define Py_GUARDPVM_H

/* =========================================================================
 * 🛡️ GUARDPVM MASTER DEFINITION HEADER
 * =========================================================================
 * 
 * [WHAT CHANGED]:
 * Original CPython mein yeh file exist nahi karti thi! Yeh GuardPVM ka 100% 
 * naya internal header file hai.
 * 
 * [WHY IT IS USED]:
 * 1. Single Source of Truth: Pura VM (ceval loop, bytecodes, sysmodule, pylifecycle)
 *    isi struct ke through aapas mein baat karta hai.
 * 2. Shared Memory: Telemetry stats (steps, opcodes, division faults) ko ek
 *    central memory location par rakhne ke liye taaki zero overhead ho.
 * 
 * [REAL-WORLD USE CASE / VIVA ANSWER]:
 * "Sir, multi-tenant cloud environments (jaise AWS Lambda ya OpenAI Code Interpreter)
 *  mein har user ka Python code kitne low-level instructions consume kar raha hai,
 *  wo track karne ke liye hume kernel-level ya VM-level state struct chahiye hoti hai.
 *  Yeh struct wahi central control unit (ECU) hai."
 * ========================================================================= */

#ifndef Py_PYTHON_H
#include "Python.h"
#endif
#include <stdint.h>

/* =========================================================================
 * GUARDPVM MASTER RUNTIME STATE STRUCT
 * Yeh struct engine ka central memory block hai jahan sab record hota hai.
 * ========================================================================= */
typedef struct {
    uint64_t steps_executed;       /* [KEYWORD: Odometer] Total instructions run (Hardware steps) */
    int64_t  step_quota;           /* [KEYWORD: Fuel Limit] Max steps allowed before abort (0 = unlimited) */
    uint64_t call_count;           /* [KEYWORD: Entry Sensor] Kitni baar koi function enter hua */
    uint64_t return_count;         /* [KEYWORD: Exit Sensor] Kitni baar koi function return/finish hua */
    uint64_t zero_div_count;       /* [KEYWORD: Crash Log] Kitni baar divide-by-zero intercept hua */
    int      div_mode;             /* [KEYWORD: Airbag Switch] 0 = strict (crash), 1 = recover (return 0) */
    uint64_t opcode_counts[512];   /* [KEYWORD: Opcode Diary] Har instruction ka frequency tally table */
    int      initialized;          /* [KEYWORD: Ready Flag] Bootup single-init protection flag */
} _PyGuardPVMState;

extern _PyGuardPVMState _Py_GuardPVM_State;

void _Py_GuardPVM_Init(void);
void _Py_GuardPVM_ResetStats(void);
PyObject *_Py_GuardPVM_GetStats(void);
void _Py_GuardPVM_SetStepQuota(int64_t quota);
int64_t _Py_GuardPVM_GetStepQuota(void);
int _Py_GuardPVM_SetDivMode(const char *mode);
const char *_Py_GuardPVM_GetDivMode(void);

#endif /* Py_GUARDPVM_H */
