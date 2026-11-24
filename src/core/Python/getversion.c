/* =============================================================================
 * FILE PURPOSE:
 * Overrides CPython's version and build-information banner strings.
 * Injects the '[GuardPVM v1.0]' flavor identifier tag into sys.version and CLI output
 * while preserving compiler bracket syntax for regex compatibility.
 * Compiled directly into the CPython binary as Python/getversion.c.
 * ============================================================================= */

/* Return the full version string. */

#include "Python.h"

#include "patchlevel.h"

static int initialized = 0;
static char version[300];

void _Py_InitVersion(void)
{
    if (initialized) {
        return;
    }
    initialized = 1;
    /* =========================================================================
     * 🛡️ GUARDPVM FLAVOR IDENTITY TAG
     * =========================================================================
     * [WHAT CHANGED]:
     * Original CPython banner format: `%.80s (%.80s) [%.80s]`
     * GuardPVM format: `%.80s (%.80s) [GuardPVM v1.0, %.80s]`
     * 
     * [WHY IT IS USED & USE CASE]:
     * Runtime identity verification. Jab professor ya security team check kare
     * `python -V` ya `sys.version`, unhe immediately verify ho jata hai ki ye
     * unmodified vanilla Python nahi balki secure GuardPVM runtime engine hai.
     * Compiler brackets ke andar rakhna zaroori hota hai taaki `platform.py`
     * ka regex parser break na ho.
     * ========================================================================= */
#ifdef Py_GIL_DISABLED
    const char *buildinfo_format = "%.80s free-threading build (%.80s) [GuardPVM v1.0, %.80s]";
#else
    const char *buildinfo_format = "%.80s (%.80s) [GuardPVM v1.0, %.80s]";
#endif
    PyOS_snprintf(version, sizeof(version), buildinfo_format,
                  PY_VERSION, Py_GetBuildInfo(), Py_GetCompiler());
}

const char *
Py_GetVersion(void)
{
    _Py_InitVersion();
    return version;
}

// Export the Python hex version as a constant.
const unsigned long Py_Version = PY_VERSION_HEX;
