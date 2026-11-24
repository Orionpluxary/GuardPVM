/* =============================================================================
 * 😁 changes done here (100% New File created for GuardPVM)
 * Defines _PyGuardPVMState struct and runtime telemetry variables
 * =============================================================================
 * FILE PURPOSE:
 * Central internal header for GuardPVM runtime state.
 * Defines the shared _PyGuardPVMState struct used by the interpreter loop,
 * sys module, and lifecycle hooks to track steps, quotas, and division modes.
 * ============================================================================= */
#ifndef Py_GUARDPVM_H
#define Py_GUARDPVM_H

#ifndef Py_PYTHON_H
#include "Python.h"
#endif
#include <stdint.h>

/*
 * My implementation: Central state struct.
 * Stock CPython has no global counters for bytecode execution.
 * I created this struct to keep all runtime telemetry in one shared location:
 * - steps_executed: total instructions run by the interpreter
 * - step_quota: max allowed steps before raising RuntimeError (0 = unlimited)
 * - call_count: function entry counter
 * - return_count: function exit counter
 * - zero_div_count: number of zero-division occurrences intercepted
 * - div_mode: 0 for standard Python crash (strict), 1 for recover (return 0)
 * - opcode_counts: histogram array tracking the frequency of each opcode (0-511)
 * - initialized: flag ensuring boot logic only runs once
 */
typedef struct {
    uint64_t steps_executed;
    int64_t  step_quota;
    uint64_t call_count;
    uint64_t return_count;
    uint64_t zero_div_count;
    int      div_mode;             /* 0 = strict, 1 = recover */
    uint64_t opcode_counts[512];
    int      initialized;
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
