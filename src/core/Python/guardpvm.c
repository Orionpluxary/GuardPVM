/* =============================================================================
 * FILE PURPOSE:
 * Core implementation file for GuardPVM runtime engine state and lifecycle logic.
 * Implements startup environment variable parsing (GUARD_PVM_STEP_QUOTA, GUARD_PVM_DIV_MODE),
 * telemetry counters, and C-to-Python dictionary serialization for sys.get_guard_stats().
 * Compiled directly into the CPython binary as part of the core runtime.
 * ============================================================================= */

/* =========================================================================
 * 🛡️ GUARDPVM RUNTIME ENGINE LOGIC (Implementation)
 * =========================================================================
 * 
 * [WHAT CHANGED]:
 * Yeh file original CPython codebase mein nahi thi. Yeh GuardPVM ka 100% naya
 * C source file hai jisko humne Python build system (Makefile/Setup) ke sath link kiya.
 * 
 * [WHY IT IS USED]:
 * 1. Separation of Concerns: Core CPython files (`ceval.c`, `sysmodule.c`) ko clean
 *    rakhne ke liye GuardPVM ki helper logic yahan isolate ki gayi hai.
 * 2. Environment Variable Parsing: Startup par `GUARD_PVM_STEP_QUOTA` aur
 *    `GUARD_PVM_DIV_MODE` ko safely parse karta hai bina kisi dynamic allocation ke.
 * 3. Python Dict Serialization: C struct ke telemetry data ko fast Python dictionary
 *    me convert karta hai jab user `sys.get_guard_stats()` call karta hai.
 * 
 * [REAL-WORLD USE CASE / VIVA ANSWER]:
 * "Sir, Docker containers aur Kubernetes pods mein code change kiye bina agar
 *  hum runtime environment variables se pure container ka execution quota limit
 *  karna chahein, toh yeh module boot-time par un environment variables ko detect
 *  karke engine ko auto-configure kar deta hai."
 * ========================================================================= */

#include "Python.h"
#include "pycore_guardpvm.h"
#include "pycore_opcode_metadata.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

_PyGuardPVMState _Py_GuardPVM_State = {0};

void _Py_GuardPVM_Init(void)
{
    if (_Py_GuardPVM_State.initialized) {
        return;
    }
    _Py_GuardPVM_State.initialized = 1;
    _Py_GuardPVM_State.step_quota = 0;
    _Py_GuardPVM_State.steps_executed = 0;
    _Py_GuardPVM_State.call_count = 0;
    _Py_GuardPVM_State.return_count = 0;
    _Py_GuardPVM_State.zero_div_count = 0;
    _Py_GuardPVM_State.div_mode = 0; /* 0 = strict, 1 = recover */
    memset(_Py_GuardPVM_State.opcode_counts, 0, sizeof(_Py_GuardPVM_State.opcode_counts));

    const char *quota_env = Py_GETENV("GUARD_PVM_STEP_QUOTA");
    if (quota_env != NULL && *quota_env != '\0') {
        char *endptr = NULL;
        long long q = strtoll(quota_env, &endptr, 10);
        if (endptr != quota_env && q > 0) {
            _Py_GuardPVM_State.step_quota = (int64_t)q;
        }
    }

    const char *div_env = Py_GETENV("GUARD_PVM_DIV_MODE");
    if (div_env != NULL) {
        if (strcmp(div_env, "recover") == 0) {
            _Py_GuardPVM_State.div_mode = 1;
        } else if (strcmp(div_env, "strict") == 0) {
            _Py_GuardPVM_State.div_mode = 0;
        }
    }
}

void _Py_GuardPVM_ResetStats(void)
{
    _Py_GuardPVM_State.steps_executed = 0;
    _Py_GuardPVM_State.call_count = 0;
    _Py_GuardPVM_State.return_count = 0;
    _Py_GuardPVM_State.zero_div_count = 0;
    memset(_Py_GuardPVM_State.opcode_counts, 0, sizeof(_Py_GuardPVM_State.opcode_counts));
}

void _Py_GuardPVM_SetStepQuota(int64_t quota)
{
    if (quota < 0) {
        quota = 0;
    }
    _Py_GuardPVM_State.step_quota = quota;
}

int64_t _Py_GuardPVM_GetStepQuota(void)
{
    return _Py_GuardPVM_State.step_quota;
}

int _Py_GuardPVM_SetDivMode(const char *mode)
{
    if (mode == NULL) return -1;
    if (strcmp(mode, "strict") == 0) {
        _Py_GuardPVM_State.div_mode = 0;
        return 0;
    } else if (strcmp(mode, "recover") == 0) {
        _Py_GuardPVM_State.div_mode = 1;
        return 0;
    }
    return -1;
}

const char *_Py_GuardPVM_GetDivMode(void)
{
    return _Py_GuardPVM_State.div_mode == 1 ? "recover" : "strict";
}

PyObject *_Py_GuardPVM_GetStats(void)
{
    PyObject *d = PyDict_New();
    if (d == NULL) {
        return NULL;
    }

    PyObject *v_steps = PyLong_FromUnsignedLongLong(_Py_GuardPVM_State.steps_executed);
    PyObject *v_quota = PyLong_FromLongLong(_Py_GuardPVM_State.step_quota);
    PyObject *v_calls = PyLong_FromUnsignedLongLong(_Py_GuardPVM_State.call_count);
    PyObject *v_rets = PyLong_FromUnsignedLongLong(_Py_GuardPVM_State.return_count);
    PyObject *v_zerodiv = PyLong_FromUnsignedLongLong(_Py_GuardPVM_State.zero_div_count);
    PyObject *v_mode = PyUnicode_FromString(_Py_GuardPVM_GetDivMode());

    if (!v_steps || !v_quota || !v_calls || !v_rets || !v_zerodiv || !v_mode) {
        Py_XDECREF(v_steps); Py_XDECREF(v_quota); Py_XDECREF(v_calls);
        Py_XDECREF(v_rets); Py_XDECREF(v_zerodiv); Py_XDECREF(v_mode);
        Py_DECREF(d);
        return NULL;
    }

    PyDict_SetItemString(d, "steps_executed", v_steps);
    PyDict_SetItemString(d, "step_quota", v_quota);
    PyDict_SetItemString(d, "call_count", v_calls);
    PyDict_SetItemString(d, "return_count", v_rets);
    PyDict_SetItemString(d, "zero_div_count", v_zerodiv);
    PyDict_SetItemString(d, "div_mode", v_mode);

    Py_DECREF(v_steps); Py_DECREF(v_quota); Py_DECREF(v_calls);
    Py_DECREF(v_rets); Py_DECREF(v_zerodiv); Py_DECREF(v_mode);

    PyObject *top_dict = PyDict_New();
    if (top_dict != NULL) {
        int op_indices[512];
        int count = 0;
        for (int i = 0; i < 512; i++) {
            if (_Py_GuardPVM_State.opcode_counts[i] > 0) {
                op_indices[count++] = i;
            }
        }
        int limit = count < 15 ? count : 15;
        for (int i = 0; i < limit; i++) {
            int max_idx = i;
            for (int j = i + 1; j < count; j++) {
                if (_Py_GuardPVM_State.opcode_counts[op_indices[j]] > _Py_GuardPVM_State.opcode_counts[op_indices[max_idx]]) {
                    max_idx = j;
                }
            }
            if (max_idx != i) {
                int tmp = op_indices[i];
                op_indices[i] = op_indices[max_idx];
                op_indices[max_idx] = tmp;
            }
            int op = op_indices[i];
            const char *name = NULL;
            if (op >= 0 && op < 267) {
                name = _PyOpcode_OpName[op];
            }
            char buf[32];
            if (!name || name[0] == '\0') {
                snprintf(buf, sizeof(buf), "OP_%d", op);
                name = buf;
            }
            PyObject *c_val = PyLong_FromUnsignedLongLong(_Py_GuardPVM_State.opcode_counts[op]);
            if (c_val != NULL) {
                PyDict_SetItemString(top_dict, name, c_val);
                Py_DECREF(c_val);
            }
        }
        PyDict_SetItemString(d, "top_opcodes", top_dict);
        Py_DECREF(top_dict);
    }

    return d;
}
